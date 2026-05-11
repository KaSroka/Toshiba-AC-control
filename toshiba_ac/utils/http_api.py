# Copyright 2021 Kamil Sroka

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import asyncio
import logging
import random
import typing as t
from dataclasses import dataclass

import aiohttp
from toshiba_ac.device.properties import ToshibaAcDeviceEnergyConsumption
from toshiba_ac.utils import RetryJitterMode, retry_on_exception

logger = logging.getLogger(__name__)


@dataclass
class ToshibaAcDeviceInfo:
    ac_id: str
    ac_unique_id: str
    ac_name: str
    initial_ac_state: str
    firmware_version: str
    merit_feature: str
    ac_model_id: str


@dataclass
class ToshibaAcDeviceAdditionalInfo:
    cdu: t.Optional[str]
    fcu: t.Optional[str]


class ToshibaAcHttpApiError(Exception):
    pass


class ToshibaAcHttpApiAuthError(ToshibaAcHttpApiError):
    pass


class ToshibaAcHttpApiRateLimitError(ToshibaAcHttpApiError):
    pass


class ToshibaAcHttpApi:
    REQUEST_MIN_INTERVAL_S = 0.15
    REQUEST_JITTER_S = 0.25
    BASE_URL = "https://mobileapi.toshibahomeaccontrols.com"
    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    )
    LOGIN_PATH = "/api/Consumer/Login"
    REGISTER_PATH = "/api/Consumer/RegisterMobileDevice"
    AC_MAPPING_PATH = "/api/AC/GetConsumerACMapping"
    AC_STATE_PATH = "/api/AC/GetCurrentACState"
    AC_ENERGY_CONSUMPTION_PATH = "/api/AC/GetGroupACEnergyConsumption"

    def __init__(self, username: str, password: str) -> None:
        self.username = username
        self.password = password
        self.access_token: t.Optional[str] = None
        self.access_token_type: t.Optional[str] = None
        self.consumer_id: t.Optional[str] = None
        self.session: t.Optional[aiohttp.ClientSession] = None
        self._session_lock = asyncio.Lock()
        self._auth_lock = asyncio.Lock()
        self._auth_generation = 0
        self._request_pacing_lock = asyncio.Lock()
        self._next_request_not_before = 0.0

    async def _pace_requests(self) -> None:
        async with self._request_pacing_lock:
            loop = asyncio.get_running_loop()
            now = loop.time()

            wait_for = max(0.0, self._next_request_not_before - now)
            if wait_for > 0:
                await asyncio.sleep(wait_for)

            self._next_request_not_before = (
                loop.time() + self.REQUEST_MIN_INTERVAL_S + random.uniform(0.0, self.REQUEST_JITTER_S)
            )

    async def _ensure_session(self) -> None:
        async with self._session_lock:
            if not self.session or self.session.closed:
                timeout = aiohttp.ClientTimeout(total=20, connect=10, sock_read=15)
                self.session = aiohttp.ClientSession(timeout=timeout)

    async def _refresh_auth_if_stale(self, failed_auth_generation: int) -> None:
        async with self._auth_lock:
            if self._auth_generation != failed_auth_generation:
                return

            await self.connect()

    @retry_on_exception(
        exceptions=ToshibaAcHttpApiRateLimitError,
        retries=5,
        backoff=10,
        max_backoff=600,
        growth_factor=3,
        jitter_mode=RetryJitterMode.EQUAL,
    )
    @retry_on_exception(
        exceptions=(ToshibaAcHttpApiError, aiohttp.ClientError, asyncio.TimeoutError),
        retries=2,
        backoff=5,
        max_backoff=30,
        should_retry=lambda e: not isinstance(
            e,
            (ToshibaAcHttpApiAuthError, ToshibaAcHttpApiRateLimitError),
        ),
    )
    async def request_api(
        self,
        path: str,
        get: dict[str, str] | None = None,
        post: t.Mapping[str, str | t.Sequence[str]] | None = None,
        headers: t.Any = None,
        reauth_on_auth_error: bool = True,
    ) -> t.Any:
        auth_generation = self._auth_generation
        is_authenticated_request = False

        if not isinstance(headers, dict):
            if not self.access_token_type or not self.access_token:
                raise ToshibaAcHttpApiError("Failed to send request, missing access token")

            headers = {
                "Content-Type": "application/json",
                "Authorization": self.access_token_type + " " + self.access_token,
                "User-Agent": self.USER_AGENT,
            }
            is_authenticated_request = True

        url = self.BASE_URL + path

        await self._ensure_session()

        if not self.session:
            raise ToshibaAcHttpApiError("Failed to initialize HTTP session")

        await self._pace_requests()

        method_args = {"params": get, "headers": headers}

        if post:
            logger.debug(f"Sending POST to {url}")
            method_args["json"] = post
            method = self.session.post
        else:
            logger.debug(f"Sending GET to {url}")
            method = self.session.get

        async with method(url, **method_args) as response:
            logger.debug(f"Response code: {response.status}")

            if response.status == 200:
                try:
                    json = await response.json()
                except (aiohttp.ContentTypeError, ValueError) as e:
                    raise ToshibaAcHttpApiError(f"Malformed JSON response for {path}: {e}") from e

                if json["IsSuccess"]:
                    return json["ResObj"]
                else:
                    if json["StatusCode"] == "InvalidUserNameorPassword":
                        raise ToshibaAcHttpApiAuthError(json["Message"])

                    raise ToshibaAcHttpApiError(json["Message"])

            response_text = await response.text()
            logger.warning(
                "Non-200 response from Toshiba API "
                f"(status={response.status}, path={path}, content_type={response.headers.get('Content-Type')}, "
                f"server={response.headers.get('Server')})"
            )
            logger.debug(f"Non-200 response body for {path} (first 500 chars): {response_text[:500]}")

            if is_authenticated_request and response.status == 401:
                if reauth_on_auth_error:
                    logger.warning(
                        f"Auth failed for endpoint {path} with status 401. " f"Refreshing auth and retrying once."
                    )
                    await self._refresh_auth_if_stale(auth_generation)
                    return await self.request_api(
                        path,
                        get=get,
                        post=post,
                        headers=None,
                        reauth_on_auth_error=False,
                    )

                raise ToshibaAcHttpApiAuthError(f"HTTP 401 calling {path}")

            if response.status == 403:
                raise ToshibaAcHttpApiRateLimitError(f"HTTP 403 calling {path}")

            raise ToshibaAcHttpApiError(f"HTTP {response.status} calling {path}")

    async def connect(self) -> None:
        headers = {
            "Content-Type": "application/json",
            "User-Agent": self.USER_AGENT,
        }
        post = {"Username": self.username, "Password": self.password}

        res = await self.request_api(self.LOGIN_PATH, post=post, headers=headers)

        self.access_token = res["access_token"]
        self.access_token_type = res["token_type"]
        self.consumer_id = res["consumerId"]
        self._auth_generation += 1

    async def shutdown(self) -> None:
        async with self._session_lock:
            if self.session:
                await self.session.close()
                self.session = None

    async def get_devices(self) -> t.List[ToshibaAcDeviceInfo]:
        if not self.consumer_id:
            raise ToshibaAcHttpApiError("Failed to send request, missing consumer id")

        get = {"consumerId": self.consumer_id}

        res = await self.request_api(self.AC_MAPPING_PATH, get=get)

        devices = []

        for group in res:
            for device in group["ACList"]:
                devices.append(
                    ToshibaAcDeviceInfo(
                        device["Id"],
                        device["DeviceUniqueId"],
                        device["Name"],
                        device["ACStateData"],
                        device["FirmwareVersion"],
                        device["MeritFeature"],
                        device["ACModelId"],
                    )
                )

        return devices

    async def get_device_state(self, ac_id: str) -> str:
        get = {
            "ACId": ac_id,
        }
        if self.consumer_id:
            get["consumerId"] = self.consumer_id

        res = await self.request_api(self.AC_STATE_PATH, get=get)

        if "ACStateData" not in res:
            raise ToshibaAcHttpApiError("Missing ACStateData in response")

        if not isinstance(res["ACStateData"], str):
            raise ToshibaAcHttpApiError("Malformed ACStateData in response")

        return res["ACStateData"]

    async def get_device_additional_info(self, ac_id: str) -> ToshibaAcDeviceAdditionalInfo:
        get = {
            "ACId": ac_id,
        }
        if self.consumer_id:
            get["consumerId"] = self.consumer_id

        res = await self.request_api(self.AC_STATE_PATH, get=get)

        try:
            cdu = res["Cdu"]["model_name"]
        except (KeyError, TypeError):
            cdu = None

        try:
            fcu = res["Fcu"]["model_name"]
        except (KeyError, TypeError):
            fcu = None

        return ToshibaAcDeviceAdditionalInfo(cdu=cdu, fcu=fcu)

    async def get_devices_energy_consumption(
        self, ac_unique_ids: t.List[str]
    ) -> t.Dict[str, ToshibaAcDeviceEnergyConsumption]:
        year = int(datetime.datetime.now().year)
        since = datetime.datetime(year, 1, 1).astimezone(datetime.timezone.utc)

        post = {
            "ACDeviceUniqueIdList": ac_unique_ids,
            "FromUtcTime": str(year),
            "Timezone": "UTC",
            "ToUtcTime": str(year + 1),
            "Type": "EnergyYear",
        }

        res = await self.request_api(self.AC_ENERGY_CONSUMPTION_PATH, post=post)

        ret = {}

        try:
            for ac in res:
                try:
                    consumption = sum(int(consumption["Energy"]) for consumption in ac["EnergyConsumption"])
                    ret[ac["ACDeviceUniqueId"]] = ToshibaAcDeviceEnergyConsumption(consumption, since)
                except (KeyError, ValueError):
                    pass
        except TypeError:
            pass

        return ret

    async def register_client(self, device_id: str) -> str:
        post = {"DeviceID": device_id, "DeviceType": "1", "Username": self.username}

        res = await self.request_api(self.REGISTER_PATH, post=post)

        if "SasToken" not in res:
            raise ToshibaAcHttpApiError("Missing SasToken in response")

        if not isinstance(res["SasToken"], str):
            raise ToshibaAcHttpApiError("Malformed SasToken in response")

        return res["SasToken"]
