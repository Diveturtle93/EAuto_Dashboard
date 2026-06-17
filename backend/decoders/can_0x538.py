def decode_0x538(data):
    """Decode CAN 0x538: 4 × 12-bit ADC temperature sensor values (Big-Endian).

    Packing (6 bytes used, bytes 6-7 are always 0):
      Byte 0      : T1[11:4]
      Byte 1 hi   : T1[3:0]
      Byte 1 lo   : T2[11:8]
      Byte 2      : T2[7:0]
      Byte 3      : T3[11:4]
      Byte 4 hi   : T3[3:0]
      Byte 4 lo   : T4[11:8]
      Byte 5      : T4[7:0]

    Returns dict {key: int} or None if data is too short.
    """
    if len(data) < 6:
        return None

    t1 = (data[0] << 4) | (data[1] >> 4)
    t2 = ((data[1] & 0x0F) << 8) | data[2]
    t3 = (data[3] << 4) | (data[4] >> 4)
    t4 = ((data[4] & 0x0F) << 8) | data[5]

    return {
        "temp_adc_1": t1,
        "temp_adc_2": t2,
        "temp_adc_3": t3,
        "temp_adc_4": t4,
    }
