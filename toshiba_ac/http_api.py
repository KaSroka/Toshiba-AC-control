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

import aiohttp
from dataclasses import dataclass

import datetime

import logging
logger = logging.getLogger(__name__)

from toshiba_ac.device import ToshibaAcDeviceEnergyConsumption

import typing

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
    cdu: typing.Optional[str]
    fcu: typing.Optional[str]

class ToshibaAcHttpApiError(Exception):
    pass

class ToshibaAcHttpApiAuthError(ToshibaAcHttpApiError):
    pass

class ToshibaAcHttpApi:
    BASE_URL = 'https://toshibamobileservice.azurewebsites.net'
    LOGIN_PATH = '/api/Consumer/Login'
    REGISTER_PATH = '/api/Consumer/RegisterMobileDevice'
    AC_MAPPING_PATH = '/api/AC/GetConsumerACMapping'
    AC_STATE_PATH = '/api/AC/GetCurrentACState'
    AC_ENERGY_CONSUMPTION_PATH = '/api/AC/GetGroupACEnergyConsumption'

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.access_token = None
        self.access_token_type = None
        self.consumer_id = None
        self.session = None

    async def request_api(self, path, get=None, post=None, headers=None):
        if not self.session:
            self.session = aiohttp.ClientSession()

        if not headers:
            headers = {}
            headers['Content-Type'] = 'application/json'
            headers['Authorization'] = self.access_token_type + ' ' + self.access_token

        url = self.BASE_URL + path

        if post:
            method = lambda : self.session.post(url, params=get, json=post, headers=headers)
            logger.debug(f'Sending POST to {url} with params={get}, json={post}, headers={headers}')

        else:
            method = lambda : self.session.get(url, params=get, headers=headers)
            logger.debug(f'Sending GET to {url} with params={get}, headers={headers}')

        async with method() as response:
            json = await response.json()
            logger.debug(f'Response code: {response.status}, JSON: {json}')

            err_type = ToshibaAcHttpApiError

            if response.status == 200:
                if json['IsSuccess']:
                    return json['ResObj']
                else:
                    if json['StatusCode'] == 'InvalidUserNameorPassword':
                        err_type = ToshibaAcHttpApiAuthError

            raise err_type(json['Message'])

    async def connect(self):
        headers = {'Content-Type': 'application/json'}
        post = {'Username': self.username, 'Password': self.password}

        res = await self.request_api(self.LOGIN_PATH, post=post, headers=headers)

        self.access_token = res['access_token']
        self.access_token_type = res['token_type']
        self.consumer_id = res['consumerId']

    async def shutdown(self):
        if self.session:
            await self.session.close()
            self.session = None

    async def get_devices(self):
        get = {
            'consumerId': self.consumer_id
        }

        res = await self.request_api(self.AC_MAPPING_PATH, get=get)

        devices = []

        for group in res:
            for device in group['ACList']:
                devices.append(
                    ToshibaAcDeviceInfo(
                        device['Id'],
                        device['DeviceUniqueId'],
                        device['Name'],
                        device['ACStateData'],
                        device['FirmwareVersion'],
                        device['MeritFeature'],
                        device['ACModelId']
                    )
                )

        return devices

    async def get_device_state(self, ac_id):
        get = {
            "ACId": ac_id,
        }

        res = await self.request_api(self.AC_STATE_PATH, get=get)

        return res['ACStateData']

    async def get_device_additional_info(self, ac_id):
        get = {
            "ACId": ac_id,
        }

        res = await self.request_api(self.AC_STATE_PATH, get=get)

        try:
            cdu = res['Cdu']['model_name']
        except (KeyError, TypeError):
            cdu = None

        try:
            fcu = res['Fcu']['model_name']
        except (KeyError, TypeError):
            fcu = None

        return ToshibaAcDeviceAdditionalInfo(
            cdu=cdu,
            fcu=fcu
        )

    async def get_devices_energy_consumption(self, ac_unique_ids):
        year = int(datetime.datetime.now().year)
        since = datetime.datetime(year, 1, 1).astimezone(datetime.timezone.utc)

        post = {
            'ACDeviceUniqueIdList': ac_unique_ids,
            'FromUtcTime': str(year),
            'Timezone': 'UTC',
            'ToUtcTime': str(year + 1),
            'Type': 'EnergyYear'
        }

        res = await self.request_api(self.AC_ENERGY_CONSUMPTION_PATH, post=post)

        ret = {}

        try:
            for ac in res:
                try:
                    consumption = sum(int(consumption['Energy']) for consumption in ac['EnergyConsumption'])
                    ret[ac['ACDeviceUniqueId']] = ToshibaAcDeviceEnergyConsumption(consumption, since)
                except (KeyError, ValueError):
                    pass
        except TypeError:
            pass

        return ret

    async def register_client(self, device_id):
        post = {
            'DeviceID': device_id,
            'DeviceType': '1',
            'Username': self.username
        }

        res = await self.request_api(self.REGISTER_PATH, post=post)

        return res['SasToken']
