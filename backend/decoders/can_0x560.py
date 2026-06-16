from .common import decode_status_state


def decode_0x560(data):
    """Decode the 0x560 (Motor) CAN payload into (status, state)."""
    return decode_status_state(data, min_len=4)
