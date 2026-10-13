#-----------------------------------------------------------------------
# Titel		:	cell_temperatures.py
#-----------------------------------------------------------------------
# Sprache	:	Python
# Datum		:	29.06.2026
# Version	:	1.0
# Autor		:	Diveturtle93
# Projekt	:	EAuto_Dashboard
# Quelle	:
#-----------------------------------------------------------------------

# Einfuegen der standard Module
#-----------------------------------------------------------------------
import struct
#-----------------------------------------------------------------------

# Einfuegen der externen Module
#-----------------------------------------------------------------------

#-----------------------------------------------------------------------

# Einfuegen der eigenen Module
#-----------------------------------------------------------------------

#-----------------------------------------------------------------------

# Definiere Debug-Symbole
#-----------------------------------------------------------------------
DEBUG_CELL_TEMPERATURES							= False
#-----------------------------------------------------------------------

# Version definieren
#-----------------------------------------------------------------------
CELL_TEMPERATURES_MAJOR							= 1
CELL_TEMPERATURES_MINOR							= 0
CELL_TEMPERATURES_PATCH							= 0
CELL_TEMPERATURES_DEV							= 0
#-----------------------------------------------------------------------

# Konstanten definieren
#-----------------------------------------------------------------------
_NUM_MODULES									= 10						# Anzahl Module
_SENSORS_PER_MSG								= 4							# 8 Byte / 2 Byte pro Sensor
_MSGS_PER_MOD									= 4							# 4 x 4 Sensoren = 16 Sensoren pro Modul
BASE_ID											= 0x780						# CAN-ID der ersten Nachricht
#-----------------------------------------------------------------------

# Variablen definieren
#-----------------------------------------------------------------------

#-----------------------------------------------------------------------

# Decoder fuer alle 40 Zelltemperatur-Nachrichten (0x780 - 0x7A7) erzeugen
# Rueckgabe: {canId: Decoder}
#-----------------------------------------------------------------------
def buildTempDecoders () -> dict:
	decoders = {}
	for m in range(_NUM_MODULES):
		for msgIdx in range(_MSGS_PER_MOD):
			canId = BASE_ID + m * _MSGS_PER_MOD + msgIdx
			sensorBase = msgIdx * _SENSORS_PER_MSG

			# Decoder mit fest gebundenem Modul und Sensor-Offset erzeugen
			def _make (module=m, sb=sensorBase):
				# 4 Sensorwerte (16 Bit, Big Endian) aus der Nachricht lesen
				def _decode (data: bytes) -> dict:
					out = {}
					for i in range(_SENSORS_PER_MSG):
						raw = struct.unpack_from(">H", data, i * 2)[0]
						out[f"cell_t_m{module}_s{sb + i}"] = raw
					return out

				return _decode

			decoders[canId] = _make()

	return decoders
#-----------------------------------------------------------------------
