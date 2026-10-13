#-----------------------------------------------------------------------
# Titel		:	can_0x237.py
#-----------------------------------------------------------------------
# Sprache	:	Python
# Datum		:	06.07.2026
# Version	:	1.0
# Autor		:	Diveturtle93
# Projekt	:	EAuto_Dashboard
# Quelle	:
#-----------------------------------------------------------------------

# Beschreibung
#-----------------------------------------------------------------------
# Decoder fuer CAN 0x237: Zustaende der BMS GPIO-Ausgaenge
#-----------------------------------------------------------------------

# Einfuegen der standard Module
#-----------------------------------------------------------------------

#-----------------------------------------------------------------------

# Einfuegen der externen Module
#-----------------------------------------------------------------------

#-----------------------------------------------------------------------

# Einfuegen der eigenen Module
#-----------------------------------------------------------------------

#-----------------------------------------------------------------------

# Definiere Debug-Symbole
#-----------------------------------------------------------------------
DEBUG_CAN_0X237									= False
#-----------------------------------------------------------------------

# Version definieren
#-----------------------------------------------------------------------
CAN_0X237_MAJOR									= 1
CAN_0X237_MINOR									= 0
CAN_0X237_PATCH									= 0
CAN_0X237_DEV									= 0
#-----------------------------------------------------------------------

# Konstanten definieren
#-----------------------------------------------------------------------
# Byte 0: systemoutput
_SYSTEM_BITS									= [
	"sys_ams_limit",														# 0 BMS Error
	"sys_imd_ok",															# 1 IMD Error
	"sys_ams_ok",															# 2 AMS-OK
	"sys_freigabe",															# 3 Freigabe RUN, Bamocar
	"sys_recuperation",														# 4 Recuperation moeglich
	"sys_hv_p",																# 5 HV-Relais, Positiv
	"sys_hv_n",																# 6 HV-Relais, Negativ
	"sys_power_on",															# 7 Signal, Power ON
]

# Byte 1: highcurrent_out
_HIGHCURRENT_BITS								= [
	"hc_digital1",															# 0 Digitaler Ausgang
	"hc_digital2",															# 1 Digitaler Ausgang
	"hc_precharge_out",														# 2 Precharge Relais
	"hc_hv_m",																# 3 HV-Relais, Zusaetzlich
	"hc_hv_chg",															# 4 HV-Relais, Ladegeraet
	None,																	# 5 Reserviert
	"hc_heater1",															# 6 Heizung
	"hc_heater2",															# 7 Heizung
]

# Byte 2: ledoutput
_LED_BITS										= [
	"led_inlet_red",														# 0 Rote LED, Inlet
	"led_inlet_green",														# 1 Gruene LED, Inlet
	"led_akku_error",														# 2 Akku Error
	None,																	# 3 Reserviert
	None,																	# 4 Reserviert
	"led_red",																# 5 Rote LED, PCB
	"led_green",															# 6 Gruene LED, PCB
	"led_blue",																# 7 Blaue LED, PCB
]

# Byte 3: komfortoutput
_KOMFORT_BITS									= [
	"komfort_trigger_out",													# 0 Trigger Stromsensor, CAN Nachrichten
	"komfort_isospi_en",													# 1 IsoSPI Spannung einschalten
	"komfort_isohv_en",														# 2 Precharge Abfrage einschalten
	None, None, None, None, None,											# 3-7 Reserviert
]
#-----------------------------------------------------------------------

# Variablen definieren
#-----------------------------------------------------------------------

#-----------------------------------------------------------------------

# Bits eines Bytes auf die zugehoerigen Namen aufteilen, None wird uebersprungen
#-----------------------------------------------------------------------
def _unpack (byte, names):
	return {name: (byte >> i) & 0x01 for i, name in enumerate(names) if name is not None}
#-----------------------------------------------------------------------

# CAN 0x237 dekodieren
# Byte 0: systemoutput, Byte 1: highcurrent_out, Byte 2: ledoutput,
# Byte 3: komfortoutput, Byte 4: Rolling Counter
# Rueckgabe: {Key: 0|1} plus "gpio_counter" oder None, wenn data zu kurz ist
#-----------------------------------------------------------------------
def decode0x237 (data: bytes) -> dict:
	if len(data) < 5:
		return None

	out = {}
	out.update(_unpack(data[0], _SYSTEM_BITS))
	out.update(_unpack(data[1], _HIGHCURRENT_BITS))
	out.update(_unpack(data[2], _LED_BITS))
	out.update(_unpack(data[3], _KOMFORT_BITS))
	out["gpio_counter"] = data[4]

	return out
#-----------------------------------------------------------------------
