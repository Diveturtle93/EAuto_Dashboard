import struct

_NUM_MODULES       = 10
_SENSORS_PER_MSG   = 4   # 8 bytes / 2 bytes per sensor
_MSGS_PER_MOD      = 4   # 4 × 4 sensors = 16 sensors per module
BASE_ID            = 0x780


def build_temp_decoders() -> dict:
    """Return {can_id: decoder_fn} for all 40 cell-temperature messages (0x780–0x7A7)."""
    decoders = {}
    for m in range(_NUM_MODULES):
        for msg_i in range(_MSGS_PER_MOD):
            can_id      = BASE_ID + m * _MSGS_PER_MOD + msg_i
            sensor_base = msg_i * _SENSORS_PER_MSG

            def _make(module=m, sb=sensor_base):
                def _decode(data: bytes) -> dict:
                    out = {}
                    for i in range(_SENSORS_PER_MSG):
                        raw = struct.unpack_from(">H", data, i * 2)[0]
                        out[f"cell_t_m{module}_s{sb + i}"] = raw
                    return out
                return _decode

            decoders[can_id] = _make()
    return decoders
