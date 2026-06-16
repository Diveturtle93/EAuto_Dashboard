from .common import decode_status_state


def decode_0x505(data):
    """Decode the 0x505 (BMS) CAN payload into (status, state)."""
    return decode_status_state(data, min_len=1)
