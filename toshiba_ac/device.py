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

class ToshibaAcDevice:
    HOST_NAME = 'toshibasmaciothubprod.azure-devices.net'

    def __init__(self, device_id, shared_key, ac_unique_id):
        self.device_id = device_id
        self.shared_key = shared_key
        self.ac_unique_id = ac_unique_id
        self.amqp_api = ToshibaAcAmqpApi(self.HOST_NAME, self.device_id, self.shared_key)
        self.amqp_api.register_command_handler('CMD_FCU_FROM_AC', self.handle_cmd_fcu_from_ac)
        self.amqp_api.register_command_handler('CMD_HEARTBEAT', self.handle_cmd_heartbeat)
        self.fcu_state = ToshibaAcFcuState()

    def connect(self):
        return self.amqp_api.connect()

    def shutdown(self):
        return self.amqp_api.shutdown()

    def handle_cmd_fcu_from_ac(self, source_id, message_id, target_id, payload, timestamp):
        new_state = ToshibaAcFcuState.from_hexstring(payload['data'])
        print(f'Received state update: {new_state}')
        self.fcu_state.update(payload['data'])
        print(f'Current state: {self.fcu_state}')

    def handle_cmd_heartbeat(self, source_id, message_id, target_id, payload, timestamp):
        hb_data = {k : int(v, base=16) for k, v in payload.items()}
        print(f'Received heartbeat: {hb_data}')

    def create_cmd_fcu_to_ac(self, hexstring):
        return {
            'sourceId': self.device_id,
            'messageId': '0000000',
            'targetId': [self.ac_unique_id],
            'cmd': 'CMD_FCU_TO_AC',
            'payload': {'data': hexstring},
            'timeStamp': '0000000'
            }

    @property
    def ac_status(self):
        return self.state.ac_status

    async def set_ac_status(self, val):
        state = ToshibaAcFcuState()
        state.ac_status = val

        command = self.create_cmd_fcu_to_ac(state.encode())
        msg = Message(str(command))
        msg.custom_properties['type'] = 'mob'
        msg.content_type = "application/json"
        msg.content_encoding = "utf-8"

        await self.amqp_api.send_message(msg)
