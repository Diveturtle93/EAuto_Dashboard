import threading
import time

import can  # python-can: cross-platform CAN library

from backend.decoders import decode_can_message, decode_can_multi


class CanConfig:
    def __init__(self, interface, channel, bitrate, reconnect_delay=3.0, timeout=0.5):
        self.interface = interface
        self.channel = channel
        self.bitrate = bitrate
        self.reconnect_delay = reconnect_delay
        self.timeout = timeout


_BACKOFF_MAX = 30.0  # seconds


def can_rx_thread(config, latest=None, lock=None, stop_event=None,
                  set_bus=None, clear_bus=None):
    """Open CAN bus via python-can and receive frames indefinitely.

    Reconnects automatically on errors using exponential backoff (capped at
    _BACKOFF_MAX seconds). Decodes registered CAN IDs into the shared
    latest snapshot using per-ID key mappings from the decoder registry.
    Exits cleanly when stop_event is set.
    """
    backoff = config.reconnect_delay

    while True:
        if stop_event and stop_event.is_set():
            print("[CAN] Thread stopped.")
            return

        try:
            bus = can.Bus(interface=config.interface,
                          channel=config.channel,
                          bitrate=config.bitrate)
            print(f"[CAN] Connected: interface={config.interface}, channel={config.channel}, bitrate={config.bitrate}")
            backoff = config.reconnect_delay  # reset on successful connect
            if set_bus:
                set_bus(bus)
            if latest is not None and lock is not None:
                with lock:
                    latest["can_adapter_connected"] = True
        except (can.CanError, OSError, ValueError) as e:
            print(f"[CAN] Cannot open {config.interface}/{config.channel}: {e}  -- retrying in {backoff:.0f} s")
            if latest is not None and lock is not None:
                with lock:
                    latest["can_adapter_connected"] = False
            deadline = time.time() + backoff
            while time.time() < deadline:
                if stop_event and stop_event.is_set():
                    return
                time.sleep(0.1)
            backoff = min(backoff * 2, _BACKOFF_MAX)
            continue

        while True:
            if stop_event and stop_event.is_set():
                if clear_bus:
                    clear_bus()
                try:
                    bus.shutdown()
                except (can.CanError, OSError):
                    pass
                if latest is not None and lock is not None:
                    with lock:
                        latest["can_adapter_connected"] = False
                print("[CAN] Thread stopped.")
                return

            try:
                msg = bus.recv(timeout=config.timeout)
            except can.CanError as e:
                print(f"[CAN] Bus error: {e}  -- reconnecting in {backoff:.0f} s")
                if latest is not None and lock is not None:
                    with lock:
                        latest["can_adapter_connected"] = False
                break

            if msg is None:
                continue

            can_id = msg.arbitration_id
            rx_ts  = time.time()

            # Decode outside the lock — pure functions, no shared state
            try:
                decoded = decode_can_message(can_id, msg.data)
                decoded_multi = decode_can_multi(can_id, msg.data)
            except Exception as exc:
                print(f"[CAN] Decoder error for ID 0x{can_id:03X}: {exc}")
                decoded = None
                decoded_multi = None

            if latest is not None and lock is not None:
                with lock:
                    latest["last_rx_ms"] = int(rx_ts * 1000)
                    latest["_can_rx_ts"][can_id] = rx_ts
                    if decoded is not None:
                        status, state, status_key, state_key = decoded
                        latest[status_key] = status
                        latest[state_key] = state
                    if decoded_multi is not None:
                        latest.update(decoded_multi)

        # Bus-Fehler: Referenz freigeben, dann shutdown
        if clear_bus:
            clear_bus()
        try:
            bus.shutdown()
        except (can.CanError, OSError):
            pass

        deadline = time.time() + backoff
        while time.time() < deadline:
            if stop_event and stop_event.is_set():
                return
            time.sleep(0.1)
        backoff = min(backoff * 2, _BACKOFF_MAX)


class CanManager:
    """Manages the CAN receive thread lifecycle (start / stop at runtime)."""

    def __init__(self):
        self._thread = None
        self._stop_event = None
        self._config = None
        self._lock = threading.Lock()
        self._bus = None
        self._bus_lock = threading.Lock()

    def _set_bus(self, bus):
        with self._bus_lock:
            self._bus = bus

    def _clear_bus(self):
        with self._bus_lock:
            self._bus = None

    def start(self, config, latest, lock):
        with self._lock:
            self._stop_internal()
            self._stop_event = threading.Event()
            self._config = config
            self._thread = threading.Thread(
                target=can_rx_thread,
                args=(config, latest, lock, self._stop_event,
                      self._set_bus, self._clear_bus),
                daemon=True,
            )
            self._thread.start()
        print(f"[CAN] Manager started: {config.interface}/{config.channel} @ {config.bitrate} bps")

    def stop(self):
        with self._lock:
            self._stop_internal()
        print("[CAN] Manager stopped.")

    def _stop_internal(self):
        if self._stop_event:
            self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5.0)
        self._thread = None
        self._stop_event = None
        self._config = None

    def send(self, can_id: int, data: bytes, is_extended_id: bool = False) -> bool:
        """Send a single CAN frame over the already-open RX bus."""
        with self._bus_lock:
            if self._bus is None:
                return False
            try:
                msg = can.Message(arbitration_id=can_id, data=data,
                                  is_extended_id=is_extended_id)
                self._bus.send(msg)
                return True
            except (can.CanError, OSError):
                return False

    @property
    def is_running(self):
        return self._thread is not None and self._thread.is_alive()

    @property
    def config(self):
        return self._config


# Module-level singleton used by the Dash callbacks
can_manager = CanManager()
