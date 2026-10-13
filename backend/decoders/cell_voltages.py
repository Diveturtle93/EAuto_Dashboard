#-----------------------------------------------------------------------
# Titel		:	cell_voltages.py
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
DEBUG_CELL_VOLTAGES								= False
#-----------------------------------------------------------------------

# Version definieren
#-----------------------------------------------------------------------
CELL_VOLTAGES_MAJOR								= 1
CELL_VOLTAGES_MINOR								= 0
CELL_VOLTAGES_PATCH								= 0
CELL_VOLTAGES_DEV								= 0
#-----------------------------------------------------------------------

# Konstanten definieren
#-----------------------------------------------------------------------
_NUM_MODULES									= 10						# Anzahl Module
_CELLS_PER_MSG									= 4							# 8 Byte / 2 Byte pro Zelle
_MSGS_PER_MOD									= 3							# 3 x 4 Zellen = 12 Zellen pro Modul
BASE_ID											= 0x680						# CAN-ID der ersten Nachricht
#-----------------------------------------------------------------------

# Variablen definieren
#-----------------------------------------------------------------------

#-----------------------------------------------------------------------

# Decoder fuer alle 30 Zellspannungs-Nachrichten (0x680 - 0x69D) erzeugen
# Rueckgabe: {canId: Decoder}
#-----------------------------------------------------------------------
def buildVoltageDecoders () -> dict:
	decoders = {}
	for m in range(_NUM_MODULES):
		for msgIdx in range(_MSGS_PER_MOD):
			canId = BASE_ID + m * _MSGS_PER_MOD + msgIdx
			cellBase = msgIdx * _CELLS_PER_MSG

			# Decoder mit fest gebundenem Modul und Zellen-Offset erzeugen
			def _make (module=m, cb=cellBase):
				# 4 Zellspannungen (16 Bit, Big Endian) aus der Nachricht lesen
				def _decode (data: bytes) -> dict:
					out = {}
					for i in range(_CELLS_PER_MSG):
						raw = struct.unpack_from(">H", data, i * 2)[0]
						out[f"cell_v_m{module}_c{cb + i}"] = raw
					return out

				return _decode

			decoders[canId] = _make()

	return decoders
#-----------------------------------------------------------------------
