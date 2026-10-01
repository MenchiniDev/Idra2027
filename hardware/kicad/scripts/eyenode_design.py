"""
EyeNode — scheda di controllo per 1 coppia di occhi animatronici (6 servo).
Unica fonte di verita' per schema (gen_sch.py) e PCB (gen_pcb.py).

Architettura (vedi docs/electronics.md):
  * 12 V (batteria/alimentatore del carro) -> polyfuse -> diodo -> R-78E5.0 -> +5V logica
  * 5-6 V servo da DC-DC esterno dedicato  -> fusibile lama -> VSERVO -> 6 connettori servo
  * Arduino Nano: 6 PWM (D3 D5 D6 = occhio A, D9 D10 D11 = occhio B)
  * MAX485 per bus RS-485 tra le schede (sincronizzazione teste), terminazione a jumper
  * DIP switch 4 bit = indirizzo nodo; header ausiliario I2C/analogico; misura VSERVO su A7

Coordinate schema in mm (griglia 2.54), PCB in mm.
"""

PROJECT = "EyeNode"

# Ogni componente: ref, lib_id, value, footprint, pins {pin: net}, sch (x, y), pcb (x, y, rot, side)
# Le chiavi dei pin possono essere numeri ("1") o nomi ("D3"): vengono risolte dal generatore.
NC = None

SERVO_PINS = [("D3", "A_LR"), ("D5", "A_UD"), ("D6", "A_LID"),
              ("D9", "B_LR"), ("D10", "B_UD"), ("D11", "B_LID")]

R1206 = "Resistor_SMD:R_1206_3216Metric"
C1206 = "Capacitor_SMD:C_1206_3216Metric"
LED1206 = "LED_SMD:LED_1206_3216Metric"
HDR = "Connector_PinHeader_2.54mm:PinHeader_1x{n:02d}_P2.54mm_Vertical"
TB = "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-{n}-5.08_1x{n:02d}_P5.08mm_Horizontal"

parts = []


def part(ref, lib, value, fp, pins, sch, pcb, desc=""):
    parts.append(dict(ref=ref, lib=lib, value=value, fp=fp, pins=pins, sch=sch, pcb=pcb, desc=desc))


# ---------------------------------------------------------------- alimentazione logica
part("J1", "Connector_Generic:Conn_01x02", "12V IN logica", TB.format(n=2),
     {"1": "VIN_RAW", "2": "GND"}, (30.48, 45.72), (6.0, 12.0, 90, "F"))
part("F1", "Device:Polyfuse", "0.5A", "Fuse:Fuse_1812_4532Metric",
     {"1": "VIN_RAW", "2": "VIN_F"}, (50.8, 43.18, 90), (16.5, 9.5, 0, "F"))
part("D1", "Device:D_Schottky", "SS34", "Diode_SMD:D_SMA",
     {"1": "VLOGIC", "2": "VIN_F"}, (68.58, 43.18), (25.0, 9.5, 180, "F"))
part("C4", "Device:C", "10uF 50V", C1206, {"1": "VLOGIC", "2": "GND"}, (83.82, 50.8), (31.0, 14.0, 90, "F"))
part("U1", "Converter_DCDC:R-785.0-0.5", "R-78E5.0-0.5", "Converter_DCDC:Converter_DCDC_RECOM_R-78E-0.5_THT",
     {"1": "VLOGIC", "2": "GND", "3": "+5V"}, (101.6, 43.18), (36.0, 8.0, 0, "F"))
part("C5", "Device:C", "10uF 16V", C1206, {"1": "+5V", "2": "GND"}, (121.92, 50.8), (45.0, 14.0, 90, "F"))

# ---------------------------------------------------------------- alimentazione servo
part("J2", "Connector_Generic:Conn_01x02", "5-6V IN servo", TB.format(n=2),
     {"1": "VSERVO_IN", "2": "GND"}, (30.48, 96.52), (6.0, 52.0, 90, "F"))
part("F2", "Device:Fuse", "7.5A blade", "Fuse:Fuseholder_Blade_Mini_Keystone_3568",
     {"1": "VSERVO_IN", "2": "VSERVO"}, (50.8, 93.98, 90), (20.0, 62.0, 0, "F"))
part("D2", "Device:D_Schottky", "SS54 (crowbar inv. pol.)", "Diode_SMD:D_SMC",
     {"1": "VSERVO", "2": "GND"}, (68.58, 104.14), (24.0, 44.0, 90, "F"))
part("C1", "Device:C_Polarized", "1000uF 10V", "Capacitor_THT:CP_Radial_D10.0mm_P5.00mm",
     {"1": "VSERVO", "2": "GND"}, (83.82, 104.14), (36.0, 64.0, 0, "F"))
part("C2", "Device:C_Polarized", "1000uF 10V", "Capacitor_THT:CP_Radial_D10.0mm_P5.00mm",
     {"1": "VSERVO", "2": "GND"}, (99.06, 104.14), (52.0, 64.0, 0, "F"))
part("R10", "Device:R", "1k", R1206, {"1": "VSERVO", "2": "LED_PWR"}, (116.84, 99.06), (33.0, 48.0, 90, "F"))
part("D3", "Device:LED", "verde VSERVO", LED1206, {"1": "GND", "2": "LED_PWR"}, (116.84, 111.76), (33.0, 54.0, 90, "F"))
part("R11", "Device:R", "10k", R1206, {"1": "VSERVO", "2": "VSENSE"}, (134.62, 99.06), (63.0, 40.0, 90, "F"))
part("R12", "Device:R", "10k", R1206, {"1": "VSENSE", "2": "GND"}, (134.62, 111.76), (63.0, 47.0, 90, "F"))
part("C3", "Device:C", "100nF", C1206, {"1": "VSENSE", "2": "GND"}, (147.32, 111.76), (67.0, 47.0, 90, "F"))

# ---------------------------------------------------------------- MCU
nano = {"D3": "PWM_A_LR", "D5": "PWM_A_UD", "D6": "PWM_A_LID",
        "D9": "PWM_B_LR", "D10": "PWM_B_UD", "D11": "PWM_B_LID",
        "D4": "RS485_DE", "D7": "RS485_TX", "D8": "RS485_RX", "D12": "LED_STAT_D",
        "A0": "ADDR0", "A1": "ADDR1", "A2": "ADDR2", "A3": "ADDR3",
        "A4": "AUX_SDA", "A5": "AUX_SCL", "A6": "AUX_A6", "A7": "VSENSE",
        "+5V": "+5V", "4": "GND", "29": "GND",
        "D1/TX": NC, "D0/RX": NC, "D2": NC, "D13": NC, "3V3": NC, "AREF": NC,
        "3": NC, "28": NC, "VIN": NC}
part("A1", "MCU_Module:Arduino_Nano_v3.x", "Arduino Nano v3", "Module:Arduino_Nano",
     nano, (210.82, 83.82), (50.0, 30.0, 90, "F"))

# ---------------------------------------------------------------- uscite servo
for i, (pin, name) in enumerate(SERVO_PINS):
    y = 33.02 + i * 12.7
    part(f"R{i + 1}", "Device:R", "220", R1206, {"1": f"PWM_{name}", "2": f"SIG_{name}"},
         (279.4, y, 90), (76.0 + (i // 3) * 0.0, 9.0 + i * 8.0 + (i // 3) * 4.0, 0, "F"))
    part(f"J{i + 3}", "Connector_Generic:Conn_01x03", f"SERVO {name}", HDR.format(n=3),
         {"1": "GND", "2": "VSERVO", "3": f"SIG_{name}"},
         (320.04, y), (88.0, 6.5 + i * 8.0 + (i // 3) * 4.0, 90, "F"))

# ---------------------------------------------------------------- RS-485
part("U2", "Interface_UART:MAX485E", "MAX485E", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
     {"1": "RS485_RX", "2": "RS485_DE", "3": "RS485_DE", "4": "RS485_TX",
      "5": "GND", "6": "RS485_A", "7": "RS485_B", "8": "+5V"}, (210.82, 165.1), (40.0, 76.0, 0, "F"))
part("C6", "Device:C", "100nF", C1206, {"1": "+5V", "2": "GND"}, (233.68, 177.8), (47.0, 76.0, 90, "F"))
part("R7", "Device:R", "120", R1206, {"1": "RS485_A", "2": "TERM"}, (254.0, 160.02, 90), (54.0, 82.0, 0, "F"))
part("JP1", "Jumper:Jumper_2_Open", "TERM 120R", HDR.format(n=2),
     {"1": "TERM", "2": "RS485_B"}, (274.32, 160.02), (60.0, 82.0, 90, "F"))
part("J9", "Connector_Generic:Conn_01x03", "RS485 IN", TB.format(n=3),
     {"1": "RS485_A", "2": "RS485_B", "3": "GND"}, (320.04, 154.94), (68.0, 90.0, 180, "F"))
part("J10", "Connector_Generic:Conn_01x03", "RS485 OUT", TB.format(n=3),
     {"1": "RS485_A", "2": "RS485_B", "3": "GND"}, (320.04, 175.26), (88.0, 90.0, 180, "F"))

# ---------------------------------------------------------------- indirizzo / ausiliari
part("SW1", "Switch:SW_DIP_x04", "ADDR", "Button_Switch_THT:SW_DIP_SPSTx04_Slide_9.78x12.34mm_W7.62mm_P2.54mm",
     {"1": "ADDR0", "2": "ADDR1", "3": "ADDR2", "4": "ADDR3",
      "5": "GND", "6": "GND", "7": "GND", "8": "GND"}, (144.78, 170.18), (14.0, 80.0, 0, "F"))
part("J11", "Connector_Generic:Conn_01x05", "AUX I2C/A6", HDR.format(n=5),
     {"1": "+5V", "2": "AUX_SDA", "3": "AUX_SCL", "4": "AUX_A6", "5": "GND"},
     (144.78, 137.16), (26.0, 92.0, 90, "F"))
part("R13", "Device:R", "1k", R1206, {"1": "LED_STAT_D", "2": "LED_STAT"}, (266.7, 121.92, 90), (70.0, 30.0, 90, "F"))
part("D4", "Device:LED", "blu STATO", LED1206, {"1": "GND", "2": "LED_STAT"}, (287.02, 121.92, 90), (70.0, 36.0, 90, "F"))

# ---------------------------------------------------------------- PWR_FLAG e fori
FLAGS = [("#FLG01", "GND", (30.48, 124.46)), ("#FLG02", "VLOGIC", (83.82, 33.02)),
         ("#FLG03", "VSERVO", (68.58, 83.82)), ("#FLG04", "VSERVO_IN", (40.64, 83.82)),
         ("#FLG05", "VIN_RAW", (40.64, 33.02))]
NOTES = [("ALIMENTAZIONE LOGICA 12V -> 5V", 25.4, 25.4),
         ("ALIMENTAZIONE SERVO 5-6V (da DC-DC esterno)", 25.4, 78.74),
         ("MCU", 190.5, 25.4),
         ("USCITE SERVO  (A = occhio sx, B = occhio dx)", 264.16, 22.86),
         ("BUS RS-485 (sincronizzazione teste)", 190.5, 142.24),
         ("INDIRIZZO NODO / AUX", 129.54, 127.0)]
HOLES = [("H1", (3.5, 3.5)), ("H2", (96.5, 3.5)), ("H3", (3.5, 96.5)), ("H4", (96.5, 96.5))]
BOARD = (0.0, 0.0, 100.0, 100.0)   # x0, y0, x1, y1 [mm]

NETCLASS_POWER = ["GND", "VSERVO", "VSERVO_IN"]
