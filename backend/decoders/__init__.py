from .can_0x505 import decode_0x505
from .can_0x560 import decode_0x560

# Each entry: CAN-ID -> (decoder_fn, status_key, state_key)
DECODERS = {
    0x505: (decode_0x505, "bms_status_code",   "bms_state"),
    0x560: (decode_0x560, "motor_status_code", "motor_state"),
}


def decode_can_message(can_id, data):
    """Return (status, state, status_key, state_key) or None if ID unknown."""
    entry = DECODERS.get(can_id)
    if entry is None:
        return None
    decoder, status_key, state_key = entry
    result = decoder(data)
    if result is None:
        return None
    status, state = result
    return status, state, status_key, state_key
