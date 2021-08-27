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

import logging
logger = logging.getLogger(__name__)

@dataclass
class ToshibaAcDeviceInfo:
    ac_id: str
    ac_unique_id: str
    ac_name: str

class ToshibaAcHttpApiError(Exception):
    pass

class ToshibaAcHttpApiAuthError(ToshibaAcHttpApiError):
    pass

class ToshibaAcHttpApi:
    BASE_URL = 'https://toshibamobileservice.azurewebsites.net'
    LOGIN_PATH = '/api/Consumer/Login'
    REGISTER_PATH = '/api/Consumer/RegisterMobileDevice'
    AC_MAPPING_PATH = '/api/AC/GetConsumerACMapping'
    STATUS_PATH = '/api/AC/GetCurrentACState'

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
                devices.append(ToshibaAcDeviceInfo(device['Id'], device['DeviceUniqueId'], device['Name']))

        return devices

    async def get_device_state(self, ac_unique_id):
        get = {
            "ACId": ac_unique_id,
        }

        res = await self.request_api(self.STATUS_PATH, get=get)

        return res['ACStateData']


    async def register_client(self, device_id):
        post = {
            'DeviceID': device_id,
            'DeviceType': '1',
            'Username': self.username
        }

        res = await self.request_api(self.REGISTER_PATH, post=post)

        return res['SasToken']
