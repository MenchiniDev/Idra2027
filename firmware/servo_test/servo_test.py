#!/usr/bin/env python3
"""
Collaudo servo (MG995 / MG90S) su Raspberry Pi — Idra di Guerra.

Collegamenti (Pi 5 / Pi 4, Raspberry Pi OS Bookworm):
  filo arancione/giallo (segnale) -> GPIO13 (pin fisico 33)
  filo marrone/nero  (GND)        -> GND alimentatore servo E un GND del Pi (es. pin 6)
  filo rosso         (V+)         -> + alimentatore esterno 5-6 V, almeno 3 A
  NON alimentare un MG995 dal pin 5V del Pi: allo spunto assorbe 1-2.5 A e il Pi si riavvia.

Uso:
  python3 servo_test.py              # test automatico completo
  python3 servo_test.py --pin 12     # altro GPIO
  python3 servo_test.py --manual     # comandi a mano (angolo da tastiera)
  python3 servo_test.py --min-us 500 --max-us 2500   # estremi impulso (default 1000-2000, sicuri)

Dipendenze (gia' presenti in Raspberry Pi OS Bookworm): python3-gpiozero, python3-lgpio
  sudo apt install -y python3-gpiozero python3-lgpio
"""
import argparse
import sys
import time

try:
    from gpiozero import Servo
    from gpiozero.pins.lgpio import LGPIOFactory
except ImportError:
    sys.exit("Manca gpiozero/lgpio: sudo apt install -y python3-gpiozero python3-lgpio")


def ask(msg):
    """Domanda si/no all'operatore: restituisce True/False."""
    while True:
        r = input(f"  {msg} [s/n] ").strip().lower()
        if r in ("s", "si", "y", "yes"):
            return True
        if r in ("n", "no"):
            return False


class Tester:
    def __init__(self, pin, min_us, max_us):
        self.min_us, self.max_us = min_us, max_us
        self.servo = Servo(pin, min_pulse_width=min_us / 1e6, max_pulse_width=max_us / 1e6,
                           frame_width=0.02, pin_factory=LGPIOFactory())

    def us(self, pulse_us):
        """Porta il servo all'impulso indicato (microsecondi)."""
        pulse_us = max(self.min_us, min(self.max_us, pulse_us))
        mid, half = (self.min_us + self.max_us) / 2, (self.max_us - self.min_us) / 2
        self.servo.value = (pulse_us - mid) / half

    def angle(self, deg):
        """0..180 gradi mappati sull'intervallo min_us..max_us."""
        self.us(self.min_us + (self.max_us - self.min_us) * deg / 180.0)

    def sweep(self, a0, a1, seconds):
        steps = max(1, int(seconds / 0.02))
        for i in range(steps + 1):
            self.angle(a0 + (a1 - a0) * i / steps)
            time.sleep(0.02)

    def off(self):
        self.servo.detach()

    def close(self):
        self.off()
        self.servo.close()


def auto_test(t):
    results = {}
    print("\n== 1. Centro (90 deg) ==")
    t.angle(90)
    time.sleep(1.5)
    results["centro"] = ask("Il servo si e' mosso e ora sta fermo al centro, senza ronzare forte?")

    print("\n== 2. Estremi 0 / 180 deg ==")
    for a in (0, 180, 90):
        print(f"  -> {a} deg")
        t.angle(a)
        time.sleep(1.5)
    results["estremi"] = ask("Ha raggiunto entrambi gli estremi senza scatti, salti o rumore di ingranaggi?")

    print("\n== 3. Sweep lento avanti/indietro (x3) ==")
    for _ in range(3):
        t.sweep(10, 170, 3.0)
        t.sweep(170, 10, 3.0)
    t.angle(90)
    results["sweep"] = ask("Il movimento e' stato fluido e continuo (niente punti duri o zone morte)?")

    print("\n== 4. Passi piccoli (precisione) ==")
    for a in (90, 95, 100, 95, 90, 85, 80, 85, 90):
        t.angle(a)
        time.sleep(0.6)
    results["passi"] = ask("Ha seguito anche i passi da 5 deg?")

    print("\n== 5. Tenuta sotto sforzo ==")
    t.angle(90)
    print("  Ora prova a ruotare A MANO la squadretta (con delicatezza) per ~5 secondi.")
    time.sleep(6)
    results["tenuta"] = ask("Ha opposto resistenza e poi e' tornato al centro?")

    print("\n== 6. Stabilita' da fermo (10 s) ==")
    t.angle(90)
    time.sleep(10)
    results["fermo"] = ask("E' rimasto fermo senza tremare? (un leggero ronzio e' normale)")

    t.off()
    print("\n== 7. Temperatura ==")
    results["temperatura"] = ask("Toccando il corpo del servo: e' solo tiepido (non caldo)?")

    print("\n================ ESITO ================")
    for k, v in results.items():
        print(f"  {k:12s} {'OK' if v else 'KO'}")
    ok = all(results.values())
    print(f"\n  SERVO {'BUONO' if ok else 'DA SCARTARE / VERIFICARE'}")
    return ok


def manual(t):
    print("Comandi: numero 0-180 = angolo | uNNNN = impulso in us (es. u1500) | "
          "s = sweep | o = stacca | q = esci")
    while True:
        c = input("> ").strip().lower()
        if c in ("q", "quit", "exit"):
            return
        if c == "s":
            t.sweep(0, 180, 2.0)
            t.sweep(180, 0, 2.0)
        elif c == "o":
            t.off()
        elif c.startswith("u") and c[1:].isdigit():
            t.us(int(c[1:]))
        else:
            try:
                t.angle(float(c))
            except ValueError:
                print("?")


def main():
    p = argparse.ArgumentParser(description="Collaudo servo su Raspberry Pi")
    p.add_argument("--pin", type=int, default=13, help="GPIO BCM del segnale (default 13)")
    p.add_argument("--min-us", type=int, default=1000, help="impulso a 0 deg (default 1000)")
    p.add_argument("--max-us", type=int, default=2000, help="impulso a 180 deg (default 2000)")
    p.add_argument("--manual", action="store_true", help="modalita' manuale")
    a = p.parse_args()

    print(f"Servo su GPIO{a.pin}, impulso {a.min_us}-{a.max_us} us. Ctrl+C per fermare.")
    print("Controlla: alimentazione ESTERNA 5-6 V accesa e GND in comune col Pi.")
    input("Invio per iniziare...")
    t = Tester(a.pin, a.min_us, a.max_us)
    try:
        if a.manual:
            manual(t)
            ok = True
        else:
            ok = auto_test(t)
    except KeyboardInterrupt:
        print("\nInterrotto.")
        ok = False
    finally:
        t.close()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
