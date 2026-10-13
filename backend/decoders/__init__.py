#-----------------------------------------------------------------------
# Titel		:	__init__.py
#-----------------------------------------------------------------------
# Sprache	:	Python
# Datum		:	16.06.2026
# Version	:	1.0
# Autor		:	Diveturtle93
# Projekt	:	EAuto_Dashboard
# Quelle	:
#-----------------------------------------------------------------------

# Beschreibung
#-----------------------------------------------------------------------
# Decoder-Registry: ordnet CAN-IDs ihren Decoder-Funktionen zu
#
# Einzelwert-Decoder, CAN-ID -> (Decoder, Status-Key, State-Key):
#   from .can_0x505 import decode0x505
#   DECODERS[0x505] = (decode0x505, "motor_status_code", "motor_state")
#
# Mehrwert-Decoder, CAN-ID -> Decoder, der {Key: Wert, ...} liefert:
#   from .can_0x538 import decode0x538
#   MULTI_DECODERS[0x538] = decode0x538
#-----------------------------------------------------------------------

# Einfuegen der standard Module
#-----------------------------------------------------------------------

#-----------------------------------------------------------------------

# Einfuegen der externen Module
#-----------------------------------------------------------------------

#-----------------------------------------------------------------------

# Einfuegen der eigenen Module
#-----------------------------------------------------------------------
from .can_0x237 import decode0x237
from .cell_temperatures import buildTempDecoders
from .cell_voltages import buildVoltageDecoders
#-----------------------------------------------------------------------

# Definiere Debug-Symbole
#-----------------------------------------------------------------------
DEBUG_DECODERS									= False
#-----------------------------------------------------------------------

# Version definieren
#-----------------------------------------------------------------------
DECODERS_MAJOR									= 1
DECODERS_MINOR									= 0
DECODERS_PATCH									= 0
DECODERS_DEV									= 0
#-----------------------------------------------------------------------

# Variablen definieren
#-----------------------------------------------------------------------
DECODERS										= {}						# Einzelwert-Decoder
MULTI_DECODERS									= {}						# Mehrwert-Decoder
MULTI_DECODERS.update(buildVoltageDecoders())								# 0x680 - 0x69D Zellspannungen
MULTI_DECODERS.update(buildTempDecoders())									# 0x780 - 0x7A7 Zelltemperaturen
MULTI_DECODERS[0x237] = decode0x237											# BMS GPIO-Zustaende
#-----------------------------------------------------------------------

# Einzelwert-Decoder ausfuehren
# Rueckgabe: (status, state, statusKey, stateKey) oder None bei unbekannter ID
#-----------------------------------------------------------------------
def decodeCanMessage (canId, data):
	entry = DECODERS.get(canId)
	if entry is None:
		return None

	decoder, statusKey, stateKey = entry
	result = decoder(data)
	if result is None:
		return None

	status, state = result
	return status, state, statusKey, stateKey
#-----------------------------------------------------------------------

# Mehrwert-Decoder ausfuehren
# Rueckgabe: {Key: Wert, ...} oder None, wenn die ID nicht in MULTI_DECODERS steht
#-----------------------------------------------------------------------
def decodeCanMulti (canId, data):
	decoder = MULTI_DECODERS.get(canId)
	if decoder is None:
		return None

	return decoder(data)
#-----------------------------------------------------------------------
