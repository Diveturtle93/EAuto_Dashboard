#-----------------------------------------------------------------------
# Titel		:	can_bus.py
#-----------------------------------------------------------------------
# Sprache	:	Python
# Datum		:	16.06.2026
# Version	:	1.0
# Autor		:	Diveturtle93
# Projekt	:	EAuto_Dashboard
# Quelle	:
#-----------------------------------------------------------------------

# Einfuegen der standard Module
#-----------------------------------------------------------------------
import threading
import time
#-----------------------------------------------------------------------

# Einfuegen der externen Module
#-----------------------------------------------------------------------
import can																	# python-can: plattformuebergreifende CAN-Bibliothek
#-----------------------------------------------------------------------

# Einfuegen der eigenen Module
#-----------------------------------------------------------------------
from backend.decoders import decodeCanMessage, decodeCanMulti
#-----------------------------------------------------------------------

# Definiere Debug-Symbole
#-----------------------------------------------------------------------
DEBUG_CAN_BUS									= False
#-----------------------------------------------------------------------

# Version definieren
#-----------------------------------------------------------------------
CAN_BUS_MAJOR									= 1
CAN_BUS_MINOR									= 0
CAN_BUS_PATCH									= 0
CAN_BUS_DEV										= 0
#-----------------------------------------------------------------------

# Konstanten definieren
#-----------------------------------------------------------------------
_BACKOFF_MAX									= 30.0						# Maximale Wartezeit zwischen Reconnects in s
#-----------------------------------------------------------------------

# Konfiguration des CAN-Adapters
#-----------------------------------------------------------------------
class CanConfig:
	# Objekt initialisieren
	def __init__ (self, interface, channel, bitrate, reconnectDelay=3.0, timeout=0.5):
		self.interface = interface											# python-can Interface, z. B. "pcan"
		self.channel = channel												# Kanal, z. B. "PCAN_USBBUS1"
		self.bitrate = bitrate												# Bitrate in bit/s
		self.reconnectDelay = reconnectDelay								# Erste Wartezeit vor Reconnect in s
		self.timeout = timeout												# Timeout fuer bus.recv() in s
#-----------------------------------------------------------------------

# Verwaltet den CAN-Empfangsthread (Start / Stop zur Laufzeit)
#-----------------------------------------------------------------------
class CanManager:
	# Objekt initialisieren
	def __init__ (self):
		self._thread = None
		self._stopEvent = None
		self._config = None
		self._lock = threading.Lock()
		self._bus = None
		self._busLock = threading.Lock()

	# Referenz auf den geoeffneten Bus setzen
	def _setBus (self, bus):
		with self._busLock:
			self._bus = bus

	# Referenz auf den Bus freigeben
	def _clearBus (self):
		with self._busLock:
			self._bus = None

	# Empfangsthread mit neuer Konfiguration starten, laufender Thread wird vorher beendet
	def start (self, config, latest, lock):
		with self._lock:
			self._stopInternal()
			self._stopEvent = threading.Event()
			self._config = config
			self._thread = threading.Thread(
				target=canRxThread,
				args=(config, latest, lock, self._stopEvent, self._setBus, self._clearBus),
				daemon=True,
			)
			self._thread.start()
		print(f"[CAN] Manager started: {config.interface}/{config.channel} @ {config.bitrate} bps")

	# Empfangsthread beenden
	def stop (self):
		with self._lock:
			self._stopInternal()
		print("[CAN] Manager stopped.")

	# Empfangsthread beenden, Aufrufer haelt self._lock
	def _stopInternal (self):
		if self._stopEvent:
			self._stopEvent.set()
		if self._thread and self._thread.is_alive():
			self._thread.join(timeout=5.0)
		self._thread = None
		self._stopEvent = None
		self._config = None

	# Einzelnen CAN-Frame ueber den bereits geoeffneten Empfangs-Bus senden
	def send (self, canId: int, data: bytes, isExtendedId: bool = False) -> bool:
		with self._busLock:
			if self._bus is None:
				return False

			try:
				msg = can.Message(arbitration_id=canId, data=data, is_extended_id=isExtendedId)
				self._bus.send(msg)
				return True
			except (can.CanError, OSError):
				return False

	# Empfangsthread laeuft
	@property
	def isRunning (self):
		return self._thread is not None and self._thread.is_alive()

	# Aktuelle Konfiguration, None wenn gestoppt
	@property
	def config (self):
		return self._config
#-----------------------------------------------------------------------

# Variablen definieren
#-----------------------------------------------------------------------
CAN_Manager = CanManager()													# Globale Instanz fuer die Dash-Callbacks
#-----------------------------------------------------------------------

# CAN-Bus ueber python-can oeffnen und Nachrichten dauerhaft empfangen
# Bei Fehlern automatischer Reconnect mit exponentiellem Backoff (max. _BACKOFF_MAX s).
# Bekannte CAN-IDs werden ueber die Decoder-Registry in latest geschrieben.
# Beendet sich, sobald stopEvent gesetzt ist.
#-----------------------------------------------------------------------
def canRxThread (config, latest=None, lock=None, stopEvent=None, setBus=None, clearBus=None):
	backoff = config.reconnectDelay

	while True:
		# Beenden angefordert
		if stopEvent and stopEvent.is_set():
			print("[CAN] Thread stopped.")
			return

		# Bus oeffnen
		try:
			bus = can.Bus(interface=config.interface, channel=config.channel, bitrate=config.bitrate)
			print(f"[CAN] Connected: interface={config.interface}, channel={config.channel}, bitrate={config.bitrate}")
			backoff = config.reconnectDelay									# Nach erfolgreichem Verbinden zuruecksetzen
			if setBus:
				setBus(bus)
			if latest is not None and lock is not None:
				with lock:
					latest["can_adapter_connected"] = True
		# Bus konnte nicht geoeffnet werden, nach Wartezeit erneut versuchen
		except (can.CanError, OSError, ValueError) as e:
			print(f"[CAN] Cannot open {config.interface}/{config.channel}: {e}  -- retrying in {backoff:.0f} s")
			if latest is not None and lock is not None:
				with lock:
					latest["can_adapter_connected"] = False
			deadline = time.time() + backoff
			while time.time() < deadline:
				if stopEvent and stopEvent.is_set():
					return
				time.sleep(0.1)
			backoff = min(backoff * 2, _BACKOFF_MAX)
			continue

		# Empfangsschleife
		while True:
			# Beenden angefordert, Bus schliessen
			if stopEvent and stopEvent.is_set():
				if clearBus:
					clearBus()
				try:
					bus.shutdown()
				except (can.CanError, OSError):
					pass
				if latest is not None and lock is not None:
					with lock:
						latest["can_adapter_connected"] = False
				print("[CAN] Thread stopped.")
				return

			# Nachricht empfangen, bei Busfehler neu verbinden
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

			canId = msg.arbitration_id
			rxTs = time.time()

			# Ausserhalb des Locks dekodieren, reine Funktionen ohne gemeinsamen Zustand
			try:
				decoded = decodeCanMessage(canId, msg.data)
				decodedMulti = decodeCanMulti(canId, msg.data)
			except Exception as exc:
				print(f"[CAN] Decoder error for ID 0x{canId:03X}: {exc}")
				decoded = None
				decodedMulti = None

			# Ergebnisse in latest uebernehmen
			if latest is not None and lock is not None:
				with lock:
					latest["last_rx_ms"] = int(rxTs * 1000)
					latest["_can_rx_ts"][canId] = rxTs
					if decoded is not None:
						status, state, statusKey, stateKey = decoded
						latest[statusKey] = status
						latest[stateKey] = state
					if decodedMulti is not None:
						latest.update(decodedMulti)

		# Bus-Fehler: Referenz freigeben, dann shutdown
		if clearBus:
			clearBus()
		try:
			bus.shutdown()
		except (can.CanError, OSError):
			pass

		# Wartezeit vor dem naechsten Verbindungsversuch
		deadline = time.time() + backoff
		while time.time() < deadline:
			if stopEvent and stopEvent.is_set():
				return
			time.sleep(0.1)
		backoff = min(backoff * 2, _BACKOFF_MAX)
#-----------------------------------------------------------------------
