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

from azure.iot.device.aio import IoTHubDeviceClient

import logging

logger = logging.getLogger(__name__)

class ToshibaAcAmqpApi:
    COMMANDS = ['CMD_FCU_FROM_AC', 'CMD_HEARTBEAT']

    def __init__(self, sas_token):
        self.sas_token = sas_token
        self.handlers = {}

        self.device = IoTHubDeviceClient.create_from_sastoken(self.sas_token)
        self.device.on_method_request_received = self.method_request_received

    async def connect(self):
        await self.device.connect()

    async def shutdown(self):
        await self.device.shutdown()

    def register_command_handler(self, command, handler):
        if command not in self.COMMANDS:
            raise AttributeError(f'Unknown command: {command}, should be one of {" ".join(self.COMMANDS)}')
        self.handlers[command] = handler

    def method_request_received(self, method_data):
        if method_data.name != 'smmobile':
            return logger.info(f'Unknown method name: {method_data.name} full data: {method_data.payload}')

        data = method_data.payload
        command = data['cmd']
        handler = self.handlers.get(command, None)

        if handler:
            handler(data['sourceId'], data['messageId'], data['targetId'], data['payload'], data['timeStamp'])
        else:
            logger.info(f'Unhandled command {command} with payload: {data["payload"]}')

    def send_message(self, message):
        return self.device.send_message(message)
