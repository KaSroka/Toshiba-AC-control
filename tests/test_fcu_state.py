from toshiba_ac.device.fcu_state import ToshibaAcFcuState
from toshiba_ac.device.properties import ToshibaAcSwingMode


def test_shorai_louver_raw_values_round_trip() -> None:
    values = {
        0x60: ToshibaAcSwingMode.HADA_CARE_FLOW,
        0x80: ToshibaAcSwingMode.LOUVER_OFF,
        0x81: ToshibaAcSwingMode.LOUVER_UD_TOP,
        0x85: ToshibaAcSwingMode.LOUVER_UD_BOTTOM,
        0x88: ToshibaAcSwingMode.LOUVER_LR_LEFT_MAX,
        0x98: ToshibaAcSwingMode.LOUVER_LR_CENTER,
        0xA8: ToshibaAcSwingMode.LOUVER_LR_RIGHT_MAX,
        0x89: ToshibaAcSwingMode.LOUVER_TOP_LEFT_MAX,
        0x9D: ToshibaAcSwingMode.LOUVER_BOTTOM_CENTER,
        0xAD: ToshibaAcSwingMode.LOUVER_BOTTOM_RIGHT_MAX,
        0x9E: ToshibaAcSwingMode.LOUVER_SWING_UD,
        0xB1: ToshibaAcSwingMode.LOUVER_SWING_LR,
        0xB6: ToshibaAcSwingMode.LOUVER_SWING_BOTH,
    }

    for raw, mode in values.items():
        assert ToshibaAcFcuState.AcSwingMode.from_raw(raw) == mode
        assert ToshibaAcFcuState.AcSwingMode.to_raw(mode) == raw
