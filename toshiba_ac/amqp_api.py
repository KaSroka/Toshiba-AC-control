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

class ToshibaAcAmqpApi:
    COMMANDS = ['CMD_FCU_FROM_AC', 'CMD_HEARTBEAT']

    def __init__(self, host_name, device_id, shared_key):
        self._host_name = host_name
        self._device_id = device_id
        self._shared_key = shared_key
        self._connection_string = f'HostName={host_name};DeviceId={device_id};SharedAccessKey={shared_key}'
        self.handlers = {}
        self.device = IoTHubDeviceClient.create_from_connection_string(self._connection_string)
        self.device.on_method_request_received = self.method_request_received

    def connect(self):
        return self.device.connect()

    def shutdown(self):
        return self.device.shutdown()

    def register_command_handler(self, command, handler):
        if command not in self.COMMANDS:
            raise AttributeError(f'Unknown command: {command}, should be one of {" ".join(self.COMMANDS)}')
        self.handlers[command] = handler

    def method_request_received(self, method_data):
        if method_data.name != 'smmobile':
            raise AttributeError(f'Unknown method name: {method_data.name} full data: {method_data.payload}')

        data = method_data.payload

        handler = self.handlers.get(data['cmd'], None)

        if handler:
            handler(data['sourceId'], data['messageId'], data['targetId'], data['payload'], data['timeStamp'])
        else:
            pass
            # log unhandled message

    def send_message(self, message):
        return self.device.send_message(message)
