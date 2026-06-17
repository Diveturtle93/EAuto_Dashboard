def decode_0x538(data):
    """Decode CAN 0x538: 4 × 12-bit ADC temperature sensor values (Little-Endian).

    Sender packs two 12-bit values into 3 bytes, LSB first:
      Byte 0      : ADC[4][7:0]
      Byte 1[3:0] : ADC[4][11:8]
      Byte 1[7:4] : ADC[5][3:0]
      Byte 2      : ADC[5][11:4]
      Byte 3      : ADC[6][7:0]
      Byte 4[3:0] : ADC[6][11:8]
      Byte 4[7:4] : ADC[7][3:0]
      Byte 5      : ADC[7][11:4]

    Returns dict {key: int} or None if data is too short.
    """
    if len(data) < 6:
        return None

    t1 = data[0] | ((data[1] & 0x0F) << 8)
    t2 = (data[1] >> 4) | (data[2] << 4)
    t3 = data[3] | ((data[4] & 0x0F) << 8)
    t4 = (data[4] >> 4) | (data[5] << 4)

    return {
        "temp_adc_1": t1,
        "temp_adc_2": t2,
        "temp_adc_3": t3,
        "temp_adc_4": t4,
    }
