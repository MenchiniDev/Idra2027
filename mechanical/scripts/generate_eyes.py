"""
Genera le versioni ingrandite dell'occhio animatronico (single eye V4, MorganManly)
per il carro "Idra di Guerra".

Principio:
  * tutto cio' che compone l'occhio (bulbo, snodo sferico, palpebre, montanti,
    torre dello snodo, piastra) viene scalato uniformemente di k = D / 35 mm
    attorno al centro dell'occhio (origine);
  * il VANO SERVO (cradle) resta in scala 1:1: viene ritagliato dalla BasePlate
    originale e trapiantato dietro la torre scalata, alla stessa quota rispetto
    al centro occhio, sopra un piedistallo che lo collega alla piastra scalata;
  * i servo restano MG90S/SG90 con le squadrette originali; per conservare gli
    angoli (e quindi la calibrazione) si montano sulle squadrette dei
    bracci di prolunga stampati con raggio scalato di k;
  * i tiranti delle palpebre vengono rigenerati: testa anteriore = testa
    originale scalata (innesto nella palpebra), corpo dritto, coda con
    3 fori di regolazione.

Coordinate (dal modello originale): origine = centro occhio, +Y = sguardo,
+Z = alto, piastra a Z = -32.25.

Uso:  python generate_eyes.py            -> genera D50, D70, D90 (singolo + coppia)
      python generate_eyes.py 60 80      -> diametri personalizzati
      python generate_eyes.py --double   -> solo la coppia di occhi
"""
import sys
from pathlib import Path

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[1] / "eyes"
SRC = ROOT / "original" / "single_v4"
SRC2 = ROOT / "original" / "double_compact"
EYE_PITCH = 65.8           # interasse occhi nella versione doppia (orig.)
OUT = ROOT / "scaled"

D0 = 35.0  # diametro bulbo originale [mm]

# --- quote ricavate dal modello originale (vedi docs/mechanical_eyes.md) ------
PLATE_TOP = -30.0          # faccia superiore piastra
PLATE_BOT = -32.25         # faccia inferiore piastra
TOWER_REAR_Y = -22.0       # faccia posteriore torre snodo
CRADLE_X = (-9.5, 21.5)    # estensione del vano servo
CRADLE_Y = (-62.0, -19.5)
CRADLE_TOP = -14.4         # sommita' pareti del vano servo
GAP = 2.0                  # luce tra torre scalata e vano servo

LID_PIN_UP = np.array([-1.25, 15.0])    # (y, z) foro tirante su palpebra sup.
LID_PIN_LO = np.array([-1.25, -15.0])   # (y, z) foro tirante su palpebra inf.
LINK_REAR = np.array([-56.3, 3.76])     # (y, z) perno posteriore tiranti (orig.)
LID_SERVO_AXIS = np.array([-53.0, -15.5])  # (y, z) asse servo palpebre (stima)
HORN_FACE_X = -15.0        # faccia esterna squadretta servo palpebre
LINK_UP_X = (-18.1, -15.3)  # spessore tirante superiore (orig.)
LINK_LO_X = (-20.13, -18.1)  # spessore tirante inferiore (orig.)
EYE_HORN_R = 16.0          # raggio max squadretta MG90S usato in origine (stima)

M2_TAP = 1.8               # foro per vite M2 autofilettante
M2_FREE = 2.4              # foro passante M2


def load(name, src=SRC):
    return trimesh.load(src / f"Animatronic Eyes - {name}.stl")


def mirror_x(m, xc):
    """Specchia una mesh rispetto al piano x = xc (mantiene le normali corrette)."""
    m = m.copy()
    T = np.eye(4)
    T[0, 0] = -1
    T[0, 3] = 2 * xc
    m.apply_transform(T)
    m.invert() if not m.is_winding_consistent or m.volume < 0 else None
    return m


def box(x, y, z):
    lo = np.array([x[0], y[0], z[0]])
    hi = np.array([x[1], y[1], z[1]])
    b = trimesh.creation.box(extents=hi - lo)
    b.apply_translation((lo + hi) / 2)
    return b


def cyl_x(r, x0, x1, y, z, sections=64):
    c = trimesh.creation.cylinder(radius=r, height=abs(x1 - x0), sections=sections)
    c.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0]))
    c.apply_translation([(x0 + x1) / 2, y, z])
    return c


def union(ms):
    return trimesh.boolean.union(ms, engine="manifold")


def diff(a, bs):
    return trimesh.boolean.difference([a] + list(bs), engine="manifold")


def inter(a, b):
    return trimesh.boolean.intersection([a, b], engine="manifold")


def scaled(m, k):
    m = m.copy()
    m.apply_scale(k)
    return m


def bar_yz(p0, p1, x0, x1, width):
    """Barra a sezione rettangolare con estremi arrotondati nel piano YZ."""
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    d = p1 - p0
    L = np.linalg.norm(d)
    ang = np.arctan2(d[1], d[0])
    t = abs(x1 - x0)
    b = trimesh.creation.box(extents=[t, L, width])
    b.apply_translation([0, L / 2, 0])
    b.apply_transform(trimesh.transformations.rotation_matrix(ang, [1, 0, 0]))
    b.apply_translation([(x0 + x1) / 2, p0[0], p0[1]])
    ends = [cyl_x(width / 2, x0, x1, *p) for p in (p0, p1)]
    return union([b] + ends)


# -----------------------------------------------------------------------------
def baseplate(k, base):
    dy = (TOWER_REAR_Y * k - GAP) - CRADLE_Y[1]   # traslazione del vano servo

    # 1) piastra + montanti + torre scalati, senza il vano servo scalato
    B = scaled(base, k)
    cut_z = (PLATE_TOP * k - 0.02, 50 * k)
    cuts = [
        box((CRADLE_X[0] * k, CRADLE_X[1] * k), (-62 * k, (TOWER_REAR_Y - 0.3) * k), cut_z),
        box((8.5 * k, CRADLE_X[1] * k), ((TOWER_REAR_Y - 0.3) * k, -19.0 * k), cut_z),
        box((CRADLE_X[0] * k, -5.6 * k), ((TOWER_REAR_Y - 0.3) * k, -19.0 * k), cut_z),
    ]
    B = diff(B, cuts)

    # 2) vano servo originale 1:1 (senza la parte alta della torre)
    cradle = inter(base, box(CRADLE_X, CRADLE_Y, (PLATE_BOT - 1, CRADLE_TOP)))
    cradle.apply_translation([0, dy, 0])

    # 3) piedistallo dal piano scalato al fondo del vano
    ped = box(CRADLE_X, (-60.8 + dy, CRADLE_Y[1] + dy),
              (PLATE_TOP * k - 0.5, PLATE_BOT + 0.5))
    return union([B, ped, cradle]), dy


def baseplate_double(k, base):
    """Versione doppia: due vani servo 1:1 (sx e dx speculare), vano centrale scalato."""
    dy = (TOWER_REAR_Y * k - GAP) - CRADLE_Y[1]
    xr = 19.0                       # limite interno vano sx (oltre c'e' il vano centrale)
    dx = EYE_PITCH * (k - 1)        # traslazione del vano dx
    B = scaled(base, k)
    cut_z = (PLATE_TOP * k - 0.02, 50 * k)
    P = EYE_PITCH * k
    left = [
        box((CRADLE_X[0] * k, xr * k), (-62 * k, (TOWER_REAR_Y - 0.3) * k), cut_z),
        box((8.5 * k, xr * k), ((TOWER_REAR_Y - 0.3) * k, -19.0 * k), cut_z),
        box((CRADLE_X[0] * k, -5.6 * k), ((TOWER_REAR_Y - 0.3) * k, -19.0 * k), cut_z),
    ]
    right = []
    for c in left:
        lo, hi = c.bounds
        right.append(box((P - hi[0], P - lo[0]), (lo[1], hi[1]), (lo[2], hi[2])))
    B = diff(B, left + right)

    zc = (PLATE_BOT - 1, CRADLE_TOP)
    cl = inter(base, box((CRADLE_X[0], xr), CRADLE_Y, zc))
    cl.apply_translation([0, dy, 0])
    cr = inter(base, box((EYE_PITCH - xr, EYE_PITCH - CRADLE_X[0]), CRADLE_Y, zc))
    cr.apply_translation([dx, dy, 0])
    pz = (PLATE_TOP * k - 0.5, PLATE_BOT + 0.5)
    pl = box((CRADLE_X[0], xr), (-60.8 + dy, CRADLE_Y[1] + dy), pz)
    pr = box((EYE_PITCH - xr + dx, EYE_PITCH - CRADLE_X[0] + dx), (-60.8 + dy, CRADLE_Y[1] + dy), pz)
    return union([B, pl, pr, cl, cr]), dy


def lid_links(k, dy, link_up, link_lo):
    axis = LID_SERVO_AXIS + np.array([dy, 0])
    rear = axis + k * (LINK_REAR - LID_SERVO_AXIS)   # perno su braccio scalato
    out = {}
    for name, link, pin, xr in (("Linkage_Upper", link_up, LID_PIN_UP, LINK_UP_X),
                                ("Linkage_Lower", link_lo, LID_PIN_LO, LINK_LO_X)):
        x0, x1 = xr[0] * k, xr[1] * k
        F = pin * k
        # testa anteriore originale scalata (innesto sulla palpebra)
        head = inter(scaled(link, k), cyl_x(4.0 * k, x0 - 1, x1 + 1, *F))
        w = max(5.0, 2.2 * k)
        body = bar_yz(F, rear, x0, x1, w)
        # tre fori di regolazione: nominale, +-3 mm lungo l'asse
        u = (rear - F) / np.linalg.norm(rear - F)
        ext = bar_yz(rear, rear + 3.5 * u, x0, x1, w)
        holes = [cyl_x(M2_FREE / 2, x0 - 1, x1 + 1, *(rear + s * u)) for s in (-3, 0, 3)]
        part = diff(union([head, body, ext]), holes)
        out[name] = part
        out[name + "_len"] = float(np.linalg.norm(rear - F))
    return out, axis


def lid_crank(k, axis):
    """Braccio di prolunga per il servo palpebre: si avvita sulla squadretta."""
    y, z = axis
    r_nom = k * np.linalg.norm(LINK_REAR - LID_SERVO_AXIS)
    arm_x1 = LINK_UP_X[1] * k + 0.3 + 3.0
    arm_x0 = LINK_UP_X[1] * k + 0.3
    hub = cyl_x(9.0, HORN_FACE_X - 3.0, HORN_FACE_X, y, z)
    parts = [hub]
    if arm_x1 < HORN_FACE_X - 3.0:
        parts.append(cyl_x(7.0, arm_x1, HORN_FACE_X - 2.0, y, z))
    # braccio verticale (servo a 90 deg = braccio verso l'alto)
    parts.append(bar_yz((y, z), (y, z + r_nom + 4.0), arm_x0, arm_x1, 9.0))
    m = union(parts)
    holes = [cyl_x(M2_TAP / 2, arm_x0 - 1, arm_x1 + 1, y, z + r_nom + s) for s in (-3, 0, 3)]
    holes.append(cyl_x(3.2, min(arm_x0, HORN_FACE_X - 3) - 1, HORN_FACE_X + 1, y, z))
    return diff(m, holes)


def horn_extender(k, wire):
    """Prolunga per squadrette dei servo occhio (sx/dx e su/giu). Stampa in piano."""
    r_max = k * EYE_HORN_R + 3.0
    hub = trimesh.creation.cylinder(radius=9.0, height=3.0, sections=64)
    arm = trimesh.creation.box(extents=[r_max, 9.0, 3.0])
    arm.apply_translation([r_max / 2, 0, 0])
    tip = trimesh.creation.cylinder(radius=4.5, height=3.0, sections=48)
    tip.apply_translation([r_max, 0, 0])
    m = union([hub, arm, tip])
    holes = [trimesh.creation.cylinder(radius=3.2, height=5, sections=48)]
    r = 8.0
    while r <= r_max + 0.01:
        h = trimesh.creation.cylinder(radius=(wire + 0.3) / 2, height=5, sections=24)
        h.apply_translation([r, 0, 0])
        holes.append(h)
        r += 2.5
    m = diff(m, holes)
    m.apply_translation([0, 0, 1.5])
    return m


def hardware(k):
    def pick(v, table):
        return min(table, key=lambda t: abs(t[0] - v))[1]
    return {
        "vite_snodo": pick(3.4 * k, [(3.4, "M3"), (4.5, "M4"), (5.5, "M5"), (6.6, "M6"), (8.6, "M8")]),
        "inserto_snodo_foro_mm": round(4.1 * k, 1),
        "fori_piastra_mm": round(3.5 * k, 1),
        "perno_palpebra_mm": round(4.0 * k, 1),
        "filo_occhio_mm": {50: 1.5, 70: 2.0, 90: 2.5}.get(round(D0 * k), round(1.0 * k * 0.9, 1)),
    }


def build(D):
    k = D / D0
    od = OUT / f"D{int(D)}"
    od.mkdir(parents=True, exist_ok=True)
    tag = f"D{int(D)}"
    base = load("BasePlate")
    hw = hardware(k)

    for n in ("Eyeball", "EyeBall Ball Joint", "Eyelid_Upper_L", "Eyelid_Lower_L"):
        m = scaled(load(n), k)
        m.export(od / f"{n.replace(' ', '_')}_{tag}.stl")

    bp, dy = baseplate(k, base)
    bp.export(od / f"BasePlate_{tag}.stl")

    links, axis = lid_links(k, dy, load("Linkage_Upper_L"), load("Linkage_Lower_L"))
    for n in ("Linkage_Upper", "Linkage_Lower"):
        links[n].export(od / f"{n}_{tag}.stl")
    lid_crank(k, axis).export(od / f"LidCrank_{tag}.stl")
    horn_extender(k, hw["filo_occhio_mm"]).export(od / f"HornExtender_{tag}.stl")

    info = {
        "diametro_mm": D, "k": round(k, 4), "spostamento_vano_servo_y_mm": round(dy, 2),
        "asse_servo_palpebre_yz": np.round(axis, 2).tolist(),
        "tirante_sup_mm": round(links["Linkage_Upper_len"], 1),
        "tirante_inf_mm": round(links["Linkage_Lower_len"], 1),
        "raggio_braccio_palpebre_mm": round(k * np.linalg.norm(LINK_REAR - LID_SERVO_AXIS), 1),
        **hw,
    }
    (od / "info.txt").write_text("\n".join(f"{a}: {b}" for a, b in info.items()), encoding="utf8")
    for f in sorted(od.glob("*.stl")):
        m = trimesh.load(f)
        print(f"  {f.name:40s} wt={m.is_watertight}  ext={np.round(m.extents, 1)}")
    print(info)


def build_double(D):
    """Coppia di occhi: file *_L (occhio sx) e *_R (occhio dx) + BasePlate doppia.
    Bulbo e snodo sono identici per i due occhi (stampare 2 pezzi)."""
    k = D / D0
    tag = f"D{int(D)}"
    od = OUT / "double" / tag
    od.mkdir(parents=True, exist_ok=True)
    xc = EYE_PITCH * k / 2
    hw = hardware(k)

    for n in ("Eyeball", "EyeBall Ball Joint"):
        scaled(load(n, SRC2), k).export(od / f"{n.replace(' ', '_')}_{tag}_x2.stl")
    for n in ("Eyelid_Upper_L", "Eyelid_Lower_L", "Eyelid_Upper_R", "Eyelid_Lower_R"):
        scaled(load(n, SRC2), k).export(od / f"{n}_{tag}.stl")

    bp, dy = baseplate_double(k, load("BasePlate", SRC2))
    bp.export(od / f"BasePlate_Double_{tag}.stl")

    links, axis = lid_links(k, dy, load("Linkage_Upper_L", SRC2), load("Linkage_Lower_L", SRC2))
    crank = lid_crank(k, axis)
    for n in ("Linkage_Upper", "Linkage_Lower"):
        links[n].export(od / f"{n}_L_{tag}.stl")
        mirror_x(links[n], xc).export(od / f"{n}_R_{tag}.stl")
    crank.export(od / f"LidCrank_L_{tag}.stl")
    mirror_x(crank, xc).export(od / f"LidCrank_R_{tag}.stl")
    horn_extender(k, hw["filo_occhio_mm"]).export(od / f"HornExtender_{tag}_x4.stl")

    info = {
        "diametro_mm": D, "k": round(k, 4), "interasse_occhi_mm": round(EYE_PITCH * k, 1),
        "spostamento_vani_servo_y_mm": round(dy, 2),
        "tirante_sup_mm": round(links["Linkage_Upper_len"], 1),
        "tirante_inf_mm": round(links["Linkage_Lower_len"], 1),
        "raggio_braccio_palpebre_mm": round(k * float(np.linalg.norm(LINK_REAR - LID_SERVO_AXIS)), 1),
        **hw,
    }
    (od / "info.txt").write_text("\n".join(f"{a}: {b}" for a, b in info.items()), encoding="utf8")
    for f in sorted(od.glob("*.stl")):
        m = trimesh.load(f)
        print(f"  {f.name:40s} wt={m.is_watertight} vol>0={m.volume > 0} ext={np.round(m.extents, 1)}")
    print(info)


if __name__ == "__main__":
    args = sys.argv[1:]
    only_double = "--double" in args
    sizes = [float(a) for a in args if not a.startswith("--")] or [50, 70, 90]
    for D in sizes:
        if not only_double:
            print(f"== single D{int(D)}")
            build(D)
        print(f"== double D{int(D)}")
        build_double(D)
