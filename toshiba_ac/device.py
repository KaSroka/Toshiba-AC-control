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

from toshiba_ac.amqp_api import ToshibaAcAmqpApi
from toshiba_ac.fcu_state import ToshibaAcFcuState

from azure.iot.device import Message
import asyncio

import logging

logger = logging.getLogger(__name__)

class ToshibaAcDevice:
    HOST_NAME = 'toshibasmaciothubprod.azure-devices.net'
    PERIODIC_STATE_RELOAD_PERIOD = 60 * 10

    def __init__(self, name, device_id, ac_id, ac_unique_id, amqp_api, http_api):
        self.name = name
        self.device_id = device_id
        self.ac_id = ac_id
        self.ac_unique_id = ac_unique_id
        self.amqp_api = amqp_api
        self.http_api = http_api
        self.fcu_state = ToshibaAcFcuState()
        self.on_state_changed = None

    async def connect(self):
        await self.state_reload()
        self.periodic_reload_state_task = asyncio.get_event_loop().create_task(self.periodic_state_reload())

    async def shutdown(self):
        self.periodic_reload_state_task.cancel()

    async def state_reload(self):
        hex_state = await self.http_api.get_device_state(self.ac_id)
        self.fcu_state.update(hex_state)
        self.state_changed()

    def state_changed(self):
        logger.debug(f'[{self.name}] Current state: {self.fcu_state}')
        if self.on_state_changed:
            self.on_state_changed(self)

    async def periodic_state_reload(self):
        while True:
            await self.state_reload()
            await asyncio.sleep(self.PERIODIC_STATE_RELOAD_PERIOD)

    def handle_cmd_fcu_from_ac(self, payload):
        self.fcu_state.update(payload['data'])
        self.state_changed()

    def handle_cmd_heartbeat(self, payload):
        hb_data = {k : int(v, base=16) for k, v in payload.items()}
        logger.debug(f'[{self.name}] Received heartbeat: {hb_data}')

    def create_cmd_fcu_to_ac(self, hex_state):
        return {
            'sourceId': self.device_id,
            'messageId': '0000000',
            'targetId': [self.ac_unique_id],
            'cmd': 'CMD_FCU_TO_AC',
            'payload': {'data': hex_state},
            'timeStamp': '0000000'
        }

    async def send_command_to_ac(self, command):
        msg = Message(str(command))
        msg.custom_properties['type'] = 'mob'
        msg.content_type = "application/json"
        msg.content_encoding = "utf-8"

        await self.amqp_api.send_message(msg)

    async def send_state_to_ac(self, state):
        command = self.create_cmd_fcu_to_ac(state.encode())
        await self.send_command_to_ac(command)

    @property
    def ac_status(self):
        return self.fcu_state.ac_status

    async def set_ac_status(self, val):
        state = ToshibaAcFcuState()
        state.ac_status = val

        await self.send_state_to_ac(state)

    @property
    def ac_mode(self):
        return self.fcu_state.ac_mode

    async def set_ac_mode(self, val):
        state = ToshibaAcFcuState()
        state.ac_mode = val

        await self.send_state_to_ac(state)

    @property
    def ac_temperature(self):
        return self.fcu_state.ac_temperature

    async def set_ac_temperature(self, val):
        state = ToshibaAcFcuState()
        state.ac_temperature = val

        await self.send_state_to_ac(state)

    @property
    def ac_fan_mode(self):
        return self.fcu_state.ac_fan_mode

    async def set_ac_fan_mode(self, val):
        state = ToshibaAcFcuState()
        state.ac_fan_mode = val

        await self.send_state_to_ac(state)
