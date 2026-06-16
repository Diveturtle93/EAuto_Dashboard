"""Shared decoder helpers for CAN status/state payloads."""

_STATE_MAP = {
    0x1: "Normal",
    0x2: "Warning",
    0x4: "Error",
    0x8: "Critical Error",
}


def decode_status_state(data, min_len=1):
    """Decode a CAN payload where byte 0 encodes status (low nibble) and state (high nibble).

    Returns (status_int, state_str) or (None, error_str) on invalid input.
    """
    if len(data) < min_len:
        return None, "Invalid payload length"

    first = data[0]
    status = first & 0x0F
    state_bits = (first >> 4) & 0x0F

    if state_bits == 0:
        state = "Invalid"
    elif state_bits in _STATE_MAP:
        state = _STATE_MAP[state_bits]
    else:
        state = "Severe Error"

    return status, state
