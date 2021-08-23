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

from toshiba_ac.http_api import ToshibaAcHttpApi
from toshiba_ac.amqp_api import ToshibaAcAmqpApi
from toshiba_ac.device import ToshibaAcDevice

import asyncio

class ToshibaAcDeviceManager:
    def __init__(self, user, password):
        self.http_api = ToshibaAcHttpApi(user, password)
        self.reg_info = None
        self.amqp_api = None
        self.devices = {}


    async def connect(self):
        await self.http_api.connect()
        self.reg_info = await self.http_api.register_client()

        self.amqp_api = ToshibaAcAmqpApi(self.reg_info.sas_token)
        self.amqp_api.register_command_handler('CMD_FCU_FROM_AC', self.handle_cmd_fcu_from_ac)
        self.amqp_api.register_command_handler('CMD_HEARTBEAT', self.handle_cmd_heartbeat)
        await self.amqp_api.connect()

    async def get_devices(self, refresh=False):
        # TODO handle refresh
        if not self.devices:
            devices_info = await self.http_api.get_devices()
            for device_info in devices_info:
                device = ToshibaAcDevice(device_info.ac_name,
                    self.reg_info.device_id,
                    device_info.ac_id,
                    device_info.ac_unique_id,
                    self.amqp_api,self.http_api
                )

                await device.connect()
                await self.http_api.get_device_state(device_info.ac_id)

                self.devices[device.ac_unique_id] = device

        return list(self.devices.values())

    def handle_cmd_fcu_from_ac(self, source_id, message_id, target_id, payload, timestamp):
        self.devices[source_id].handle_cmd_fcu_from_ac(payload)

    def handle_cmd_heartbeat(self, source_id, message_id, target_id, payload, timestamp):
        self.devices[source_id].handle_cmd_heartbeat(payload)

    async def shutdown(self):
        await asyncio.gather(*[device.shutdown() for device in self.devices.values()])
        if self.amqp_api:
            await self.amqp_api.shutdown()
