# Copyright 2022 Kamil Sroka

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto


@dataclass
class ToshibaAcDeviceEnergyConsumption:
    energy_wh: float
    since: datetime


class ToshibaAcStatus(Enum):
    ON = auto()
    OFF = auto()
    NONE = None


class ToshibaAcMode(Enum):
    AUTO = auto()
    COOL = auto()
    HEAT = auto()
    DRY = auto()
    FAN = auto()
    NONE = None


class ToshibaAcFanMode(Enum):
    AUTO = auto()
    QUIET = auto()
    LOW = auto()
    MEDIUM_LOW = auto()
    MEDIUM = auto()
    MEDIUM_HIGH = auto()
    HIGH = auto()
    NONE = None


class ToshibaAcSwingMode(Enum):
    OFF = auto()
    SWING_VERTICAL = auto()
    SWING_HORIZONTAL = auto()
    SWING_VERTICAL_AND_HORIZONTAL = auto()
    FIXED_1 = auto()
    FIXED_2 = auto()
    FIXED_3 = auto()
    FIXED_4 = auto()
    FIXED_5 = auto()
    HADA_CARE_FLOW = auto()
    LOUVER_OFF = auto()
    LOUVER_UD_TOP = auto()
    LOUVER_UD_UPPER = auto()
    LOUVER_UD_MIDDLE = auto()
    LOUVER_UD_LOWER = auto()
    LOUVER_UD_BOTTOM = auto()
    LOUVER_LR_LEFT_MAX = auto()
    LOUVER_LR_LEFT = auto()
    LOUVER_LR_CENTER = auto()
    LOUVER_LR_RIGHT = auto()
    LOUVER_LR_RIGHT_MAX = auto()
    LOUVER_TOP_LEFT_MAX = auto()
    LOUVER_TOP_LEFT = auto()
    LOUVER_TOP_CENTER = auto()
    LOUVER_TOP_RIGHT = auto()
    LOUVER_TOP_RIGHT_MAX = auto()
    LOUVER_UPPER_LEFT_MAX = auto()
    LOUVER_UPPER_LEFT = auto()
    LOUVER_UPPER_CENTER = auto()
    LOUVER_UPPER_RIGHT = auto()
    LOUVER_UPPER_RIGHT_MAX = auto()
    LOUVER_MIDDLE_LEFT_MAX = auto()
    LOUVER_MIDDLE_LEFT = auto()
    LOUVER_MIDDLE_CENTER = auto()
    LOUVER_MIDDLE_RIGHT = auto()
    LOUVER_MIDDLE_RIGHT_MAX = auto()
    LOUVER_LOWER_LEFT_MAX = auto()
    LOUVER_LOWER_LEFT = auto()
    LOUVER_LOWER_CENTER = auto()
    LOUVER_LOWER_RIGHT = auto()
    LOUVER_LOWER_RIGHT_MAX = auto()
    LOUVER_BOTTOM_LEFT_MAX = auto()
    LOUVER_BOTTOM_LEFT = auto()
    LOUVER_BOTTOM_CENTER = auto()
    LOUVER_BOTTOM_RIGHT = auto()
    LOUVER_BOTTOM_RIGHT_MAX = auto()
    LOUVER_SWING_UD = auto()
    LOUVER_SWING_LR = auto()
    LOUVER_SWING_BOTH = auto()
    NONE = None


class ToshibaAcPowerSelection(Enum):
    POWER_50 = auto()
    POWER_75 = auto()
    POWER_100 = auto()
    NONE = None


class ToshibaAcMeritB(Enum):
    FIREPLACE_1 = auto()
    FIREPLACE_2 = auto()
    OFF = auto()
    NONE = None


class ToshibaAcMeritA(Enum):
    HIGH_POWER = auto()
    CDU_SILENT_1 = auto()
    ECO = auto()
    HEATING_8C = auto()
    SLEEP_CARE = auto()
    FLOOR = auto()
    COMFORT = auto()
    CDU_SILENT_2 = auto()
    OFF = auto()
    NONE = None


class ToshibaAcAirPureIon(Enum):
    OFF = auto()
    ON = auto()
    NONE = None


class ToshibaAcSelfCleaning(Enum):
    ON = auto()
    OFF = auto()
    NONE = None
