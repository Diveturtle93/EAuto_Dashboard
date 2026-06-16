import threading
import time

import can  # python-can: cross-platform CAN library

from backend.decoders import decode_can_message


class CanConfig:
    def __init__(self, interface, channel, bitrate, reconnect_delay=3.0, timeout=0.5):
        self.interface = interface
        self.channel = channel
        self.bitrate = bitrate
        self.reconnect_delay = reconnect_delay
        self.timeout = timeout


_BACKOFF_MAX = 30.0  # seconds


def can_rx_thread(config, latest=None, lock=None):
    """Open CAN bus via python-can and receive frames indefinitely.

    Reconnects automatically on errors using exponential backoff (capped at
    _BACKOFF_MAX seconds). Decodes registered CAN IDs into the shared
    latest snapshot using per-ID key mappings from the decoder registry.
    """
    backoff = config.reconnect_delay

    while True:
        try:
            bus = can.Bus(interface=config.interface,
                          channel=config.channel,
                          bitrate=config.bitrate)
            print(f"[CAN] Connected: interface={config.interface}, channel={config.channel}, bitrate={config.bitrate}")
            backoff = config.reconnect_delay  # reset on successful connect
        except (can.CanError, OSError, ValueError) as e:
            print(f"[CAN] Cannot open {config.interface}/{config.channel}: {e}  -- retrying in {backoff:.0f} s")
            time.sleep(backoff)
            backoff = min(backoff * 2, _BACKOFF_MAX)
            continue

        while True:
            try:
                msg = bus.recv(timeout=config.timeout)
            except can.CanError as e:
                print(f"[CAN] Bus error: {e}  -- reconnecting in {backoff:.0f} s")
                break

            if msg is None:
                continue

            can_id = msg.arbitration_id
            d = list(msg.data)

            if latest is not None and lock is not None:
                with lock:
                    latest["last_rx_ms"] = int(time.time() * 1000)

                    decoded = decode_can_message(can_id, d)
                    if decoded is not None:
                        status, state, status_key, state_key = decoded
                        latest[status_key] = status
                        latest[state_key] = state

        try:
            bus.shutdown()
        except (can.CanError, OSError):
            pass
        time.sleep(backoff)
        backoff = min(backoff * 2, _BACKOFF_MAX)


def start_can_rx_thread(config, latest=None, lock=None):
    thread = threading.Thread(target=can_rx_thread, args=(config, latest, lock), daemon=True)
    thread.start()
    return thread
