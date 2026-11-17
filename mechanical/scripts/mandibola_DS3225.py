"""
Supporto regolabile del servo della mandibola (DS3225, 25 kg) appeso alla base degli occhi D85.

Tre pezzi stampati (+ 2 rondelle stampate) e viti M4 / M3, nessuna modifica alla base:
  1. Traversa  - barra larga 246 mm appesa ai 2 fori da 12 mm davanti della base (x = +-62.7, y = -36.4)
                 con 2 colonnine alte 24 mm: passa sotto i piedi dei supporti a L (che sporgono 21.5 mm sotto
                 la base). Sotto ha 2 binari a T lungo x con dadi M4 scorrevoli -> DESTRA / SINISTRA.
  2. Braccio   - piastra orizzontale con asola lungo y (AVANTI / INDIETRO, 2 viti nei dadi della traversa) e
                 piastra verticale su un fianco con asola lungo z (SU / GIU'). Girandolo di 180 gradi la piastra
                 verticale va dall'altro lato / dall'altra parte.
  3. Culla     - tiene il DS3225 per le orecchie (4 viti M3, dadi nelle sedi) con l'albero orizzontale (asse x:
                 la mandibola gira come una cerniera attorno all'albero) e si avvita all'asola verticale del
                 braccio con 2 viti M4. Il servo puo' stare davanti o dietro la piastra verticale, con l'albero
                 in alto o in basso.

Coordinate della base assemblata: x verso destra, y verso dietro (linguetta PCA9685 a y > 40; gli occhi sono
davanti, a y < -100), z in su, fondo della base a z = 0 (i piedi dei supporti arrivano a z = -21.5).

Servo DS3225 (datasheet Dsservo DS3225 Red): corpo 40 x 20 x 40.5, orecchie 54.5, fori 49.5 x 10,
faccia inferiore delle orecchie a 27.7 dal fondo; albero a ~10 mm dall'estremita' del corpo (da verificare).

Uso: python mandibola_DS3225.py      -> STL in mechanical/mandibola/pezzi (posa di stampa) e il piatto A1 con
                                       2 set completi in mechanical/mandibola/stampa (progetto 3MF + STL + png)
"""
from pathlib import Path

import manifold3d as m3
import numpy as np
import trimesh
from manifold3d import Manifold

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "mechanical" / "mandibola"
PEZZI = OUT / "pezzi"
SEG = 48
ADD = m3.OpType.Add

# ------------------------------------------------------------------ viteria
M4_FREE, M4_HEAD_D, M4_NUT_AF, M4_NUT_H = 4.5, 8.6, 7.0, 3.2
M3_FREE, M3_NUT_AF, M3_NUT_H = 3.4, 5.5, 2.4

# ------------------------------------------------------------------ base degli occhi (D85 assemblata)
BASE_HOLES = [(-62.7, -36.4), (62.7, -36.4)]      # fori passanti D12 (quelli di Will, ingranditi)
BASE_T = 12.8                                     # spessore della base attorno ai fori
FEET_Z = -21.5                                    # fondo dei piedi dei supporti a L

# ------------------------------------------------------------------ servo DS3225
SV = dict(L=40.0, W=20.0, H=40.5, EAR_L=54.5, HOLE_L=49.5, HOLE_W=10.0, EAR_Z=27.7, EAR_T=2.5,
          SHAFT=10.0, SPLINE_H=4.5)
WIN_CL = 0.4                                      # gioco per lato nella finestra della culla

# ------------------------------------------------------------------ pezzi
TR = dict(x0=-123.0, x1=123.0, y0=-69.0, y1=-26.0,
          z_top=FEET_Z - 2.5, T=15.5,             # barra: sotto i piedi con 2.5 mm di gioco
          ch=(-47.0, -62.0), lip=3.5, chan=6.5, slot_w=4.6, chan_w=7.6,
          col_d=20.0, spig_d=11.5, spig_h=10.0,   # colonnine e perni di centraggio nei fori D12
          nut_z=-20.5)                            # quota del dado M4 dentro la colonnina
AR = dict(LEN=150.0, X0=-17.0, X1=17.5, TOP_T=10.0,
          V_X0=5.5, V_Y=30.0, V_H=200.0,          # piastra verticale: x 5.5..17.5, y 0..30
          RIB_X0=13.5, RIB_H=16.0,
          slot_z=(-40.0, -190.0))
CR = dict(T=6.0, ATT_W=30.0, H=72.0, SV_W=38.0, bolt_dz=40.0)
WASHER = dict(D=22.0, T=3.0)


def box(lo, hi):
    lo, hi = np.asarray(lo, float), np.asarray(hi, float)
    return Manifold.cube(tuple(hi - lo)).translate(tuple(lo))


def cyl(r, p0, p1, seg=SEG):
    """cilindro tra due punti su una retta parallela a un asse."""
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    d = p1 - p0
    a = int(np.argmax(np.abs(d)))
    c = Manifold.cylinder(float(abs(d[a])), r, r, seg)
    if a == 0:
        c = c.rotate((0, 90, 0))
    elif a == 1:
        c = c.rotate((-90, 0, 0))
    return c.translate(tuple(p0 if d[a] > 0 else p1))


def slot(w, p0, p1, thru, t0, t1):
    """asola larga w tra i centri p0 e p1, passante lungo l'asse 'thru' da t0 a t1."""
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    a, b, a2, b2 = p0.copy(), p1.copy(), p0.copy(), p1.copy()
    a[thru] = b[thru] = t0
    a2[thru] = b2[thru] = t1
    ax = int(np.argmax(np.abs(p1 - p0)))
    lo, hi = np.minimum(p0, p1), np.maximum(p0, p1)
    for k in range(3):
        if k == thru:
            lo[k], hi[k] = min(t0, t1), max(t0, t1)
        elif k != ax:
            lo[k] -= w / 2
            hi[k] += w / 2
    return Manifold.batch_boolean([cyl(w / 2, a, a2), cyl(w / 2, b, b2), box(lo, hi)], ADD)


def to_tm(m):
    mm = m.to_mesh()
    return trimesh.Trimesh(np.asarray(mm.vert_properties)[:, :3], np.asarray(mm.tri_verts), process=True)


# ======================================================================== 1. traversa (coord. base)
def traversa():
    t = TR
    zt, zb = t["z_top"], t["z_top"] - t["T"]
    parts = [box((t["x0"], t["y0"], zb), (t["x1"], t["y1"], zt))]
    for (x, y) in BASE_HOLES:
        parts.append(cyl(t["col_d"] / 2, (x, y, zt - 0.01), (x, y, 0.0)))
        parts.append(cyl(t["spig_d"] / 2, (x, y, -0.01), (x, y, t["spig_h"])))
    m = Manifold.batch_boolean(parts, ADD)
    for yc in t["ch"]:   # binari a T aperti in basso e alle estremita'
        m = m - box((t["x0"] - 1, yc - t["slot_w"] / 2, zb - 1), (t["x1"] + 1, yc + t["slot_w"] / 2, zb + t["lip"]))
        m = m - box((t["x0"] - 1, yc - t["chan_w"] / 2, zb + t["lip"]),
                    (t["x1"] + 1, yc + t["chan_w"] / 2, zb + t["lip"] + t["chan"]))
    for (x, y) in BASE_HOLES:
        m = m - cyl(M4_FREE / 2, (x, y, zb - 1), (x, y, t["spig_h"] + 1))
        # sede del dado M4 nella colonnina, infilato di lato (dal retro, +y)
        nz0, nz1 = t["nut_z"] - (M4_NUT_H + 0.4) / 2, t["nut_z"] + (M4_NUT_H + 0.4) / 2
        af = M4_NUT_AF + 0.3
        m = m - box((x - af / 2, y - af / 2 * 1.155, nz0), (x + af / 2, y + t["col_d"], nz1))
    return m


# ======================================================================== 2. braccio (coord. locali)
# origine: estremita' della piastra orizzontale, faccia superiore, asse dell'asola (x = 0); y lungo il braccio
def braccio():
    a = AR
    parts = [box((a["X0"], 0, -a["TOP_T"]), (a["X1"], a["LEN"], 0)),
             box((a["RIB_X0"], 0, -a["TOP_T"] - a["RIB_H"]), (a["X1"], a["LEN"], -a["TOP_T"])),
             box((a["V_X0"], 0, -a["V_H"]), (a["X1"], a["V_Y"], 0))]
    m = Manifold.batch_boolean(parts, ADD)
    m = m - slot(M4_FREE, (0, 7.25, 0), (0, a["LEN"] - 7.25, 0), 2, 1, -a["TOP_T"] - 1)
    m = m - slot(M4_FREE, (0, a["V_Y"] / 2, a["slot_z"][0]), (0, a["V_Y"] / 2, a["slot_z"][1]), 0,
                 a["V_X0"] - 1, a["X1"] + 1)
    return m


# ======================================================================== 3. culla (coord. locali)
# piastra nel piano yz, spessa in x (0..T; x = 0 contro il braccio); zona di attacco y 0..ATT_W con i 2 fori
# M4 su y = ATT_W/2 (z = 0 e z = -bolt_dz); zona servo y ATT_W..ATT_W+SV_W con la finestra del corpo.
def culla():
    c = CR
    zc = -c["bolt_dz"] / 2
    m = box((0, 0, zc - c["H"] / 2), (c["T"], c["ATT_W"] + c["SV_W"], zc + c["H"] / 2))
    for z in (0.0, -c["bolt_dz"]):
        m = m - cyl(M4_FREE / 2, (-1, c["ATT_W"] / 2, z), (c["T"] + 1, c["ATT_W"] / 2, z))
    ys = c["ATT_W"] + c["SV_W"] / 2
    wl, ww = SV["L"] + 2 * WIN_CL, SV["W"] + 2 * WIN_CL
    m = m - box((-1, ys - ww / 2, zc - wl / 2), (c["T"] + 1, ys + ww / 2, zc + wl / 2))
    for dz in (-SV["HOLE_L"] / 2, SV["HOLE_L"] / 2):
        for dy in (-SV["HOLE_W"] / 2, SV["HOLE_W"] / 2):
            y, z = ys + dy, zc + dz
            m = m - cyl(M3_FREE / 2, (-1, y, z), (c["T"] + 1, y, z))
            m = m - cyl((M3_NUT_AF + 0.3) / np.sqrt(3), (-1, y, z), (M3_NUT_H + 0.3, y, z), seg=6)
    return m, ys, zc


def rondella():
    w = WASHER
    return cyl(w["D"] / 2, (0, 0, 0), (0, 0, w["T"])) - cyl(M4_FREE / 2, (0, 0, -1), (0, 0, w["T"] + 1))


# ======================================================================== servo (per immagini e verifiche)
def servo_model():
    """DS3225: albero lungo +x, orecchie sul piano x = 0..EAR_T, asse lungo del corpo lungo z (centro z = 0)."""
    s = SV
    top = s["H"] - s["EAR_Z"]
    zs = s["L"] / 2 - s["SHAFT"]
    parts = [box((-s["EAR_Z"], -s["W"] / 2, -s["L"] / 2), (top, s["W"] / 2, s["L"] / 2)),
             box((0, -s["W"] / 2 + 1, -s["EAR_L"] / 2), (s["EAR_T"], s["W"] / 2 - 1, s["EAR_L"] / 2)),
             cyl(3.0, (top - 0.1, 0, zs), (top + s["SPLINE_H"], 0, zs)),
             box((top + s["SPLINE_H"], -4, zs - 4), (top + s["SPLINE_H"] + 3, 4, zs + 25))]
    m = Manifold.batch_boolean(parts, ADD)
    for dz in (-s["HOLE_L"] / 2, s["HOLE_L"] / 2):
        for dy in (-s["HOLE_W"] / 2, s["HOLE_W"] / 2):
            m = m - cyl(1.8, (-1, dy, dz), (s["EAR_T"] + 1, dy, dz))
    return m, zs


def assieme(x_arm=0.0, y_arm=-160.0, verso=+1, z_cr=-60.0, servo_davanti=True, albero_su=True):
    """Posizione di esempio (coordinate della base).
    x_arm: asse dell'asola del braccio; y_arm: estremita' del braccio con la piastra verticale;
    verso=+1: il braccio va verso dietro (+y) e la piastra verticale e' a +x; verso=-1: girato di 180 gradi.
    z_cr: foro alto della culla sotto la faccia superiore del braccio; servo_davanti: zona servo verso -y
    (rispetto al braccio non girato)."""
    zt = TR["z_top"] - TR["T"]                    # faccia inferiore della traversa = superiore del braccio
    Rz = trimesh.transformations.rotation_matrix(0 if verso > 0 else np.pi, (0, 0, 1))
    Tw = trimesh.transformations.translation_matrix((x_arm, y_arm, zt)) @ Rz
    A = to_tm(braccio())
    A.apply_transform(Tw)
    Cm, ys, zc = culla()
    C = to_tm(Cm)
    Sm, _ = servo_model()
    S = to_tm(Sm)
    if not albero_su:
        S.apply_transform(trimesh.transformations.reflection_matrix((0, 0, 0), (0, 0, 1)))
    y_srv = ys
    if servo_davanti:
        F = trimesh.transformations.reflection_matrix((0, CR["ATT_W"] / 2, 0), (0, 1, 0))
        C.apply_transform(F)
        y_srv = CR["ATT_W"] - ys
    # culla sulla faccia esterna della piastra verticale (x = X1 nel braccio), allineata in y con la piastra
    C.apply_translation((AR["X1"], AR["V_Y"] / 2 - CR["ATT_W"] / 2, z_cr))
    S.apply_translation((AR["X1"] + CR["T"], AR["V_Y"] / 2 - CR["ATT_W"] / 2 + y_srv, z_cr + zc))
    C.apply_transform(Tw)
    S.apply_transform(Tw)
    return dict(traversa=to_tm(traversa()), braccio=A, culla=C, servo=S)


def pose_di_stampa():
    T = to_tm(traversa())                          # binari sul piatto, colonnine in su
    T.apply_translation(-T.bounds[0])
    A = to_tm(braccio())                           # capovolto: faccia superiore sul piatto, piastra verticale in su
    A.apply_transform(trimesh.transformations.rotation_matrix(np.pi, (0, 1, 0)))
    A.apply_translation(-A.bounds[0])
    C = to_tm(culla()[0])                          # faccia contro il braccio (sedi dei dadi M3) sul piatto
    C.apply_transform(trimesh.transformations.rotation_matrix(-np.pi / 2, (0, 1, 0)))
    C.apply_translation(-C.bounds[0])
    W = to_tm(rondella())
    W.apply_translation(-W.bounds[0])
    return {"Traversa": T, "Braccio": A, "Culla_DS3225": C, "Rondella_x2": W}


# piatto A1 con 2 set completi (2 teste): disposizione trovata con teste_D85.Packer sulle impronte reali
PIATTO = "layout_piatti.json"
STAMPA = {"wall_loops": "4", "sparse_infill_density": "25%", "sparse_infill_pattern": "gyroid",
          "enable_support": "0"}


def export():
    PEZZI.mkdir(parents=True, exist_ok=True)
    for n, m in pose_di_stampa().items():
        assert m.is_watertight, n
        m.export(PEZZI / f"{n}.stl")
        print(f"{n:14s} {np.round(m.extents, 1).tolist()}  {m.volume / 1000:.1f} cm3")
    piatto()


def piatto():
    import json
    import shutil
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import teste_D85 as T
    T.PEZZI = PEZZI
    T._mesh.clear()
    sd = OUT / "stampa"
    lay = json.load(open(sd / PIATTO, encoding="utf-8"))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    for pl in lay["piatti"]:
        pdir = sd / pl["nome"]
        if pdir.exists():
            shutil.rmtree(pdir)
        pdir.mkdir(parents=True)
        items = pl["pezzi"]
        meshes = [T.placed(it) for it in items]
        d, lo, hi, fps = T.check(items)
        for k, (it, m) in enumerate(zip(items, meshes)):
            m.export(pdir / f"{k:02d}_{it['pezzo']}.stl")
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.add_patch(plt.Rectangle((0, 0), T.BED, T.BED, fc="#eeeeee", ec="k"))
        for it, f in zip(items, fps):
            for gg in getattr(f, "geoms", [f]):
                ax.fill(*gg.exterior.xy, alpha=.75)
            c = f.representative_point()
            ax.text(c.x, c.y, it["pezzo"].replace("_x2", "").replace("_DS3225", ""), ha="center", fontsize=8)
        ax.set_xlim(-5, T.BED + 5)
        ax.set_ylim(-5, T.BED + 5)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_title(f"Supporto mandibola - {pl['nome']}: 2 set completi")
        fig.savefig(pdir / "piatto.png", dpi=80, bbox_inches="tight")
        plt.close(fig)
        name = f"Mandibola_{pl['nome']}"
        T.write_3mf(pdir / f"{name}.3mf", items, meshes, name, png=pdir / "piatto.png", impostazioni=STAMPA)
        zmax = max(m.bounds[1, 2] for m in meshes)
        print(f"{name}: {len(items)} pezzi, distanza minima {d:.1f} mm, bordo {lo:.1f}..{hi:.1f}, alt. {zmax:.0f} mm")


if __name__ == "__main__":
    export()
