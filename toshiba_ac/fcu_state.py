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

_NONE_VAL = -1

class ToshibaAcFcuState:

    AcTemperature = Enum('AcTemperature', tuple((str(i), i) for i in range(-100, 100)) + (("NONE", _NONE_VAL), ("UNKNOWN", 0x7f)))

    class AcNone(Enum):
        NONE = _NONE_VAL

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
        SWING_VERTICAL = 0x41
        SWING_HORIZONTAL = 0x42
        SWING_VERTICAL_AND_HORIZONTAL = 0x43
        FIXED_1 = 0x50
        FIXED_2 = 0x51
        FIXED_3 = 0x52
        FIXED_4 = 0x53
        FIXED_5 = 0x54
        INVALID = 0x00
        NONE = _NONE_VAL

    class AcPowerSelection(Enum):
        POWER_50 = 0x32
        POWER_75 = 0x4b
        POWER_100 = 0x64
        NONE = _NONE_VAL

    class AcMeritBFeature(Enum):
        FIREPLACE_1 = 0x02
        FIREPLACE_2 = 0x03
        OFF = 0x00
        NONE = 0x0f

    class AcMeritAFeature(Enum):
        HIGH_POWER = 0x01
        CDU_SILENT_1 = 0x02
        ECO = 0x03
        HEATING_8C = 0x04
        SLEEP_CARE = 0x05
        FLOOR = 0x06
        COMFORT = 0x07
        CDU_SILENT_2 = 0x0a
        OFF = 0x00
        NONE = 0x0f

    class AcAirPureIon(Enum):
        OFF = 0x10
        ON = 0x18
        NONE = _NONE_VAL

    class AcSelfCleaning(Enum):
        ON = 0x18
        OFF = 0x10
        NONE = _NONE_VAL

    @classmethod
    def from_hex_state(cls, hex_state):
        state = cls()
        state.decode(hex_state)
        return state

    def __init__(self):
        self.ac_status = ToshibaAcFcuState.AcStatus.NONE
        self.ac_mode = ToshibaAcFcuState.AcMode.NONE
        self.ac_temperature = ToshibaAcFcuState.AcTemperature.NONE
        self.ac_fan_mode = ToshibaAcFcuState.AcFanMode.NONE
        self.ac_swing_mode = ToshibaAcFcuState.AcSwingMode.NONE
        self.ac_power_selection = ToshibaAcFcuState.AcPowerSelection.NONE
        self.ac_merit_b_feature = ToshibaAcFcuState.AcMeritBFeature.NONE
        self.ac_merit_a_feature = ToshibaAcFcuState.AcMeritAFeature.NONE
        self.ac_air_pure_ion = ToshibaAcFcuState.AcAirPureIon.NONE
        self.ac_indoor_temperature = ToshibaAcFcuState.AcTemperature.NONE
        self.ac_outdoor_temperature = ToshibaAcFcuState.AcTemperature.NONE

        self.ac_self_cleaning = ToshibaAcFcuState.AcSelfCleaning.NONE

    def encode(self):
        data = (self.ac_status,
                self.ac_mode,
                self.ac_temperature,
                self.ac_fan_mode,
                self.ac_swing_mode,
                self.ac_power_selection,
                self.ac_merit_b_feature,
                self.ac_merit_a_feature,
                self.ac_air_pure_ion,
                self.ac_indoor_temperature,
                self.ac_outdoor_temperature,
                ToshibaAcFcuState.AcNone.NONE,
                ToshibaAcFcuState.AcNone.NONE,
                ToshibaAcFcuState.AcNone.NONE,
                ToshibaAcFcuState.AcNone.NONE,
                self.ac_self_cleaning,
                ToshibaAcFcuState.AcNone.NONE,
                ToshibaAcFcuState.AcNone.NONE,
                ToshibaAcFcuState.AcNone.NONE,
                ToshibaAcFcuState.AcNone.NONE)
        encoded = struct.pack('bbbbbbbbbbbbbbbbbbbb', *[prop.value for prop in data]).hex()
        return encoded[:12] + encoded[13] + encoded[15] + encoded[16:] # Merit A/B features are encoded using half bytes but our packing added them as bytes


    def decode(self, hex_state):
        extended_hex_state = hex_state[:12] + '0' + hex_state[12] + '0' + hex_state[13:] # Merit A/B features are encoded using half bytes but our unpacking expect them as bytes
        data = struct.unpack('bbbbbbbbbbbbbbbbbbbb', bytes.fromhex(extended_hex_state))
        (self.ac_status,
        self.ac_mode,
        self.ac_temperature,
        self.ac_fan_mode,
        self.ac_swing_mode,
        self.ac_power_selection,
        self.ac_merit_b_feature,
        self.ac_merit_a_feature,
        self.ac_air_pure_ion,
        self.ac_indoor_temperature,
        self.ac_outdoor_temperature,
        _,
        _,
        _,
        _,
        self.ac_self_cleaning,
        *_) = data

    def update(self, hex_state):
        state_update = ToshibaAcFcuState.from_hex_state(hex_state)

        changed = False

        if state_update.ac_status not in [ToshibaAcFcuState.AcStatus.NONE, self.ac_status]:
            self.ac_status = state_update.ac_status
            changed = True

        if state_update.ac_mode not in [ToshibaAcFcuState.AcMode.NONE, self.ac_mode]:
            self.ac_mode = state_update.ac_mode
            changed = True

        if state_update.ac_temperature not in [ToshibaAcFcuState.AcTemperature.NONE, self.ac_temperature]:
            self.ac_temperature = state_update.ac_temperature
            changed = True

        if state_update.ac_fan_mode not in [ToshibaAcFcuState.AcFanMode.NONE, self.ac_fan_mode]:
            self.ac_fan_mode = state_update.ac_fan_mode
            changed = True

        if state_update.ac_swing_mode not in [ToshibaAcFcuState.AcSwingMode.NONE, self.ac_swing_mode]:
            self.ac_swing_mode = state_update.ac_swing_mode
            changed = True

        if state_update.ac_power_selection not in [ToshibaAcFcuState.AcPowerSelection.NONE, self.ac_power_selection]:
            self.ac_power_selection = state_update.ac_power_selection
            changed = True

        if state_update.ac_merit_b_feature not in [ToshibaAcFcuState.AcMeritBFeature.NONE, self.ac_merit_b_feature]:
            self.ac_merit_b_feature = state_update.ac_merit_b_feature
            changed = True

        if state_update.ac_merit_a_feature not in [ToshibaAcFcuState.AcMeritAFeature.NONE, self.ac_merit_a_feature]:
            self.ac_merit_a_feature = state_update.ac_merit_a_feature
            changed = True

        if state_update.ac_air_pure_ion not in [ToshibaAcFcuState.AcAirPureIon.NONE, self.ac_air_pure_ion]:
            self.ac_air_pure_ion = state_update.ac_air_pure_ion
            changed = True

        if state_update.ac_indoor_temperature not in [ToshibaAcFcuState.AcTemperature.NONE, self.ac_indoor_temperature]:
            self.ac_indoor_temperature = state_update.ac_indoor_temperature
            changed = True

        if state_update.ac_outdoor_temperature not in [ToshibaAcFcuState.AcTemperature.NONE, self.ac_outdoor_temperature]:
            self.ac_outdoor_temperature = state_update.ac_outdoor_temperature
            changed = True

        if state_update.ac_self_cleaning not in [ToshibaAcFcuState.AcSelfCleaning.NONE, self.ac_self_cleaning]:
            self.ac_self_cleaning = state_update.ac_self_cleaning
            changed = True

        return changed

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
        self._ac_temperature = ToshibaAcFcuState.AcTemperature(val)

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

    @property
    def ac_merit_b_feature(self):
        return self._ac_merit_b_feature

    @ac_merit_b_feature.setter
    def ac_merit_b_feature(self, val):
        self._ac_merit_b_feature = ToshibaAcFcuState.AcMeritBFeature(val)

    @property
    def ac_merit_a_feature(self):
        return self._ac_merit_a_feature

    @ac_merit_a_feature.setter
    def ac_merit_a_feature(self, val):
        self._ac_merit_a_feature = ToshibaAcFcuState.AcMeritAFeature(val)

    @property
    def ac_air_pure_ion(self):
        return self._ac_air_pure_ion

    @ac_air_pure_ion.setter
    def ac_air_pure_ion(self, val):
        self._ac_air_pure_ion = ToshibaAcFcuState.AcAirPureIon(val)

    @property
    def ac_indoor_temperature(self):
        return self._ac_indoor_temperature

    @ac_indoor_temperature.setter
    def ac_indoor_temperature(self, val):
        self._ac_indoor_temperature = ToshibaAcFcuState.AcTemperature(val)

    @property
    def ac_outdoor_temperature(self):
        return self._ac_outdoor_temperature

    @ac_outdoor_temperature.setter
    def ac_outdoor_temperature(self, val):
        self._ac_outdoor_temperature = ToshibaAcFcuState.AcTemperature(val)

    @property
    def ac_self_cleaning(self):
        return self._ac_self_cleaning

    @ac_self_cleaning.setter
    def ac_self_cleaning(self, val):
        self._ac_self_cleaning = ToshibaAcFcuState.AcSelfCleaning(val)

    def __str__(self):
        res = f'AcStatus: {self.ac_status.name}'
        res += f', AcMode: {self.ac_mode.name}'
        res += f', AcTemperature: {self.ac_temperature.name}'
        res += f', AcFanMode: {self.ac_fan_mode.name}'
        res += f', AcSwingMode: {self.ac_swing_mode.name}'
        res += f', AcPowerSelection: {self.ac_power_selection.name}'
        res += f', AcMeritBFeature: {self.ac_merit_b_feature.name}'
        res += f', AcMeritAFeature: {self.ac_merit_a_feature.name}'
        res += f', AcAirPureIon: {self.ac_air_pure_ion.name}'
        res += f', AcIndoorAcTemperature: {self.ac_indoor_temperature.name}'
        res += f', AcOutdoorAcTemperature: {self.ac_outdoor_temperature.name}'
        res += f', AcSelfCleaning: {self.ac_self_cleaning.name}'

        return res
