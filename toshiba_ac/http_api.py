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

import httpx
from dataclasses import dataclass

@dataclass
class ToshibaAcClientInfo:
    device_id: str
    sas_token: str

@dataclass
class ToshibaAcDeviceInfo:
    ac_id: str
    ac_unique_id: str
    ac_name: str

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

    async def request_api(self, path, get=None, post=None, headers=None):
        if not headers:
            headers = {}
            headers['Content-Type'] = 'application/json'
            headers['Authorization'] = self.access_token_type + ' ' + self.access_token

        url = self.BASE_URL + path

        async with httpx.AsyncClient() as client:
            if post:
                res = await client.post(url, params=get, json=post, headers=headers)
            else:
                res = await client.get(url, params=get, headers=headers)

        return res.json()['ResObj']

    async def connect(self):
        headers = {'Content-Type': 'application/json'}
        post = {'Username': self.username, 'Password': self.password}

        res = await self.request_api(self.LOGIN_PATH, post=post, headers=headers)

        self.access_token = res['access_token']
        self.access_token_type = res['token_type']
        self.consumer_id = res['consumerId']

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


    async def register_client(self):
        post = {
            'DeviceID': self.username + '_3e6e4eb5f0e5aa46',
            'DeviceType': '1',
            'Username': self.username
        }

        res = await self.request_api(self.REGISTER_PATH, post=post)

        return ToshibaAcClientInfo(res['DeviceId'], res['SasToken'])
