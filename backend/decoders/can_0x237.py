"""Decoder for CAN 0x237: BMS GPIO output states."""

_SYSTEM_BITS = [
    "sys_ams_limit",        # 0 - BMS Error
    "sys_imd_ok",           # 1 - IMD Error
    "sys_ams_ok",           # 2 - AMS-OK
    "sys_freigabe",         # 3 - Freigabe RUN, Bamocar
    "sys_recuperation",     # 4 - Recuperation moeglich
    "sys_hv_p",             # 5 - HV-Relais, Positiv
    "sys_hv_n",             # 6 - HV-Relais, Negativ
    "sys_power_on",         # 7 - Signal, Power ON
]

_HIGHCURRENT_BITS = [
    "hc_digital1",          # 0 - Digitaler Ausgang
    "hc_digital2",          # 1 - Digitaler Ausgang
    "hc_precharge_out",     # 2 - Precharge Relais
    "hc_hv_m",              # 3 - HV-Relais, Zusaetzlich
    "hc_hv_chg",            # 4 - HV-Relais, Ladegeraet
    None,                   # 5 - reserved
    "hc_heater1",           # 6 - Heizung
    "hc_heater2",           # 7 - Heizung
]

_LED_BITS = [
    "led_inlet_red",        # 0 - Rote LED, Inlet
    "led_inlet_green",      # 1 - Gruene LED, Inlet
    "led_akku_error",       # 2 - Akku Error
    None,                   # 3 - reserved
    None,                   # 4 - reserved
    "led_red",              # 5 - Rote LED, PCB
    "led_green",            # 6 - Gruene LED, PCB
    "led_blue",             # 7 - Blaue LED, PCB
]

_KOMFORT_BITS = [
    "komfort_trigger_out",  # 0 - Trigger Stromsensor, CAN Nachrichten
    "komfort_isospi_en",    # 1 - IsoSPI Spannung einschalten
    "komfort_isohv_en",     # 2 - Precharge abfrage einschalten
    None, None, None, None, None,  # 3-7 reserved
]


def _unpack(byte, names):
    return {name: (byte >> i) & 0x01 for i, name in enumerate(names) if name is not None}


def decode_0x237(data: bytes) -> dict:
    """Decode CAN 0x237: BMS GPIO output states.

    Byte 0: systemoutput, Byte 1: highcurrent_out, Byte 2: ledoutput,
    Byte 3: komfortoutput, Byte 5: rolling counter.

    Returns dict {key: 0|1} (plus "gpio_counter") or None if data is too short.
    """
    if len(data) < 6:
        return None

    out = {}
    out.update(_unpack(data[0], _SYSTEM_BITS))
    out.update(_unpack(data[1], _HIGHCURRENT_BITS))
    out.update(_unpack(data[2], _LED_BITS))
    out.update(_unpack(data[3], _KOMFORT_BITS))
    out["gpio_counter"] = data[5]

    return out
