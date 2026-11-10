"""
Supporto del servo della mandibola (DSservo DS3225 "25KG", corpo rosso) regolabile in altezza.

Due pezzi, uniti da 2 viti M4 (+ dado e rondella) che scorrono in un'asola:
  * JawMount_Culla : piastra con la finestra del servo (orecchie avvitate sulla piastra, albero
                     orizzontale, perpendicolare alla piastra) e braccio verso l'alto con l'asola.
  * JawMount_Testa : piatto da incollare a caldo sotto la base degli occhi (fori passanti: la colla
                     li attraversa e fa da rivetto) e codolo con 2 fori M4 che si appoggia al braccio.

H = distanza dal bordo superiore del servo ("bocca" della finestra) alla faccia superiore del piatto:
regolabile da H_MIN a H_MAX (85 mm a meta' corsa). Si trova la posizione sulla testa, si serrano le
viti, poi si incolla il piatto alla base.

Quote DS3225 dal datasheet Dsservo "DS3225(Red)": corpo 40 x 20 x 40.4, orecchie 54.5 da punta a
punta, fori 49.5 x 10, faccia delle orecchie a 27.7 dal fondo. Diametro fori / spessore orecchie non
in tabella: fori pilota 2.6 per autofilettanti M3 (o M3 passanti allargando a 3.2).

Uso:  python generate_jaw_mount.py              (H 72..98)
      python generate_jaw_mount.py --hmin 60 --hmax 86
Uscita: mechanical/jaw/JawMount_Culla.stl, JawMount_Testa.stl (gia' nella posa di stampa).
"""
import argparse
from pathlib import Path

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "mechanical" / "jaw"

# DS3225
SERVO_L, SERVO_W = 40.0, 20.0
HOLE_DX, HOLE_DZ = 49.5, 10.0
GAP = 0.3                     # gioco per lato nella finestra
PILOT = 2.6                   # foro per autofilettante M3 nelle orecchie
M4 = 4.4                      # asola e fori M4

T = 6.0                       # spessore piastra/braccio/codolo
RIB = 8.0                     # profondita' delle costole (rigidezza contro i 25 kg cm)
RIB_T = 4.0
PLATE_W = 64.0                # larghezza piastra servo (orecchie 54.5)
ARM_W = 30.0
MARGIN = 8.0                  # piastra sotto la finestra
SCREW_PITCH = 20.0            # interasse dei 2 fori del codolo
A_TOP = 33.0                  # dal fondo del piatto al foro superiore del codolo
PAD = (64.0, 44.0, 5.0)       # piatto da incollare (x, y, z)


def box(lo, hi):
    lo, hi = np.asarray(lo, float), np.asarray(hi, float)
    b = trimesh.creation.box(extents=hi - lo)
    b.apply_translation((lo + hi) / 2)
    return b


def cyl_y(x, z, d, y0, y1):
    c = trimesh.creation.cylinder(radius=d / 2, height=y1 - y0, sections=40)
    c.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
    c.apply_translation([x, (y0 + y1) / 2, z])
    return c


def slot_y(x, z0, z1, d, y0, y1):
    return trimesh.boolean.union([cyl_y(x, z0, d, y0, y1), cyl_y(x, z1, d, y0, y1),
                                  box([x - d / 2, y0, z0], [x + d / 2, y1, z1])], engine="manifold")


def U(ms):
    return trimesh.boolean.union(ms, engine="manifold")


def D(a, bs):
    return trimesh.boolean.difference([a, *bs], engine="manifold")


def build(hmin, hmax):
    # sistema: z in su, piastra nel piano x-z, faccia anteriore (orecchie) a y = 0, costole verso +y
    win_z0 = MARGIN
    zm = win_z0 + SERVO_W + 2 * GAP              # "bocca": bordo superiore della finestra
    arm_top = zm + hmin - PAD[2] - 1.0           # sotto il piatto anche alla quota minima
    # fori del codolo rispetto a zm: superiore = H - PAD_z - A_TOP, inferiore = superiore - pitch
    s_hi = hmax - PAD[2] - A_TOP
    s_lo = hmin - PAD[2] - A_TOP - SCREW_PITCH
    if zm + s_hi > arm_top - 6:
        raise SystemExit("corsa troppo lunga per il braccio: allungare A_TOP o ridurre hmax")
    if s_lo < 6:
        raise SystemExit("asola troppo bassa: ridurre la corsa")

    plate_top = zm + 10.0
    culla = U([
        box([-PLATE_W / 2, 0, 0], [PLATE_W / 2, T, plate_top]),
        box([-ARM_W / 2, 0, 0], [ARM_W / 2, T, arm_top]),
        # costole laterali della piastra e del braccio (dietro, lato corpo del servo)
        box([-PLATE_W / 2, T, 0], [-PLATE_W / 2 + RIB_T, T + RIB, plate_top]),
        box([PLATE_W / 2 - RIB_T, T, 0], [PLATE_W / 2, T + RIB, plate_top]),
        box([-ARM_W / 2, T, zm], [-ARM_W / 2 + RIB_T, T + RIB, arm_top]),
        box([ARM_W / 2 - RIB_T, T, zm], [ARM_W / 2, T + RIB, arm_top]),
        box([-PLATE_W / 2, T, plate_top - RIB_T], [PLATE_W / 2, T + RIB, plate_top]),
    ])
    hz = win_z0 + GAP + SERVO_W / 2
    cuts = [box([-SERVO_L / 2 - GAP, -1, win_z0], [SERVO_L / 2 + GAP, T + RIB + 1, zm])]
    cuts += [cyl_y(sx * HOLE_DX / 2, hz + sz * HOLE_DZ / 2, PILOT, -1, T + 1)
             for sx in (-1, 1) for sz in (-1, 1)]
    cuts.append(slot_y(0, zm + s_lo, zm + s_hi, M4, -1, T + RIB + 1))
    culla = D(culla, cuts)

    # testa: piatto (faccia superiore a z = 0) + codolo davanti al braccio (y da -T a 0)
    px, py, pz = PAD
    tongue_len = A_TOP + SCREW_PITCH + 8.0
    testa = U([
        box([-px / 2, -T - py / 2 + T / 2, -pz], [px / 2, -T + py / 2 + T / 2, 0]),
        box([-ARM_W / 2, -T, -pz - tongue_len], [ARM_W / 2, 0, -pz]),
        # fazzoletti tra piatto e codolo (sul lato libero, y < -T)
        *[trimesh.convex.convex_hull(np.array(
            [[x, -T, -pz], [x + 4, -T, -pz], [x, -T - 14, -pz], [x + 4, -T - 14, -pz],
             [x, -T, -pz - 22], [x + 4, -T, -pz - 22]], float)) for x in (-ARM_W / 2, ARM_W / 2 - 4, -2)],
    ])
    tcuts = [cyl_y(0, -pz - A_TOP, M4, -T - 1, 1), cyl_y(0, -pz - A_TOP - SCREW_PITCH, M4, -T - 1, 1)]
    # fori per la colla a caldo nel piatto, lontani dal codolo
    for x in (-27, -20, 20, 27):
        for y in (-T - 12, -T + 12 + T):
            c = trimesh.creation.cylinder(radius=2.5, height=pz + 2, sections=24)
            c.apply_translation([x, y, -pz / 2])
            tcuts.append(c)
    testa = D(testa, tcuts)

    # pose di stampa: culla sulla faccia anteriore (y = 0 sul piatto, costole in su);
    # testa col piatto sul piano (faccia da incollare in giu': ruotata di 180 attorno a x)
    culla.apply_transform(trimesh.transformations.rotation_matrix(-np.pi / 2, [1, 0, 0]))
    testa.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0]))
    for m in (culla, testa):
        m.apply_translation(-m.bounds[0])
    return culla, testa, zm


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hmin", type=float, default=72.0)
    ap.add_argument("--hmax", type=float, default=98.0)
    a = ap.parse_args()
    culla, testa, zm = build(a.hmin, a.hmax)
    OUT.mkdir(parents=True, exist_ok=True)
    for n, m in (("JawMount_Culla", culla), ("JawMount_Testa", testa)):
        assert m.is_watertight, n
        m.export(OUT / f"{n}.stl")
        print(f"{n}: {m.extents.round(1)} mm, {m.volume / 1000:.1f} cm3")
    print(f"altezza bocca servo -> faccia superiore del piatto: {a.hmin:.0f} .. {a.hmax:.0f} mm")


if __name__ == "__main__":
    main()
