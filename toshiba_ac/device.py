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
from dataclasses import dataclass
import asyncio

import logging

import datetime

logger = logging.getLogger(__name__)

@dataclass
class ToshibaAcDeviceEnergyConsumption:
    energy_wh: float
    since: datetime.datetime

class ToshibaAcDeviceCallback:
    def __init__(self):
        self.callbacks = []

    def add(self, callback):
        if callback not in self.callbacks:
            self.callbacks.append(callback)
            return True

        return False

    def remove(self, callback):
        if callback in self.callbacks:
            self.callbacks.remove(callback)
            return True

        return False

    async def __call__(self, *args, **kwargs):
        for callback in self.callbacks:
            asyncs = []
            if asyncio.iscoroutinefunction(callback):
                asyncs.append(callback(*args, **kwargs))
            else:
                callback(*args, **kwargs)

            await asyncio.gather(*asyncs)

class ToshibaAcDevice:
    PERIODIC_STATE_RELOAD_PERIOD = 60 * 10

    def __init__(self, loop, name, device_id, ac_id, ac_unique_id, initial_ac_state, amqp_api, http_api):
        self.loop = loop
        self.name = name
        self.device_id = device_id
        self.ac_id = ac_id
        self.ac_unique_id = ac_unique_id
        self.amqp_api = amqp_api
        self.http_api = http_api
        self.fcu_state = ToshibaAcFcuState.from_hex_state(initial_ac_state)
        self._on_state_changed_callback = ToshibaAcDeviceCallback()
        self._on_energy_consumption_changed_callback = ToshibaAcDeviceCallback()
        self._ac_energy_consumption = None

    async def connect(self):
        self.periodic_reload_state_task = self.loop.create_task(self.periodic_state_reload())

    async def shutdown(self):
        self.periodic_reload_state_task.cancel()

    async def state_reload(self):
        hex_state = await self.http_api.get_device_state(self.ac_id)
        logger.debug(f'[{self.name}] AC state from HTTP: {hex_state}')
        if self.fcu_state.update(hex_state):
            await self.state_changed()

    async def state_changed(self):
        logger.info(f'[{self.name}] Current state: {self.fcu_state}')
        await self.on_state_changed_callback(self)

    async def periodic_state_reload(self):
        while True:
            await asyncio.sleep(self.PERIODIC_STATE_RELOAD_PERIOD)
            await self.state_reload()

    async def handle_cmd_fcu_from_ac(self, payload):
        logger.debug(f'[{self.name}] AC state from AMQP: {payload["data"]}')
        if self.fcu_state.update(payload['data']):
            await self.state_changed()

    async def handle_cmd_heartbeat(self, payload):
        hb_data = {k : int(v, base=16) for k, v in payload.items()}
        logger.debug(f'[{self.name}] AC heartbeat from AMQP: {hb_data}')

    async def handle_update_ac_energy_consumption(self, val):
        if self._ac_energy_consumption != val:
            self._ac_energy_consumption = val

            logger.debug(f'[{self.name}] Energy consumption: {val}')

            await self.on_energy_consumption_changed_callback(self)

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
        future_state = ToshibaAcFcuState.from_hex_state(self.fcu_state.encode())
        future_state.update(state.encode())

        # In SAVE mode reported temperatures are 16 degrees higher than actual setpoint (only when heating)
        if state.ac_temperature not in [ToshibaAcFcuState.AcTemperature.NONE, ToshibaAcFcuState.AcTemperature.UNKNOWN]:
            if future_state.ac_mode == ToshibaAcFcuState.AcMode.HEAT:
                if future_state.ac_merit_a_feature == ToshibaAcFcuState.AcMeritAFeature.SAVE:
                    state.ac_temperature = ToshibaAcFcuState.AcTemperature(state.ac_temperature.value + 16)

        if future_state.ac_mode != ToshibaAcFcuState.AcMode.HEAT:
            state.ac_merit_b_feature = ToshibaAcFcuState.AcMeritBFeature.OFF

            if future_state.ac_merit_a_feature in [ToshibaAcFcuState.AcMeritAFeature.SAVE, ToshibaAcFcuState.AcMeritAFeature.FLOOR]:
                state.ac_merit_a_feature = ToshibaAcFcuState.AcMeritAFeature.OFF

        # If we are requesting to turn on, we have to clear self cleaning flag
        if state.ac_status == ToshibaAcFcuState.AcStatus.ON and self.fcu_state.ac_self_cleaning == ToshibaAcFcuState.AcSelfCleaning.ON:
            state.ac_self_cleaning = ToshibaAcFcuState.AcSelfCleaning.OFF

        logger.debug(f'[{self.name}] Sending command: {state}')

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
        # In SAVE mode reported temperatures are 16 degrees higher than actual setpoint (only when heating)

        ret = self.fcu_state.ac_temperature

        if self.fcu_state.ac_mode == ToshibaAcFcuState.AcMode.HEAT:
            if self.fcu_state.ac_merit_a_feature == ToshibaAcFcuState.AcMeritAFeature.SAVE:
                if self.fcu_state.ac_temperature not in [ToshibaAcFcuState.AcTemperature.NONE, ToshibaAcFcuState.AcTemperature.UNKNOWN]:
                    ret = ToshibaAcFcuState.AcTemperature(self.fcu_state.ac_temperature.value - 16)

        if ret in [ToshibaAcFcuState.AcTemperature.NONE, ToshibaAcFcuState.AcTemperature.UNKNOWN]:
            return None

        return ret.value

    async def set_ac_temperature(self, val):
        state = ToshibaAcFcuState()
        state.ac_temperature = int(val)

        await self.send_state_to_ac(state)

    @property
    def ac_fan_mode(self):
        return self.fcu_state.ac_fan_mode

    async def set_ac_fan_mode(self, val):
        state = ToshibaAcFcuState()
        state.ac_fan_mode = val

        await self.send_state_to_ac(state)

    @property
    def ac_swing_mode(self):
        return self.fcu_state.ac_swing_mode

    async def set_ac_swing_mode(self, val):
        state = ToshibaAcFcuState()
        state.ac_swing_mode = val

        await self.send_state_to_ac(state)

    @property
    def ac_power_selection(self):
        return self.fcu_state.ac_power_selection

    async def set_ac_power_selection(self, val):
        state = ToshibaAcFcuState()
        state.ac_power_selection = val

        await self.send_state_to_ac(state)

    @property
    def ac_merit_b_feature(self):
        return self.fcu_state.ac_merit_b_feature

    async def set_ac_merit_b_feature(self, val):
        state = ToshibaAcFcuState()
        state.ac_merit_b_feature = val

        await self.send_state_to_ac(state)

    @property
    def ac_merit_a_feature(self):
        return self.fcu_state.ac_merit_a_feature

    async def set_ac_merit_a_feature(self, val):
        state = ToshibaAcFcuState()
        state.ac_merit_a_feature = val

        await self.send_state_to_ac(state)

    @property
    def ac_air_pure_ion(self):
        return self.fcu_state.ac_air_pure_ion

    async def set_ac_air_pure_ion(self, val):
        state = ToshibaAcFcuState()
        state.ac_air_pure_ion = val

        await self.send_state_to_ac(state)

    @property
    def ac_indoor_temperature(self):
        ret = self.fcu_state.ac_indoor_temperature

        if ret in [ToshibaAcFcuState.AcTemperature.NONE, ToshibaAcFcuState.AcTemperature.UNKNOWN]:
            return None

        return ret.value

    @property
    def ac_outdoor_temperature(self):
        ret = self.fcu_state.ac_outdoor_temperature

        if ret in [ToshibaAcFcuState.AcTemperature.NONE, ToshibaAcFcuState.AcTemperature.UNKNOWN]:
            return None

        return ret.value

    @property
    def ac_self_cleaning(self):
        return self.fcu_state.ac_self_cleaning

    @property
    def ac_energy_consumption(self):
        return self._ac_energy_consumption

    @property
    def on_state_changed_callback(self):
        return self._on_state_changed_callback

    @property
    def on_energy_consumption_changed_callback(self):
        return self._on_energy_consumption_changed_callback

    def __repr__(self):
        return f'ToshibaAcDevice(name={self.name}, device_id={self.device_id}, ac_id={self.ac_id}, ac_unique_id={self.ac_unique_id})'
