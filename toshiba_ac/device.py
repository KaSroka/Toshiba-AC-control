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

from toshiba_ac.fcu_state import ToshibaAcFcuState
from toshiba_ac.utils import async_sleep_until_next_multiply_of_minutes

from azure.iot.device import Message
from dataclasses import dataclass
import asyncio

import datetime
import struct
import logging

logger = logging.getLogger(__name__)

class ToshibaAcDeviceError(Exception):
    pass

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
    STATE_RELOAD_PERIOD_MINUTES = 30

    def __init__(self, loop, name, device_id, ac_id, ac_unique_id, initial_ac_state, firmware_version, merit_feature, ac_model_id, amqp_api, http_api):
        self.loop = loop
        self.name = name
        self.device_id = device_id
        self.ac_id = ac_id
        self.ac_unique_id = ac_unique_id
        self.firmware_version = firmware_version
        self.amqp_api = amqp_api
        self.http_api = http_api

        self.fcu_state = ToshibaAcFcuState.from_hex_state(initial_ac_state)

        self.cdu = None
        self.fcu = None
        self._supported_merit_a_features = None
        self._supported_merit_b_features = None
        self._is_pure_ion_supported = None
        self._on_state_changed_callback = ToshibaAcDeviceCallback()
        self._on_energy_consumption_changed_callback = ToshibaAcDeviceCallback()
        self._ac_energy_consumption = None

        self.load_supported_merit_features(merit_feature, ac_model_id)

    async def connect(self):
        await self.load_additional_device_info()
        self.periodic_reload_state_task = self.loop.create_task(self.periodic_state_reload())

    async def shutdown(self):
        self.periodic_reload_state_task.cancel()

    async def load_additional_device_info(self):
        additional_info = await self.http_api.get_device_additional_info(self.ac_id)
        self.cdu = additional_info.cdu
        self.fcu = additional_info.fcu
        await self.on_state_changed_callback(self)

    def load_supported_merit_features(self, merit_feature_hexstring, ac_model_id):
        try:
            merit_byte, = struct.unpack('b', bytes.fromhex(merit_feature_hexstring[:2]))
        except (TypeError, ValueError, struct.error):
            ac_model_id = '1'

        supported_a_features = [ToshibaAcFcuState.AcMeritAFeature.OFF]
        supported_b_features = [ToshibaAcFcuState.AcMeritBFeature.OFF]
        pure_ion = False

        if ac_model_id != '1':
            supported_a_features.append(ToshibaAcFcuState.AcMeritAFeature.HIGH_POWER)
            supported_a_features.append(ToshibaAcFcuState.AcMeritAFeature.ECO)

            floor, _, cdu_silent, pure_ion, fireplace, heating_8c, _, _ = struct.unpack('????????', bytes.fromhex('0' + '0'.join(f'{merit_byte:08b}')))

            if floor:
                supported_a_features.append(ToshibaAcFcuState.AcMeritAFeature.FLOOR)

            if cdu_silent:
                supported_a_features.append(ToshibaAcFcuState.AcMeritAFeature.CDU_SILENT_1)
                supported_a_features.append(ToshibaAcFcuState.AcMeritAFeature.CDU_SILENT_2)

            if fireplace:
                supported_b_features.append(ToshibaAcFcuState.AcMeritBFeature.FIREPLACE_1)
                supported_b_features.append(ToshibaAcFcuState.AcMeritBFeature.FIREPLACE_2)

            if heating_8c:
                supported_a_features.append(ToshibaAcFcuState.AcMeritAFeature.HEATING_8C)

        self._supported_merit_a_features = supported_a_features
        self._supported_merit_b_features = supported_b_features
        self._is_pure_ion_supported = pure_ion

        logger.debug(
            '[{}] Supported merit A features: {}. Supported merit B features: {}. Pure ION supported: {}'.format(
                self.name,
                ", ".join(f.name.title().replace("_", " ") for f in supported_a_features),
                ", ".join(f.name.title().replace("_", " ") for f in supported_b_features),
                pure_ion
            )
        )

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
            await async_sleep_until_next_multiply_of_minutes(self.STATE_RELOAD_PERIOD_MINUTES)
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
                if future_state.ac_merit_a_feature == ToshibaAcFcuState.AcMeritAFeature.HEATING_8C:
                    state.ac_temperature = ToshibaAcFcuState.AcTemperature(state.ac_temperature.value + 16)

        if future_state.ac_mode != ToshibaAcFcuState.AcMode.HEAT:
            state.ac_merit_b_feature = ToshibaAcFcuState.AcMeritBFeature.OFF

            if future_state.ac_merit_a_feature in [ToshibaAcFcuState.AcMeritAFeature.HEATING_8C, ToshibaAcFcuState.AcMeritAFeature.FLOOR]:
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
            if self.fcu_state.ac_merit_a_feature == ToshibaAcFcuState.AcMeritAFeature.HEATING_8C:
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
        if val != ToshibaAcFcuState.AcMeritBFeature.NONE and val not in self.supported_merit_b_features:
            raise ToshibaAcDeviceError(f'Trying to set unsupported merit b feature: {val.name.title().replace("_", " ")}')

        state = ToshibaAcFcuState()
        state.ac_merit_b_feature = val

        await self.send_state_to_ac(state)

    @property
    def ac_merit_a_feature(self):
        return self.fcu_state.ac_merit_a_feature

    async def set_ac_merit_a_feature(self, val):
        if val != ToshibaAcFcuState.AcMeritAFeature.NONE and val not in self.supported_merit_a_features:
            raise ToshibaAcDeviceError(f'Trying to set unsupported merit a feature: {val.name.title().replace("_", " ")}')

        state = ToshibaAcFcuState()
        state.ac_merit_a_feature = val

        await self.send_state_to_ac(state)

    @property
    def ac_air_pure_ion(self):
        return self.fcu_state.ac_air_pure_ion

    async def set_ac_air_pure_ion(self, val):
        if not self.is_pure_ion_supported:
            raise ToshibaAcDeviceError('Pure Ion feature is not supported by this device')
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

    @property
    def supported_merit_a_features(self):
        return self._supported_merit_a_features

    @property
    def supported_merit_b_features(self):
        return self._supported_merit_b_features

    @property
    def is_pure_ion_supported(self):
        return self._is_pure_ion_supported

    def __repr__(self):
        return f'ToshibaAcDevice(name={self.name}, device_id={self.device_id}, ac_id={self.ac_id}, ac_unique_id={self.ac_unique_id})'
