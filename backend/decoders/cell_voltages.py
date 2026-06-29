import struct

_NUM_MODULES    = 10
_CELLS_PER_MSG  = 4   # 8 bytes / 2 bytes per cell
_MSGS_PER_MOD   = 3   # 3 × 4 cells = 12 cells per module
BASE_ID         = 0x680


def build_voltage_decoders() -> dict:
    """Return {can_id: decoder_fn} for all 30 cell-voltage messages (0x680–0x69D)."""
    decoders = {}
    for m in range(_NUM_MODULES):
        for msg_i in range(_MSGS_PER_MOD):
            can_id     = BASE_ID + m * _MSGS_PER_MOD + msg_i
            cell_base  = msg_i * _CELLS_PER_MSG

            def _make(module=m, cb=cell_base):
                def _decode(data: bytes) -> dict:
                    out = {}
                    for i in range(_CELLS_PER_MSG):
                        raw = struct.unpack_from(">H", data, i * 2)[0]
                        out[f"cell_v_m{module}_c{cb + i}"] = raw
                    return out
                return _decode

            decoders[can_id] = _make()
    return decoders
