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

from enum import Enum
import struct

_NONE_VAL = 0xff

class ToshibaAcFcuState:

    class IntValue:
        def __init__(self, val):
            if isinstance(val, ToshibaAcFcuState.IntValue):
                self.name = val.name
            else:
                self.name = val

        @property
        def name(self):
            if self._value != _NONE_VAL:
                return self._value
            else:
                return None

        @name.setter
        def name(self, val):
            if val == None:
                self._value = _NONE_VAL
            else:
                self._value = val

        @property
        def value(self):
            return self._value

        def __str__(self):
            return f'{self.name}'

    class AcStatus(Enum):
        ON = 0x30
        OFF = 0x31
        INVALID = 0x02
        NONE = _NONE_VAL

    class AcMode(Enum):
        AUTO = 0x41
        COOL = 0x42
        HEAT = 0x43
        DRY = 0x44
        FAN = 0x45
        INVALID = 0x00
        NONE = _NONE_VAL

    class AcFanMode(Enum):
        AUTO = 0x41
        QUIET = 0x31
        LOW = 0x32
        MEDIUM_LOW = 0x33
        MEDIUM = 0x34
        MEDIUM_HIGH = 0x35
        HIGH = 0x36
        INVALID = 0x00
        NONE = _NONE_VAL

    class AcSwingMode(Enum):
        NOT_USED = 0x31
        ON = 0x41
        INVALID = 0x00
        NONE = _NONE_VAL

    class AcPowerSelection(Enum):
        POWER_50 = 0x32
        POWER_75 = 0x4b
        POWER_100 = 0x64
        NONE = _NONE_VAL

    @classmethod
    def from_hex_state(cls, hex_state):
        state = cls()
        state.decode(hex_state)
        return state

    def __init__(self):
        self.ac_status = ToshibaAcFcuState.AcStatus.NONE
        self.ac_mode = ToshibaAcFcuState.AcMode.NONE
        self.ac_temperature = ToshibaAcFcuState.IntValue(None)
        self.ac_indoor_temperature = ToshibaAcFcuState.IntValue(None)
        self.ac_outdoor_temperature = ToshibaAcFcuState.IntValue(None)
        self.ac_fan_mode = ToshibaAcFcuState.AcFanMode.NONE
        self.ac_swing_mode = ToshibaAcFcuState.AcSwingMode.NONE
        self.ac_power_selection = ToshibaAcFcuState.AcPowerSelection.NONE

    def encode(self):
        data = (self.ac_status, self.ac_mode, self.ac_temperature, self.ac_fan_mode, self.ac_swing_mode, self.ac_power_selection, ToshibaAcFcuState.IntValue(None), self.ac_indoor_temperature, self.ac_outdoor_temperature, ToshibaAcFcuState.IntValue(None), ToshibaAcFcuState.IntValue(None), ToshibaAcFcuState.IntValue(None), ToshibaAcFcuState.IntValue(None), ToshibaAcFcuState.IntValue(None), ToshibaAcFcuState.IntValue(None), ToshibaAcFcuState.IntValue(None), ToshibaAcFcuState.IntValue(None), ToshibaAcFcuState.IntValue(None), ToshibaAcFcuState.IntValue(None))
        return struct.pack('BBBBBBBBBBBBBBBBBBB', *[prop.value for prop in data]).hex()

    def decode(self, hex_state):
        data = struct.unpack('BBBBBBBBBBBBBBBBBBB', bytes.fromhex(hex_state))
        self.ac_status, self.ac_mode, self.ac_temperature, self.ac_fan_mode, self.ac_swing_mode, self.ac_power_selection, _, self.ac_indoor_temperature, self.ac_outdoor_temperature, *_ = data

    def update(self, hex_state):
        state_update = ToshibaAcFcuState.from_hex_state(hex_state)

        if state_update.ac_status != ToshibaAcFcuState.AcStatus.NONE:
            self.ac_status = state_update.ac_status

        if state_update.ac_mode != ToshibaAcFcuState.AcMode.NONE:
            self.ac_mode = state_update.ac_mode

        if state_update.ac_temperature.name != None:
            self.ac_temperature = state_update.ac_temperature

        if state_update.ac_indoor_temperature.name != None:
            self.ac_indoor_temperature = state_update.ac_indoor_temperature

        if state_update.ac_outdoor_temperature.name != None:
            self.ac_outdoor_temperature = state_update.ac_outdoor_temperature

        if state_update.ac_fan_mode != ToshibaAcFcuState.AcFanMode.NONE:
            self.ac_fan_mode = state_update.ac_fan_mode

        if state_update.ac_swing_mode != ToshibaAcFcuState.AcSwingMode.NONE:
            self.ac_swing_mode = state_update.ac_swing_mode

        if state_update.ac_power_selection != ToshibaAcFcuState.AcPowerSelection.NONE:
            self.ac_power_selection = state_update.ac_power_selection

    @property
    def ac_status(self):
        return self._ac_status

    @ac_status.setter
    def ac_status(self, val):
        self._ac_status = ToshibaAcFcuState.AcStatus(val)

    @property
    def ac_mode(self):
        return self._ac_mode

    @ac_mode.setter
    def ac_mode(self, val):
        self._ac_mode = ToshibaAcFcuState.AcMode(val)

    @property
    def ac_temperature(self):
        return self._ac_temperature

    @ac_temperature.setter
    def ac_temperature(self, val):
        self._ac_temperature = ToshibaAcFcuState.IntValue(val)

    @property
    def ac_indoor_temperature(self):
        return self._ac_indoor_temperature

    @ac_indoor_temperature.setter
    def ac_indoor_temperature(self, val):
        self._ac_indoor_temperature = ToshibaAcFcuState.IntValue(val)

    @property
    def ac_outdoor_temperature(self):
        return self._ac_outdoor_temperature

    @ac_outdoor_temperature.setter
    def ac_outdoor_temperature(self, val):
        self._ac_outdoor_temperature = ToshibaAcFcuState.IntValue(val)


    @property
    def ac_fan_mode(self):
        return self._ac_fan_mode

    @ac_fan_mode.setter
    def ac_fan_mode(self, val):
        self._ac_fan_mode = ToshibaAcFcuState.AcFanMode(val)

    @property
    def ac_swing_mode(self):
        return self._ac_swing_mode

    @ac_swing_mode.setter
    def ac_swing_mode(self, val):
        self._ac_swing_mode = ToshibaAcFcuState.AcSwingMode(val)

    @property
    def ac_power_selection(self):
        return self._ac_power_selection

    @ac_power_selection.setter
    def ac_power_selection(self, val):
        self._ac_power_selection = ToshibaAcFcuState.AcPowerSelection(val)

    def __str__(self):
        return f'AcStatus: {self.ac_status}, AcMode: {self.ac_mode}, AcTemperature: {self.ac_temperature}, AcFanMode: {self.ac_fan_mode}, AcSwingMode: {self.ac_swing_mode}, AcPowerSelection: {self.ac_power_selection}, AcIndoorTemperature: {self.ac_indoor_temperature}, AcOutdoorTemperature: {self.ac_outdoor_temperature}'
