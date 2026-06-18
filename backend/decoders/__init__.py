# ── Single-value decoders ──────────────────────────────────────────────────────
# Maps CAN-ID → (decoder_fn, status_key, state_key)
# Example:
#   from .can_0x505 import decode_0x505
#   DECODERS[0x505] = (decode_0x505, "motor_status_code", "motor_state")
DECODERS = {}

# ── Multi-value decoders ───────────────────────────────────────────────────────
# Maps CAN-ID → decoder_fn returning {key: value, ...}
# Example:
#   from .can_0x538 import decode_0x538
#   MULTI_DECODERS[0x538] = decode_0x538
MULTI_DECODERS = {}


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


def decode_can_multi(can_id, data):
    """Return {key: value, ...} dict or None if ID not in MULTI_DECODERS."""
    decoder = MULTI_DECODERS.get(can_id)
    if decoder is None:
        return None
    return decoder(data)
