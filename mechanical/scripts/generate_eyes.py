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
      python generate_eyes.py --sync     -> solo i pezzi della coppia a 2 servo
                                            (cartella double_2servo, vedi build_double_sync)
      python generate_eyes.py --mg995    -> coppia a 2 servo con MG995
                                            (cartella double_2servo_mg995, vedi build_double_mg995)
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
M3_FREE = 3.4              # foro passante M3 (perni dei servo finti)

# --- servo finto MG90S (stima da disegni SG90/MG90S: VERIFICARE col calibro) --
# origine = asse dell'albero, z = 0 fondo del servo
DUMMY_L, DUMMY_W, DUMMY_H = 22.8, 12.2, 22.7   # corpo
DUMMY_SHAFT_END = 6.1      # distanza asse albero - estremita' del corpo
DUMMY_EAR_Z = (15.9, 18.4)  # orecchie di fissaggio (sotto, sopra)
DUMMY_EAR_SPAN = 32.5
DUMMY_EAR_HOLES = 27.8     # interasse fori orecchie
DUMMY_HORN_TOP = 31.0      # quota della faccia superiore della squadretta montata
DUMMY_CLEAR = 0.15         # gioco per lato rispetto al servo vero

# --- servo MG995 (formato standard; stima da datasheet: VERIFICARE col calibro) --
MG995_L, MG995_W = 40.7, 19.7   # corpo (lunghezza, larghezza)
MG995_TOP = 42.9           # fondo -> sommita' della cassa (senza squadretta)
MG995_HORN_TOP = 48.0      # fondo -> faccia superiore della squadretta montata
MG995_SHAFT_END = 10.0     # asse albero -> estremita' vicina del corpo
MG995_EAR_Z = (26.5, 29.0)  # orecchie: quota faccia inferiore / superiore dal fondo
MG995_HOLES = (49.5, 10.0)  # interasse fori orecchie (lungo il corpo, trasversale)
MG995_CLEAR = 0.4          # gioco per lato nella sede
EYE_LUG = np.array([14.5, -4.5])   # (x, y) foro verticale attacco filo laterale bulbo (orig.)
EYE_LUG_TOP_Z = 14.0       # quota attacco superiore del bulbo (orig.)


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


def baseplate_double(k, base, cradles=True):
    """Versione doppia: due vani servo 1:1 (sx e dx speculare), vano centrale scalato.
    cradles=False: piastra senza vani MG90S (per la variante MG995)."""
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
    if not cradles:
        return B, dy

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


def lid_crank(k, axis, bore=6.4):
    """Braccio di prolunga per il servo palpebre: si avvita sulla squadretta.
    bore = foro centrale (6.4 su squadretta vera, M3_FREE sul servo finto)."""
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
    holes.append(cyl_x(bore / 2, min(arm_x0, HORN_FACE_X - 3) - 1, HORN_FACE_X + 1, y, z))
    return diff(m, holes)


def horn_extender(k, wire, tie=False, bore=6.4):
    """Prolunga per squadrette dei servo occhio (sx/dx e su/giu). Stampa in piano.
    tie=True aggiunge un secondo braccio a 90 deg per il tirante di sincronismo
    (capovolgendo il pezzo il braccio passa dall'altro lato).
    bore = foro centrale: 6.4 su squadretta vera, M3_FREE su servo finto."""
    r_max = k * EYE_HORN_R + 3.0
    hub = trimesh.creation.cylinder(radius=9.0, height=3.0, sections=64)
    parts = [hub]
    holes = [trimesh.creation.cylinder(radius=bore / 2, height=5, sections=48)]
    for ang in ((0.0, np.pi / 2) if tie else (0.0,)):
        R = trimesh.transformations.rotation_matrix(ang, [0, 0, 1])
        arm = trimesh.creation.box(extents=[r_max, 9.0, 3.0])
        arm.apply_translation([r_max / 2, 0, 0])
        tip = trimesh.creation.cylinder(radius=4.5, height=3.0, sections=48)
        tip.apply_translation([r_max, 0, 0])
        for p in (arm, tip):
            p.apply_transform(R)
            parts.append(p)
        r = 8.0
        while r <= r_max + 0.01:
            h = trimesh.creation.cylinder(radius=(wire + 0.3) / 2, height=5, sections=24)
            h.apply_translation([r, 0, 0])
            h.apply_transform(R)
            holes.append(h)
            r += 2.5
    m = diff(union(parts), holes)
    m.apply_translation([0, 0, 1.5])
    return m


def dummy_servo():
    """Servo finto MG90S: va nella sede di un servo che non serve piu' e fa da
    supporto girevole (perno M3) per squadrette/manovelle trascinate.
    Stampa in piedi, cosi' com'e' (fondo sul piatto)."""
    c = DUMMY_CLEAR
    x0, x1 = -DUMMY_SHAFT_END, DUMMY_L - DUMMY_SHAFT_END
    xm = (x0 + x1) / 2
    w = DUMMY_W / 2 - c
    body = box((x0 + c, x1 - c), (-w, w), (0, DUMMY_H))
    ex = DUMMY_EAR_SPAN / 2 - c
    ears = box((xm - ex, xm + ex), (-w, w), DUMMY_EAR_Z)
    tower = trimesh.creation.cylinder(radius=w, height=4.0, sections=64)
    tower.apply_translation([0, 0, DUMMY_H + 2.0])
    boss_h = DUMMY_HORN_TOP - DUMMY_H - 4.0
    boss = trimesh.creation.cylinder(radius=4.5, height=boss_h, sections=64)
    boss.apply_translation([0, 0, DUMMY_H + 4.0 + boss_h / 2])
    m = union([body, ears, tower, boss])
    holes = [trimesh.creation.cylinder(radius=M3_FREE / 2, height=2 * DUMMY_HORN_TOP, sections=32),
             trimesh.creation.cylinder(radius=3.25, height=6.0, sections=6)]   # dado M3, prof. 3
    for sx in (-1, 1):
        h = trimesh.creation.cylinder(radius=1.1, height=10, sections=24)
        h.apply_translation([xm + sx * DUMMY_EAR_HOLES / 2, 0, sum(DUMMY_EAR_Z) / 2])
        holes.append(h)
    return diff(m, holes)


def lid_bail(k, axis, xc, offset_deg=10.0):
    """Barra a U che unisce rigidamente le manovelle palpebre sx e dx (coassiali):
    un solo servo muove le palpebre di entrambi gli occhi.
    Le alette si avvitano sul lato interno delle manovelle con le stesse viti M2
    dei tiranti (fori a r-3 / r / r+3: usarne due per un'unione rigida).
    La barra trasversale e' spostata di offset_deg verso il retro rispetto al
    braccio, cosi' non urta le torri degli snodi quando le palpebre si chiudono.
    Coordinate di montaggio, servo palpebre a 90 deg."""
    y, z = axis
    r = k * np.linalg.norm(LINK_REAR - LID_SERVO_AXIS)
    ax0 = LINK_UP_X[1] * k + 0.3 + 3.0        # faccia interna del braccio LidCrank sx
    t, w = 3.0, 9.0
    a = np.radians(offset_deg)
    pb = np.array([y, z]) + (r + 8.0) * np.array([-np.sin(a), np.cos(a)])   # asse barra
    strip = box((ax0, ax0 + t), (y - w / 2, y + w / 2), (z + r - 3 - 4.5, z + r + 3 + 4.5))
    tab = union([strip, bar_yz((y, z + r + 3), pb, ax0, ax0 + t, w)])
    bar = box((ax0, 2 * xc - ax0), (pb[0] - w / 2, pb[0] + w / 2), (pb[1] - 3, pb[1] + 3))
    m = union([tab, bar, mirror_x(tab, xc)])
    holes = []
    for xa in (ax0, 2 * xc - ax0 - t):
        holes += [cyl_x(M2_TAP / 2, xa - 1, xa + t + 1, y, z + r + s) for s in (-3, 0, 3)]
    return diff(m, holes)


def frame(origin, ex, ey):
    """Matrice 4x4 da sistema locale servo a mondo: ex = direzione del corpo
    (dall'albero verso l'estremita' lontana), ez = ex x ey = asse albero verso la squadretta."""
    ex, ey = np.asarray(ex, float), np.asarray(ey, float)
    T = np.eye(4)
    T[:3, 0], T[:3, 1], T[:3, 2], T[:3, 3] = ex, ey, np.cross(ex, ey), origin
    return T


def mg995_body(T, clear=MG995_CLEAR, extra=0.0):
    """Ingombro del corpo MG995 (locale: albero = asse z, z = 0 faccia squadretta).
    extra allunga il volume verso il fondo (per forare la piastra)."""
    c = clear
    b = box((-MG995_SHAFT_END - c, MG995_L - MG995_SHAFT_END + c),
            (-MG995_W / 2 - c, MG995_W / 2 + c),
            (-MG995_HORN_TOP - extra, MG995_TOP - MG995_HORN_TOP))
    b.apply_transform(T)
    return b


def mg995_mount(T, z_floor, margin=4.0, slab=4.0):
    """Sede MG995: piastrina sotto le orecchie (4 fori M3) + pareti fino alla piastra.
    Il corpo passa nella finestra e le orecchie appoggiano sulla piastrina."""
    xm = MG995_L / 2 - MG995_SHAFT_END
    ex = MG995_HOLES[0] / 2 + 4.0
    z1 = MG995_EAR_Z[0] - MG995_HORN_TOP
    s = box((xm - ex, xm + ex), (-MG995_W / 2 - margin, MG995_W / 2 + margin), (z1 - slab, z1))
    s.apply_transform(T)
    lo, hi = s.bounds
    m = s
    if lo[2] > z_floor + 0.5:
        m = union([s, box((lo[0], hi[0]), (lo[1], hi[1]), (z_floor, lo[2] + 0.5))])
    holes = [mg995_body(T, extra=200.0)]
    for sx in (-1, 1):
        for sy in (-1, 1):
            h = trimesh.creation.cylinder(radius=M3_FREE / 2, height=40, sections=24)
            h.apply_translation([xm + sx * MG995_HOLES[0] / 2, sy * MG995_HOLES[1] / 2, z1])
            h.apply_transform(T)
            holes.append(h)
    # asole passacavo alle due estremita', a tutta altezza fino alla faccia d'appoggio delle
    # orecchie: il cavo dell'MG995 esce dalla testata subito sotto l'orecchia
    # (larghe 6 mm: passano tra i due fori delle viti)
    for xe in (-MG995_SHAFT_END - 6, MG995_L - MG995_SHAFT_END + 6):
        sl = box((xe - 7, xe + 7), (-3, 3), (-MG995_HORN_TOP - 200, z1 + 1))
        sl.apply_transform(T)
        holes.append(sl)
    return diff(m, holes)


def x_horn(k, a, wire):
    """Squadretta doppia per l'MG995 centrale: due bracci opposti di raggio a
    (fori ogni 2.5 mm da a-5 a a+2.5) per i tiranti verso gli attacchi interni dei
    due bulbi. Si avvita sulla squadretta tonda/croce dell'MG995. Stampa in piano."""
    r_max = a + 5.0
    parts = [trimesh.creation.cylinder(radius=11.0, height=4.0, sections=64)]
    arm = trimesh.creation.box(extents=[2 * r_max, 9.0, 4.0])
    parts.append(arm)
    for sx in (-1, 1):
        tip = trimesh.creation.cylinder(radius=4.5, height=4.0, sections=48)
        tip.apply_translation([sx * r_max, 0, 0])
        parts.append(tip)
    holes = [trimesh.creation.cylinder(radius=3.2, height=6, sections=48)]
    for sx in (-1, 1):
        r = a - 5.0
        while r <= a + 2.51:
            h = trimesh.creation.cylinder(radius=(wire + 0.3) / 2, height=6, sections=24)
            h.apply_translation([sx * r, 0, 0])
            holes.append(h)
            r += 2.5
    m = diff(union(parts), holes)
    m.apply_translation([0, 0, 2.0])
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


def build_double_sync(D):
    """Coppia di occhi a 2 SERVO: asse X sincronizzato + palpebre sincronizzate.
    Servo veri solo sull'occhio sx (sx/dx e palpebre); nelle altre 4 sedi
    (su/giu sx e dx, sx/dx dx, palpebre dx) vanno servo finti stampati.
    Genera solo i pezzi nuovi: il resto si stampa dalla cartella double/Dxx."""
    k = D / D0
    tag = f"D{int(D)}"
    od = OUT / "double_2servo" / tag
    od.mkdir(parents=True, exist_ok=True)
    xc = EYE_PITCH * k / 2
    hw = hardware(k)
    dy = (TOWER_REAR_Y * k - GAP) - CRADLE_Y[1]
    axis = LID_SERVO_AXIS + np.array([dy, 0])

    dummy_servo().export(od / "DummyServo_MG90S_x4.stl")
    horn_extender(k, hw["filo_occhio_mm"], tie=True).export(od / f"HornExtender_Tie_{tag}.stl")
    horn_extender(k, hw["filo_occhio_mm"], tie=True, bore=M3_FREE).export(
        od / f"HornExtender_Pivot_{tag}_x3.stl")
    mirror_x(lid_crank(k, axis, bore=M3_FREE), xc).export(od / f"LidCrank_R_Pivot_{tag}.stl")
    bail = lid_bail(k, axis, xc)
    bail.export(od / f"LidBail_{tag}.stl")

    stack = (LINK_UP_X[1] - LINK_LO_X[0]) * k + 0.3 + 3.0 + 3.0   # tiranti + braccio + aletta
    info = {
        "diametro_mm": D, "k": round(k, 4), "interasse_occhi_mm": round(EYE_PITCH * k, 1),
        "servo_veri": "2 (occhio sx: sx/dx + palpebre)",
        "servo_finti": "4 (su/giu sx, su/giu dx, sx/dx dx, palpebre dx)",
        "asse_servo_palpebre_yz": np.round(axis, 2).tolist(),
        "raggio_braccio_palpebre_mm": round(k * float(np.linalg.norm(LINK_REAR - LID_SERVO_AXIS)), 1),
        "lunghezza_LidBail_mm": round(float(bail.extents[0]), 1),
        "tirante_X_filo_mm": hw["filo_occhio_mm"],
        "vite_LidBail": f"M2 x {int(np.ceil((stack + 2) / 2) * 2)} (2 per lato)",
        "perni_servo_finti": "vite M3 x 40 + dado M3 nel fondo (x4)",
    }
    (od / "info.txt").write_text("\n".join(f"{a}: {b}" for a, b in info.items()), encoding="utf8")
    for f in sorted(od.glob("*.stl")):
        m = trimesh.load(f)
        print(f"  {f.name:40s} wt={m.is_watertight} vol>0={m.volume > 0} ext={np.round(m.extents, 1)}")
    print(info)


def mg995_layout(D):
    """Posizioni (coordinate di montaggio) dei due MG995 della coppia a 2 servo."""
    k = D / D0
    xc = EYE_PITCH * k / 2
    dy = (TOWER_REAR_Y * k - GAP) - CRADLE_Y[1]
    axis = LID_SERVO_AXIS + np.array([dy, 0])
    plate_top, plate_bot = PLATE_TOP * k, PLATE_BOT * k
    # MG995 palpebre (occhio sx): albero coassiale all'asse manovelle, verso -X,
    # squadretta dove stava quella del MG90S, corpo verso il retro
    T_lid = frame([HORN_FACE_X, axis[0], axis[1]], [0, -1, 0], [0, 0, 1])
    # MG995 asse X: al centro, albero verso l'alto, corpo verso il retro;
    # squadretta circa alla quota degli attacchi laterali dei bulbi (z = 0)
    z_h = max(-2.0, plate_bot + MG995_HORN_TOP + 1.0)
    y_h = MG995_Y_FACTOR * k
    T_x = frame([xc, y_h, z_h], [0, -1, 0], [1, 0, 0])
    a = xc - EYE_LUG[0] * k                   # braccio = tiranti paralleli all'asse Y
    return dict(k=k, xc=xc, dy=dy, axis=axis, plate_top=plate_top, plate_bot=plate_bot,
                T_lid=T_lid, T_x=T_x, z_h=z_h, y_h=y_h, a=a)


MG995_Y_FACTOR = -42.0     # posizione Y dell'albero MG995 centrale = fattore * k
Y_ANCHOR_Z = -5.0          # quota (orig.) del foro di ancoraggio del tirante su/giu


def build_double_mg995(D):
    """Coppia di occhi a 2 servo MG995 (asse X + palpebre sincronizzati).
    - MG995 centrale, albero verticale: squadretta doppia + 2 tiranti in filo
      armonico agli attacchi INTERNI dei due bulbi -> i bulbi girano insieme;
    - MG995 palpebre sull'occhio sx, coassiale alle manovelle; LidBail porta il
      moto alle palpebre dx (manovella dx su perno ricavato nella piastra);
    - su/giu bloccato: tirante fisso dall'attacco superiore del bulbo a un
      montante dietro la torre dello snodo.
    La piastra non ha piu' i vani MG90S."""
    L = mg995_layout(D)
    k, xc, axis = L["k"], L["xc"], L["axis"]
    P = 2 * xc
    tag = f"D{int(D)}"
    od = OUT / "double_2servo_mg995" / tag
    od.mkdir(parents=True, exist_ok=True)
    hw = hardware(k)

    B, _ = baseplate_double(k, load("BasePlate", SRC2), cradles=False)
    z_floor = L["plate_top"] - 0.5
    adds = [mg995_mount(L["T_lid"], z_floor, margin=2.5), mg995_mount(L["T_x"], z_floor, margin=3.0)]
    # perno manovella palpebre dx (ex sede servo palpebre dx)
    xf = P - HORN_FACE_X                      # faccia su cui appoggia la manovella dx
    adds.append(box((xf - 8, xf), (axis[0] - 6, axis[0] + 6), (z_floor, axis[1] + 6)))
    # montanti bassi per il tirante fisso su/giu, attaccati dietro la torre dello
    # snodo: il tirante scende in diagonale dall'attacco superiore del bulbo, cosi'
    # resta fuori dalla corsa della palpebra superiore e della LidBail
    y_post = (TOWER_REAR_Y * k - 4.0, TOWER_REAR_Y * k + 1.0)
    z_anchor = Y_ANCHOR_Z * k
    for xe in (0.0, P):
        adds.append(box((xe - 5, xe + 5), y_post, (z_floor, z_anchor + 5)))
    B = union([B] + adds)
    # il corpo dell'MG995 centrale taglia anche i supporti protoboard posteriori
    # del vano centrale (non servono: la scheda EyeNode sta altrove)
    holes = [mg995_body(L["T_x"]), mg995_body(L["T_lid"]),
             cyl_x(M3_FREE / 2, xf - 10, xf + 1, *axis)]
    for xe in (0.0, P):
        holes.append(cyl_x((hw["filo_occhio_mm"] + 0.3) / 2, xe - 6, xe + 6, y_post[0] + 2.5, z_anchor))
    B = diff(B, holes)
    B.export(od / f"BasePlate_Double_MG995_{tag}.stl")

    # provino della sede MG995 (stessa geometria della piastra): da stampare prima
    T_fit = frame([0, 0, MG995_HORN_TOP], [1, 0, 0], [0, 1, 0])
    fit = union([mg995_mount(T_fit, 0.0, margin=3.0),
                 box((-MG995_SHAFT_END - 6, MG995_L - MG995_SHAFT_END + 6),
                     (-MG995_W / 2 - 3, MG995_W / 2 + 3), (0, 2.0))])
    fit = diff(fit, [mg995_body(T_fit, extra=10.0)])
    fit.export(od.parent / "MG995_FitTest.stl")

    x_horn(k, L["a"], hw["filo_occhio_mm"]).export(od / f"XHorn_MG995_{tag}.stl")
    lid_bail(k, axis, xc).export(od / f"LidBail_{tag}.stl")
    mirror_x(lid_crank(k, axis, bore=M3_FREE), xc).export(od / f"LidCrank_R_Pivot_{tag}.stl")

    lug_y = EYE_LUG[1] * k
    info = {
        "diametro_mm": D, "k": round(k, 4), "interasse_occhi_mm": round(P, 1),
        "servo": "2 x MG995 (centrale = asse X, laterale sx = palpebre)",
        "asse_MG995_centrale_xyz": [round(xc, 1), round(L["y_h"], 1), round(L["z_h"], 1)],
        "asse_MG995_palpebre_yz": np.round(axis, 2).tolist(),
        "braccio_XHorn_mm": round(float(L["a"]), 1),
        "tirante_X_lunghezza_mm": round(float(abs(L["y_h"] - lug_y)), 1),
        "tirante_X_filo_mm": hw["filo_occhio_mm"],
        "tirante_fisso_su_giu_mm": round(float(np.hypot(y_post[0] + 2.5 - lug_y,
                                                         EYE_LUG_TOP_Z * k - z_anchor)), 1),
        "viti_MG995": "8 x M3 x 12 + dado",
        "perno_manovella_dx": "vite M3 x 25 + dado autobloccante + rondelle",
    }
    (od / "info.txt").write_text("\n".join(f"{a}: {b}" for a, b in info.items()), encoding="utf8")
    for f in sorted(od.glob("*.stl")):
        m = trimesh.load(f)
        print(f"  {f.name:40s} wt={m.is_watertight} vol>0={m.volume > 0} ext={np.round(m.extents, 1)}")
    print(info)


if __name__ == "__main__":
    args = sys.argv[1:]
    only_double = "--double" in args
    only_sync = "--sync" in args
    only_mg995 = "--mg995" in args
    sizes = [float(a) for a in args if not a.startswith("--")] or [50, 70, 90]
    for D in sizes:
        if only_mg995:
            print(f"== double 2 x MG995 D{int(D)}")
            build_double_mg995(D)
            continue
        if only_sync:
            print(f"== double 2 servo D{int(D)}")
            build_double_sync(D)
            continue
        if not only_double:
            print(f"== single D{int(D)}")
            build(D)
        print(f"== double D{int(D)}")
        build_double(D)
        print(f"== double 2 servo D{int(D)}")
        build_double_sync(D)
        print(f"== double 2 x MG995 D{int(D)}")
        build_double_mg995(D)
