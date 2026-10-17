"""
Occhi IBRIDI per l'Idra: assi X/Y "alla EyeMech" + palpebre "alla MorganManly".

Unisce due progetti:
  * EyeMech e3.2 (Will Cogley): un solo servo per l'asse X e uno solo per l'asse Y,
    comuni ai due occhi. Un telaio centrale ("Core") ruota attorno all'asse orizzontale
    che passa per i centri dei bulbi (Y = su/giu'); sul Core c'e' il servo X che muove
    i due bulbi attorno a perni verticali tramite un parallelogramma (manovella +
    tirante trasversale + leve dei bulbi, tutte uguali e parallele).
  * Animatronic Eyes (MorganManly): per ogni occhio UN solo servo palpebre; la sua
    manovella spinge in avanti due tiranti, uno sulla palpebra superiore (sopra l'asse)
    e uno sull'inferiore (sotto l'asse): spingendo, le due palpebre si chiudono insieme.
Totale 4 servo SG90/MG90S: X, Y, palpebre sx, palpebre dx (si puo' fare l'occhiolino).

Il progetto e' parametrico: tutta la meccanica segue il diametro D del bulbo, MA le
sedi dei servo, le squadrette e la viteria restano 1:1 (SG90/MG90S).
Rispetto ai pezzi originali (snap-fit e print-in-place da 32 mm, che ingranditi
diventerebbero laschi) tutti i perni sono viti M3 con giochi fissi.

Coordinate di montaggio: origine = punto medio tra i centri dei bulbi,
+Y = sguardo, +Z = alto, +X = destra della creatura. Occhio sx (L) a x = -xe,
occhio dx (R) a x = +xe. Angoli nel piano YZ misurati da +Y verso +Z.

Uso:  python generate_hybrid.py              -> D = 85 mm (baseline)
      python generate_hybrid.py 95 110       -> diametri in mm
      python generate_hybrid.py --cm 9.5     -> diametro in cm
      python generate_hybrid.py --plus 1.5   -> baseline 8.5 cm + 1.5 cm = 10 cm
      opzioni: --horn-h 30.5  (fondo servo -> faccia superiore squadretta, da misurare)
               --bed 250      (oltre questa larghezza la base viene divisa in due)
               --no-check     (salta la verifica delle interferenze)
               --render       (immagini di montaggio in docs/img)
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import trimesh
from scipy.optimize import brentq, fsolve
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union

sys.path.insert(0, str(Path(__file__).parent))
from generate_eyes import box, diff, inter, mirror_x, union  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "mechanical" / "eyes" / "scaled" / "hybrid_eyemech"
IMG = ROOT / "docs" / "img"
D_BASE = 85.0               # baseline del bulbo [mm]

# --- SG90 / MG90S (1:1, stime da datasheet: VERIFICARE col calibro) ------------
SG_L, SG_W, SG_H = 22.8, 12.4, 22.7   # corpo: lunghezza, larghezza, fondo -> cassa
SG_SHAFT = 6.0              # asse albero -> estremita' vicina del corpo
SG_EAR_Z = (15.9, 18.4)     # orecchie: faccia lato fondo / lato squadretta (dal fondo)
SG_EAR_SPAN = 32.6          # orecchia-orecchia
SG_EAR_HOLES = 27.8         # interasse fori orecchie
SG_CLEAR = 0.3              # gioco per lato nelle sedi
HORN_H = 30.5               # fondo servo -> faccia della squadretta su cui poggia la manovella
HORN_LEN = 20.0             # raggio massimo squadretta (per gli scassi di rotazione)

# --- viteria e giochi fissi ---------------------------------------------------------
M3_FREE, M3_TAP = 3.4, 2.5  # foro passante / foro da filettare (vite M3 nella plastica)
M2_TAP = 1.8
HEAD_D, HEAD_H = 6.0, 3.0   # testa vite M3 (cilindrica/bombata)
STD_M3 = (6, 8, 10, 12, 16, 20, 25, 30, 35, 40, 45, 50, 60)

G_LID = 1.5                 # gioco radiale bulbo -> palpebra inferiore
T_LID = 3.0                 # spessore palpebre e "orecchie"
T_EYE = 2.4                 # spessore guscio bulbo
LAYER_GAP = 0.5             # gioco tra strati affiancati
T_PLATE = 3.0               # spessore manovelle, tiranti, leve
BOSS_R = 5.0                # raggio occhielli dei perni
SLAB = (-6.0, 6.0)          # spessore (z) del telaio centrale Core
HUB_R = 7.0                 # mozzo verticale nel centro del bulbo
POST_T = 5.0                # spessore montanti

# --- movimento ------------------------------------------------------------------------
YAW_MAX = 30.0              # sx/dx [deg]
PITCH_MAX = 20.0            # su/giu' [deg]
LID_UP_OPEN, LID_UP_REAR = 30.0, 105.0     # palpebra sup.: bordo anteriore / posteriore (aperta)
LID_LO_OPEN, LID_LO_REAR = -30.0, -105.0   # palpebra inf.
LID_UP_CLOSED, LID_LO_CLOSED = -6.0, -3.0  # bordi a palpebre chiuse (la sup. passa sopra l'inf.)
LID_SERVO = (40, 36, 32, 28, 25, 22)   # corse servo palpebre provate (+-, attorno alla verticale)
LUG_ANG = 12.0              # attacchi tiranti (a meta' corsa) entro +-12 deg dalla verticale, come MorganManly
LUG_RMAX = 0.45             # raggio max attacco = 0.45 R (dentro l'orecchia)
LID_CRANK_R = 10.0          # raggio manovella palpebre
LINK_W = 7.0                # larghezza tiranti palpebre
LINK_CLEAR = 8.0            # distanza minima asse tirante - albero servo (mozzo squadretta r~3.5 + LINK_W/2)
Y_SERVO = 40.0              # corsa servo Y per +-PITCH_MAX


# ======================================================================================
# utilita' geometriche
# ======================================================================================
YZ = np.array([[0, 0, 1, 0], [1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1]], float)


def ext_xy(poly, z0, z1):
    """Estrude un poligono shapely (x, y) tra z0 e z1."""
    m = trimesh.creation.extrude_polygon(poly, z1 - z0)
    m.apply_translation([0, 0, z0])
    return m


def ext_yz(poly, x0, x1):
    """Estrude un poligono shapely (y, z) tra x0 e x1."""
    m = trimesh.creation.extrude_polygon(poly, x1 - x0)
    m.apply_transform(YZ)
    m.apply_translation([x0, 0, 0])
    return m


def circ(c, r, res=24):
    return Point(c).buffer(r, resolution=res)


def bar2d(p0, p1, w):
    return LineString([p0, p1]).buffer(w / 2, resolution=24)


def sector2d(r, a0, a1, c=(0, 0), n=48):
    a = np.radians(np.linspace(a0, a1, n))
    pts = [c] + [(c[0] + r * np.cos(t), c[1] + r * np.sin(t)) for t in a]
    return Polygon(pts)


def sphere(r, c=(0, 0, 0), sub=5):
    s = trimesh.creation.icosphere(subdivisions=sub, radius=r)
    s.apply_translation(c)
    return s


def cyl(r, p0, p1, sections=48):
    """Cilindro tra due punti."""
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    return trimesh.creation.cylinder(radius=r, segment=[p0, p1], sections=sections)


def rot_x(deg, c=(0, 0, 0)):
    return trimesh.transformations.rotation_matrix(np.radians(deg), [1, 0, 0], c)


def rot_z(deg, c=(0, 0, 0)):
    return trimesh.transformations.rotation_matrix(np.radians(deg), [0, 0, 1], c)


def rot_y(deg, c=(0, 0, 0)):
    return trimesh.transformations.rotation_matrix(np.radians(deg), [0, 1, 0], c)


def moved(m, T):
    m = m.copy()
    m.apply_transform(T)
    return m


def rot2(v, deg):
    a = np.radians(deg)
    c, s = np.cos(a), np.sin(a)
    return np.array([c * v[0] - s * v[1], s * v[0] + c * v[1]])


def pol(r, deg):
    a = np.radians(deg)
    return np.array([r * np.cos(a), r * np.sin(a)])


def std_len(lmax):
    ok = [s for s in STD_M3 if s <= lmax]
    return ok[-1] if ok else STD_M3[0]


# ======================================================================================
# layout: tutte le quote derivano da D (le parti servo restano fisse)
# ======================================================================================
class Layout:
    def __init__(self, D, horn_h=HORN_H):
        self.D, self.R = D, D / 2
        R = self.R
        self.horn_h = horn_h
        # palpebre: inferiore all'interno, superiore all'esterno (puo' sovrapporsi in chiusura)
        self.RL = (R + G_LID, R + G_LID + T_LID)
        self.RU = (self.RL[1] + LAYER_GAP, self.RL[1] + LAYER_GAP + T_LID)
        E = self.E = R + G_LID
        # strati laterali (distanza dal centro bulbo lungo X, uguali dentro e fuori)
        self.L1 = (E, E + T_LID)                              # orecchie palpebra inf.
        self.L2 = (E + T_LID + LAYER_GAP, E + 2 * T_LID + LAYER_GAP)   # orecchie sup. / tirante inf.
        self.L3 = (self.L2[1] + LAYER_GAP, self.L2[1] + LAYER_GAP + T_PLATE)  # tirante sup.
        self.L4 = (self.L3[1] + LAYER_GAP, self.L3[1] + LAYER_GAP + T_PLATE)  # manovella / montante est.
        # telaio centrale: semilarghezza fissa (servo X), poi montante, poi le orecchie
        self.core_x = 12.0                                    # faccia esterna boss perno Y del Core
        self.cpost = (self.core_x + LAYER_GAP, self.core_x + LAYER_GAP + POST_T)
        self.xe = self.cpost[1] + (self.L2[1] - E) + LAYER_GAP + E   # centro bulbo
        # bulbo
        self.y_cut = -0.35 * R                                # piano di taglio posteriore del bulbo
        # leve (parallelogramma X) e telaio
        self.Lv = R + 5.0                                     # lunghezza leve/manovella X
        self.bar_front = -(0.772 * R + 3.5)                   # traversa del Core (dietro i bulbi)
        self.bar_back = self.bar_front - 6.0
        # quote z del piano leve / tirante
        self.z_lev = (SLAB[0] - 3.6, SLAB[0] - 0.6)           # leve, manovella X (-9.6..-6.6)
        self.z_lboss = self.z_lev[0] - 3.6                    # fondo occhielli leve (-13.2)
        self.z_tie = (self.z_lboss - 3.4, self.z_lboss - 0.4)  # tirante (-16.6..-13.6)
        # servo X capovolto nel Core: orecchie appoggiate sulla faccia superiore
        self.x_bottom = SLAB[1] + SG_EAR_Z[1]                 # fondo servo (in alto)
        self.x_crank_face = self.x_bottom - horn_h            # deve coincidere con z_lev[1]
        # leva Y (pende sotto il perno Y, lato +x) e servo Y
        self.q_z = -0.62 * R
        self.ry = round(abs(self.q_z) * np.sin(np.radians(PITCH_MAX)) / np.sin(np.radians(Y_SERVO)), 1)
        self.ylev_x = (self.core_x - 3.0, self.core_x)        # leva Y (9..12)
        self.ylink_x = (self.ylev_x[0] - 3.5, self.ylev_x[0] - 0.5)
        self.ycrank_x = (self.ylink_x[0] - 3.5, self.ylink_x[0] - 0.5)
        # servo Y DAVANTI al perno (tra i bulbi, sotto il Core): lontano dal tirante X, che
        # guardando in alto scende dietro; corpo verso l'avanti, albero verso +x
        self.ys = np.array([22.0, self.q_z - self.ry])
        # palpebre: servo esterno, albero verso l'esterno, corpo verso il retro
        self.ls = None                                        # asse servo palpebre: da solve_lids
        assert abs(self.x_crank_face - self.z_lev[1]) < 1.5, \
            f"horn_h={horn_h}: la manovella X non e' sul piano delle leve (rivedere SLAB/HORN_H)"
        # piastra di base
        self.z_base = min(-(self.RL[1] + 2.5), self.ys[1] - SG_W / 2 - 3.0)
        self.base_t = 4.0
        self.lid, self.ls = solve_lids(self)
        self.pitch = solve_pitch(self)

    @property
    def P(self):
        return 2 * self.xe


# ======================================================================================
# cinematica
# ======================================================================================
def lid_pin(L, th):
    """Perno manovella palpebre (y, z) per angolo servo th (0 = verso l'alto, + = avanti)."""
    return L.ls + L_CR(L) * np.array([np.sin(np.radians(th)), np.cos(np.radians(th))])


def L_CR(L):
    return LID_CRANK_R


def solve_lids(L):
    """Trova gli attacchi (raggio, angolo) sulle palpebre in modo che la corsa servo
    -L.lid_servo..+L.lid_servo porti entrambe le palpebre da aperte a chiuse.
    Vincoli: tirante perpendicolare alla leva a meta' corsa (trasmissione migliore) e
    tiranti sempre lontani dall'albero/mozzo squadretta del servo (stanno sullo stesso
    piano della squadretta). Prova diverse quote del servo e tiene la migliore."""
    best_all = None
    y_s = -(L.Lv + 12.0)
    combos = []
    for trav in LID_SERVO:
        # la linguetta della manovella (16 mm, verso il retro) non deve toccare la base
        z_min = L.z_base + 1.0 + 4.0 + 16.0 * np.sin(np.radians(trav))
        combos += [(trav, z) for z in np.arange(-10.0, -34.1, -2.0) if z >= z_min]
    for trav, z_s in combos:
        L.lid_servo = trav
        L.ls = np.array([y_s, z_s])
        out, score_tot = {}, 0.0
        for kind, delta in (("up", LID_UP_CLOSED - LID_UP_OPEN), ("lo", LID_LO_CLOSED - LID_LO_OPEN)):
            best = None
            v0 = 90.0 if kind == "up" else -90.0
            # attacco sopra/sotto il perno (come MorganManly): a meta' corsa entro +-LUG_ANG dalla verticale
            for a_mid in np.arange(v0 - LUG_ANG, v0 + LUG_ANG + 0.01, 1.0):
                def g(r):
                    A0 = pol(r, a_mid - delta / 2)
                    return (np.linalg.norm(lid_pin(L, -L.lid_servo) - A0)
                            - np.linalg.norm(lid_pin(L, L.lid_servo) - rot2(A0, delta)))
                rs = np.linspace(10.0, LUG_RMAX * L.R, 41)
                v = np.array([g(r) for r in rs])
                for i in np.nonzero(v[:-1] * v[1:] <= 0)[0]:
                    r = brentq(g, rs[i], rs[i + 1]) if v[i] != v[i + 1] else rs[i]
                    A0 = pol(r, a_mid - delta / 2)
                    l0 = np.linalg.norm(lid_pin(L, -L.lid_servo) - A0)
                    Am = pol(r, a_mid)
                    link = lid_pin(L, 0.0) - Am
                    tr = np.degrees(np.arccos(abs(link @ Am) / (np.linalg.norm(link) * r)))
                    # distanza minima tirante - albero lungo la corsa
                    dmin = 1e9
                    for th in np.linspace(-L.lid_servo, L.lid_servo, 9):
                        A = rot2(A0, delta * (th + L.lid_servo) / (2 * L.lid_servo))
                        Pp = lid_pin(L, th)
                        dmin = min(dmin, LineString([A, Pp]).distance(Point(L.ls)))
                    if dmin < LINK_CLEAR:
                        continue
                    err = abs(np.linalg.norm(link) - l0)
                    score = (90 - tr) + 5 * err + 0.2 * r
                    if best is None or score < best[0]:
                        best = (score, r, a_mid - delta / 2, tr, dmin)
            if best is None:
                out = None
                break
            _, r, a, tr, dmin = best
            A0 = pol(r, a)
            out[kind] = dict(r=float(r), a=float(a), l=float(np.linalg.norm(lid_pin(L, -L.lid_servo) - A0)),
                             delta=delta, A0=A0, trasm=float(tr), dist_albero=float(dmin))
            score_tot += best[0]
        score_tot += 0.6 * (max(LID_SERVO) - trav)      # preferisce corse servo ampie
        if out is not None and (best_all is None or score_tot < best_all[0]):
            best_all = (score_tot, out, L.ls.copy(), trav)
    assert best_all is not None, "nessuna geometria palpebre valida"
    L.lid_servo = best_all[3]
    return best_all[1], best_all[2]


def lid_angle(L, kind, th):
    """Rotazione della palpebra (deg, 0 = aperta come modellata) per angolo servo th."""
    d = L.lid[kind]
    P = lid_pin(L, th)

    def f(psi):
        return np.linalg.norm(P - rot2(d["A0"], psi)) - d["l"]

    lo, hi = sorted((-15.0 + min(0, d["delta"]) * 1.6, 15.0 + max(0, d["delta"]) * 1.6))
    grid = np.linspace(lo, hi, 400)
    v = np.array([f(g) for g in grid])
    # radice piu' vicina all'interpolazione lineare attesa
    guess = d["delta"] * (th + L.lid_servo) / (2 * L.lid_servo)
    roots = [grid[i] if v[i] == 0 else brentq(f, grid[i], grid[i + 1])
             for i in range(len(grid) - 1) if v[i] * v[i + 1] <= 0 and v[i + 1] != 0]
    return min(roots, key=lambda x: abs(x - guess))


def solve_pitch(L):
    Q0 = np.array([0.0, L.q_z])
    C0 = L.ys + np.array([0.0, L.ry])
    return dict(Q0=Q0, l=float(np.linalg.norm(C0 - Q0)))


def y_crank_pin(L, beta):
    return L.ys + L.ry * np.array([np.sin(np.radians(beta)), np.cos(np.radians(beta))])


def y_servo_angle(L, a):
    """Angolo del servo Y (0 = manovella verticale) per inclinazione a del Core
    (inseguendo la soluzione con continuita' da a = 0)."""
    beta = 0.0
    for aa in np.linspace(0.0, a, max(2, int(abs(a)) * 2 + 1))[1:]:
        Q = rot2(L.pitch["Q0"], aa)

        def f(b):
            return np.linalg.norm(y_crank_pin(L, b) - Q) - L.pitch["l"]

        grid = np.linspace(beta - 20, beta + 20, 81)
        v = np.array([f(g) for g in grid])
        roots = [grid[i] if v[i] == 0 else brentq(f, grid[i], grid[i + 1])
                 for i in range(len(grid) - 1) if v[i] * v[i + 1] <= 0 and v[i + 1] != 0]
        beta = min(roots, key=lambda x: abs(x - beta))
    return beta


def planar_T(p0, p1, q0, q1, x=0.0):
    """Trasformazione rigida nel piano YZ che porta il segmento p0-p1 su q0-q1."""
    a0 = np.arctan2(*(np.asarray(p1) - p0)[::-1])
    a1 = np.arctan2(*(np.asarray(q1) - q0)[::-1])
    T = rot_x(np.degrees(a1 - a0))
    T[:3, 3] = 0
    t = np.array([0, *q0]) - T[:3, :3] @ np.array([0, *p0])
    T[:3, 3] = t
    return T


# ======================================================================================
# pezzi (coordinate di montaggio, posa neutra; occhio dx dove serve, poi specchiato)
# ======================================================================================
def eyeball(L, pupil="slit"):
    """Bulbo: calotta anteriore cava (tagliata dietro a y_cut) con due colonne ai poli
    per le viti-perno M3 dell'asse X e le nervature che le reggono in stampa.
    Coordinate centrate sul bulbo."""
    R = L.R
    shell = diff(sphere(R), [sphere(R - T_EYE)])
    shell = inter(shell, box((-R - 1, R + 1), (L.y_cut, R + 1), (-R - 1, R + 1)))
    top = (6.0 + 0.6, R - 0.5)                    # colonna superiore (sopra il mozzo)
    bot = (-(R - 0.5), L.z_lev[0])                # colonna inferiore (sotto la leva)
    parts = [shell]
    for z0, z1 in (top, bot):
        col = cyl(5.0, (0, 0, z0), (0, 0, z1))
        rib = box((-5, 5), (L.y_cut, 0), (z0, z1))
        parts.append(inter(union([col, rib]), sphere(R - 0.5)))
    # chiave esagonale per la leva X sotto al mozzo
    hexk = ext_xy(Polygon([(4.6 * np.cos(t), 4.6 * np.sin(t)) for t in np.radians(np.arange(0, 360, 60))]),
                  L.z_lev[0], L.z_lev[0] + 2.0)
    parts.append(hexk)
    m = union(parts)
    # la nervatura inferiore sta 0.4 sotto la leva (che vi appoggia solo sul mozzo)
    m = diff(m, [box((-6, 6), (L.y_cut - 1, -4.2), (L.z_lev[0] - 0.4, L.z_lev[0] + 0.01))])
    # viti-perno: lunghezza standard, punta a 0.75 mm dal centro
    screws = {}
    holes = []
    for sgn, (z0, z1) in ((1, top), (-1, bot)):
        Ls = std_len(R - HEAD_H - 0.75 - 0.5)
        seat = 0.75 + Ls
        screws["top" if sgn > 0 else "bottom"] = Ls
        holes.append(cyl(M3_FREE / 2, (0, 0, 0), (0, 0, sgn * (R + 1))))
        holes.append(cyl(HEAD_D / 2 + 0.2, (0, 0, sgn * seat), (0, 0, sgn * (R + 1))))
    # tratto filettato: 8 mm nella colonna vicino al mozzo
    m = diff(m, holes)
    tap_t = cyl(M3_TAP / 2 + 0.01, (0, 0, top[0]), (0, 0, top[0] + 8))
    tap_b = cyl(M3_TAP / 2 + 0.01, (0, 0, bot[1] - 8), (0, 0, bot[1]))
    sleeve = [diff(cyl(M3_FREE / 2 + 0.05, (0, 0, top[0]), (0, 0, top[0] + 8)), [tap_t]),
              diff(cyl(M3_FREE / 2 + 0.05, (0, 0, bot[1] - 8), (0, 0, bot[1])), [tap_b])]
    m = union([m] + sleeve)
    # iride e pupilla incise (per la pittura)
    ri = 0.42 * R
    iris = inter(diff(sphere(R + 1), [sphere(R - 0.6)]), cyl(ri, (0, 0, 0), (0, R + 2, 0), 96))
    if pupil == "slit":
        pup = trimesh.creation.cylinder(radius=1.0, height=R + 2, sections=64)
        pup.apply_scale([0.075 * R, 0.30 * R, 1])
        pup.apply_transform(rot_x(-90))
        pup.apply_translation([0, (R + 2) / 2, 0])
    else:
        pup = cyl(0.16 * R, (0, 0, 0), (0, R + 2, 0), 64)
    pupil_m = inter(diff(sphere(R + 1), [sphere(R - 1.4)]), pup)
    m = diff(m, [iris, pupil_m])
    return m, screws


def yaw_lever(L):
    """Leva del bulbo (coordinate del bulbo): si infila sulla chiave esagonale della colonna
    inferiore, sta tra colonna e mozzo, esce dal retro del bulbo fino al tirante."""
    hexh = Polygon([(4.8 * np.cos(t), 4.8 * np.sin(t)) for t in np.radians(np.arange(0, 360, 60))])
    plate = unary_union([circ((0, 0), 7.5), bar2d((0, 0), (0, -L.Lv), 9.0), circ((0, -L.Lv), BOSS_R)])
    plate = plate.difference(circ((0, 0), M3_FREE / 2))
    m = ext_xy(plate, *L.z_lev)
    boss = ext_xy(circ((0, -L.Lv), BOSS_R), L.z_lboss, L.z_lev[0] + 0.01)
    m = union([m, boss])
    return diff(m, [ext_xy(hexh, L.z_lev[0] - 0.1, L.z_lev[0] + 2.2),
                    ext_xy(circ((0, -L.Lv), M3_TAP / 2), L.z_lboss - 1, L.z_lev[1] - 1.0)])


def x_crank(L):
    """Manovella del servo X (sulla squadretta, sotto al servo capovolto)."""
    plate = unary_union([circ((0, 0), 8.0), bar2d((0, 0), (0, -L.Lv), 9.0), circ((0, -L.Lv), BOSS_R)])
    plate = plate.difference(circ((0, 0), 2.8))
    m = union([ext_xy(plate, *L.z_lev), ext_xy(circ((0, -L.Lv), BOSS_R), L.z_lboss, L.z_lev[0] + 0.01)])
    return diff(m, [ext_xy(circ((0, -L.Lv), M3_TAP / 2), L.z_lboss - 1, L.z_lev[1] - 1.0)])


def tie_bar(L):
    xs = (-L.xe, 0.0, L.xe)
    y = -L.Lv
    poly = unary_union([bar2d((-L.xe, y), (L.xe, y), 9.0)] + [circ((x, y), BOSS_R) for x in xs])
    poly = poly.difference(unary_union([circ((x, y), M3_FREE / 2) for x in xs]))
    return ext_xy(poly, *L.z_tie)


def core(L):
    """Telaio centrale: sede servo X (capovolto), boss dei perni Y, traversa, dita con
    mozzi al centro dei bulbi, leva Y che pende sotto il perno (lato +x)."""
    z0, z1 = SLAB
    xe = L.xe
    yb = (-(SG_L - SG_SHAFT) - SG_CLEAR, SG_SHAFT + SG_CLEAR)       # finestra corpo servo
    yc = (yb[0] + yb[1]) / 2
    poly = unary_union([
        Polygon([(-L.core_x, yc - 18.5), (L.core_x, yc - 18.5), (L.core_x, yc + 18.5), (-L.core_x, yc + 18.5)]),
        bar2d((0, yc - 15), (0, L.bar_front - 1), 12.0),
        Polygon([(-xe - 5, L.bar_back), (xe + 5, L.bar_back), (xe + 5, L.bar_front), (-xe - 5, L.bar_front)]),
    ] + [bar2d((s * xe, L.bar_front + 1), (s * xe, 0), 10.0) for s in (-1, 1)]
      + [circ((s * xe, 0), HUB_R) for s in (-1, 1)])
    poly = poly.buffer(1.5, resolution=8).buffer(-1.5, resolution=8)
    m = ext_xy(poly, z0, z1)
    # leva Y: piastra verticale (piano YZ) che pende dal Core fino al perno Q
    q = L.pitch["Q0"]
    lev = unary_union([bar2d((0, 0), q, 10.0), circ(q, BOSS_R + 0.5)])
    lev = lev.difference(circ(q, M3_TAP / 2))
    m = union([m, ext_yz(lev, *L.ylev_x)])
    holes = [
        box((-SG_W / 2 - SG_CLEAR, SG_W / 2 + SG_CLEAR), yb, (z0 - 1, z1 + 1)),
        # asole cavo alle due testate
        box((-3, 3), (yb[0] - 3, yb[1] + 3), (z0 - 1, z1 + 1)),
    ]
    for s in (-1, 1):
        holes.append(cyl(M2_TAP / 2, (0, yc + s * SG_EAR_HOLES / 2, z1 - 8), (0, yc + s * SG_EAR_HOLES / 2, z1 + 1), 16))
        holes.append(cyl(M3_TAP / 2, (s * (SG_W / 2 + SG_CLEAR + 0.6), 0, 0), (s * (L.core_x + 1), 0, 0), 24))
        holes.append(cyl(M3_FREE / 2 + 0.05, (s * xe, 0, z0 - 1), (s * xe, 0, z1 + 1), 24))
    # spazio di rotazione squadretta + manovella X sotto al servo (settore +-(YAW_MAX+15))
    sweep = sector2d(HORN_LEN + 2, -90 - YAW_MAX - 15, -90 + YAW_MAX + 15).union(circ((0, 0), 8.5))
    case_top = L.x_bottom - SG_H
    holes.append(ext_xy(sweep, z0 - 1, case_top + 0.3))
    return diff(m, holes)


def lid(L, kind):
    """Palpebra (occhio dx, coordinate di montaggio): calotta sferica a spicchio + due
    orecchie (interna ed esterna) con anello sul boss del montante; l'orecchia esterna
    porta l'attacco del tirante (filettato M3)."""
    xe = L.xe
    if kind == "up":
        (r0, r1), (a0, a1), lay = L.RU, (LID_UP_OPEN, LID_UP_REAR), L.L2
    else:
        (r0, r1), (a0, a1), lay = L.RL, (LID_LO_REAR, LID_LO_OPEN), L.L1
    shell = diff(sphere(r1, (xe, 0, 0)), [sphere(r0, (xe, 0, 0))])
    wedge = ext_yz(sector2d(r1 + 5, a0, a1), xe - r1 - 1, xe + r1 + 1)
    shell = inter(shell, wedge)
    d = L.lid[kind]
    lug = d["A0"]
    parts = [shell]
    for side in (-1, 1):
        x0, x1 = (xe + side * lay[0], xe + side * lay[1]) if side > 0 else (xe - lay[1], xe - lay[0])
        # raggio a cui la calotta attraversa il piano dell'orecchia (lato bulbo)
        dx = lay[0]
        rr = np.sqrt(max(r1 ** 2 - dx ** 2, 1.0))
        fan = sector2d(rr + 1.0, a0 + 4, a1 - 4).union(circ((0, 0), 8.0))
        if side > 0:
            fan = fan.union(bar2d((0, 0), lug, 9.0)).union(circ(lug, BOSS_R))
        fan = fan.difference(circ((0, 0), 5.2))
        parts.append(ext_yz(fan, x0, x1))
        # raccordo orecchia-calotta (riempie lo spicchio tra calotta e orecchia)
        cx0, cx1 = (xe + r0 * 0.6, x1) if side > 0 else (x0, xe - r0 * 0.6)
        link = inter(sphere(r1, (xe, 0, 0)), ext_yz(sector2d(r1 + 2, a0 + 4, a1 - 4).difference(circ((0, 0), 8.0)), cx0, cx1))
        link = diff(link, [sphere(r0, (xe, 0, 0))])
        parts.append(link)
    # boss dell'attacco tirante, verso l'interno (filetto lungo)
    bx1 = xe + lay[0] + 0.01
    bx0 = xe + L.L1[0] - 4.0 if kind == "lo" else xe + L.L1[0]
    parts.append(ext_yz(circ(lug, BOSS_R), bx0, bx1))
    m = union(parts)
    m = diff(m, [ext_yz(circ(lug, M3_TAP / 2), bx0 - 1, xe + lay[1] + 1)])
    # niente dentro la sfera del bulbo; foro degli anelli lungo tutto l'asse
    cuts = [sphere(r0, (xe, 0, 0)), cyl(5.2, (xe - r1 - 2, 0, 0), (xe + r1 + 2, 0, 0), 64)]
    if kind == "up":   # la calotta sup. passa nello strato L1: lascia girare gli anelli della inf.
        for sd in (-1, 1):
            cuts.append(cyl(8.6, (xe + sd * (L.L1[0] - 0.5), 0, 0), (xe + sd * (L.L2[0] - 0.01), 0, 0), 64))
    m = diff(m, cuts)
    return m


def lid_link(L, kind):
    """Tirante palpebra (occhio dx): dall'attacco sulla palpebra al perno della manovella."""
    d = L.lid[kind]
    A0 = d["A0"]
    P0 = lid_pin(L, -L.lid_servo)          # posa modellata = palpebre aperte
    lay = L.L3 if kind == "up" else L.L2
    poly = unary_union([bar2d(A0, P0, LINK_W), circ(A0, BOSS_R), circ(P0, BOSS_R)])
    # tirante sup.: due fori passanti; tirante inf.: la vite del perno manovella si avvita qui
    poly = poly.difference(circ(A0, M3_FREE / 2)).difference(
        circ(P0, (M3_FREE if kind == "up" else M3_TAP) / 2))
    return ext_yz(poly, L.xe + lay[0], L.xe + lay[1])


def lid_crank(L):
    """Manovella palpebre (occhio dx), avvitata sulla squadretta SG90; perno verso l'alto
    a meta' corsa, linguetta squadretta verso il retro. Posa modellata: palpebre aperte."""
    S = L.ls
    poly = unary_union([circ(S, 7.5), bar2d(S, S + (0, LID_CRANK_R), 9.0), circ(S + (0, LID_CRANK_R), BOSS_R),
                        bar2d(S, S + (-16, 0), 8.0)])
    poly = poly.difference(circ(S, 2.8)).difference(circ(S + (0, LID_CRANK_R), M3_FREE / 2))
    m = ext_yz(poly, L.xe + L.L4[0], L.xe + L.L4[1])
    return moved(m, rot_x(L.lid_servo, (0, *S)))     # ruota a -L.lid_servo (perno indietro)


def y_crank(L):
    S = L.ys
    poly = unary_union([circ(S, 7.5), bar2d(S, S + (0, max(L.ry, 16.0)), 9.0), circ(S + (0, L.ry), BOSS_R)])
    poly = poly.difference(circ(S, 2.8)).difference(circ(S + (0, L.ry), M3_TAP / 2))
    return ext_yz(poly, *L.ycrank_x)


def y_link(L):
    Q0 = L.pitch["Q0"]
    C0 = L.ys + (0, L.ry)
    poly = unary_union([bar2d(Q0, C0, 8.0), circ(Q0, BOSS_R), circ(C0, BOSS_R)])
    poly = poly.difference(circ(Q0, M3_FREE / 2)).difference(circ(C0, M3_FREE / 2))
    return ext_yz(poly, *L.ylink_x)


def outer_post(L):
    """Montante esterno (occhio dx), avvitato alla base: boss Ø10 su cui girano gli
    anelli esterni delle palpebre."""
    xe, zb = L.xe, L.z_base
    x0, x1 = xe + L.L4[0], xe + L.L4[0] + POST_T - 1.0
    prof = unary_union([Polygon([(-7, zb), (7, zb), (7, 0), (-7, 0)]), circ((0, 0), 8.0)])
    plate = ext_yz(prof, x0, x1)
    foot = box((x0 - 9, x1), (-14, 14), (zb, zb + 4))
    boss = cyl(5.0, (xe + L.L1[0] + 0.3, 0, 0), (x0 + 0.1, 0, 0))
    m = union([plate, foot, boss])
    holes = [cyl(M3_TAP / 2, (x0 - 4.5, s * 9.5, zb - 1), (x0 - 4.5, s * 9.5, zb + 3), 16) for s in (-1, 1)]
    return diff(m, holes)


def sg90_cradle(origin, ex, ey, t=3.0):
    """Sede SG90: piastra sotto le orecchie con finestra per il corpo + 2 fori M2.
    Locale: albero = asse z (verso la squadretta), z = 0 fondo servo, ex = corpo
    dall'albero verso l'estremita' lontana."""
    ex, ey = np.asarray(ex, float), np.asarray(ey, float)
    T = np.eye(4)
    T[:3, 0], T[:3, 1], T[:3, 2], T[:3, 3] = ex, ey, np.cross(ex, ey), origin
    xm = SG_L / 2 - SG_SHAFT
    e0 = SG_EAR_Z[0]
    plate = box((xm - SG_EAR_SPAN / 2 - 3, xm + SG_EAR_SPAN / 2 + 3), (-SG_W / 2 - 3, SG_W / 2 + 3), (e0 - t, e0))
    win = box((-SG_SHAFT - SG_CLEAR - 2.5, SG_L - SG_SHAFT + SG_CLEAR + 2.5), (-SG_W / 2 - SG_CLEAR, SG_W / 2 + SG_CLEAR),
              (e0 - t - 1, e0 + 1))
    holes = [win] + [cyl(M2_TAP / 2, (xm + s * SG_EAR_HOLES / 2, 0, e0 - t - 1), (xm + s * SG_EAR_HOLES / 2, 0, e0 + 1), 16)
                     for s in (-1, 1)]
    m = diff(plate, holes)
    m.apply_transform(T)
    return m, T


def sg90_body(T, extra=0.0):
    """Ingombro servo (corpo + orecchie + albero) per le verifiche."""
    xm = SG_L / 2 - SG_SHAFT
    b = union([box((-SG_SHAFT, SG_L - SG_SHAFT), (-SG_W / 2, SG_W / 2), (-extra, SG_H)),
               box((xm - SG_EAR_SPAN / 2, xm + SG_EAR_SPAN / 2), (-SG_W / 2, SG_W / 2), SG_EAR_Z),
               cyl(3.0, (0, 0, SG_H - 0.1), (0, 0, HORN_H - 1.6), 24)])
    return moved(b, T)


def servo_frames(L):
    """Frame locali (z = albero verso la squadretta, z=0 fondo) dei 4 servo."""
    xe = L.xe
    fr = {}
    # X: capovolto nel Core, albero verso -z, corpo verso -y
    fr["X"] = (np.array([0, 0, L.x_bottom]), [0, -1, 0], [-1, 0, 0])
    # Y: albero verso +x, corpo verso -y
    fr["Y"] = (np.array([L.ycrank_x[0] - L.horn_h, *L.ys]), [0, 1, 0], [0, 0, 1])
    # palpebre dx: albero verso +x
    fr["LID_R"] = (np.array([xe + L.L4[0] - L.horn_h, *L.ls]), [0, -1, 0], [0, 0, -1])
    fr["LID_L"] = (np.array([-(xe + L.L4[0] - L.horn_h), *L.ls]), [0, -1, 0], [0, 0, 1])
    out = {}
    for k, (o, ex, ey) in fr.items():
        ex, ey = np.asarray(ex, float), np.asarray(ey, float)
        T = np.eye(4)
        T[:3, 0], T[:3, 1], T[:3, 2], T[:3, 3] = ex, ey, np.cross(ex, ey), o
        out[k] = T
    return out


def central_post(L, side):
    """Montante centrale (integrato nella base): boss Ø10 con le orecchie interne delle
    palpebre; dentro passa la vite M3 x 12 che fa da perno al Core (testa incassata)."""
    s = side
    x0, x1 = L.cpost
    boss_end = L.xe - L.E
    prof = unary_union([Polygon([(-7, L.z_base), (7, L.z_base), (7, 0), (-7, 0)]), circ((0, 0), 8.0)])
    m = ext_yz(prof, x0, x1)
    m = union([m, cyl(5.0, (x1 - 0.1, 0, 0), (boss_end - 0.3, 0, 0))])
    seat = boss_end - 0.3 - HEAD_H - 2.0
    m = diff(m, [cyl(M3_FREE / 2, (x0 - 1, 0, 0), (boss_end + 1, 0, 0), 24),
                 cyl(HEAD_D / 2 + 0.2, (seat, 0, 0), (boss_end + 1, 0, 0), 32)])
    return m if s > 0 else mirror_x(m, 0.0), seat


def base(L, frames):
    """Piastra di base con montanti centrali, sedi dei servo Y e palpebre, attacchi
    dei montanti esterni, fori di fissaggio nella testa."""
    xe, zb = L.xe, L.z_base
    # la base finisce sotto il montante esterno (il piede vi appoggia; il montante sporge di 3 mm):
    # cosi' la D85 sta in un pezzo su un piatto da 256 mm (Bambu A1/P1)
    xw = xe + L.L4[0] + 1.0
    y0 = L.ls[0] - SG_L + SG_SHAFT - 8.0
    y1 = max(16.0, L.ys[0] + SG_L - SG_SHAFT + 6.0)
    plate = box((-xw, xw), (y0, y1), (zb - L.base_t, zb))
    parts = [plate]
    for s in (-1, 1):
        parts.append(central_post(L, s)[0])
    # sedi servo: piastra sotto le orecchie + colonna fino alla base
    for k in ("Y", "LID_R", "LID_L"):
        c, T = sg90_cradle(frames[k][:3, 3], frames[k][:3, 0], frames[k][:3, 1])
        lo, hi = c.bounds
        parts.append(c)
        parts.append(diff(box((lo[0], hi[0]), (lo[1], hi[1]), (zb - 0.5, lo[2] + 0.5)),
                          [sg90_body(T, extra=5.0)]))
    m = union(parts)
    holes = []
    for s in (-1, 1):
        x0 = s * (xe + L.L4[0] - 4.5)
        holes += [cyl(M3_FREE / 2, (x0, t * 9.5, zb - L.base_t - 1), (x0, t * 9.5, zb + 1), 16) for t in (-1, 1)]
        # fori di fissaggio M4 agli angoli
        for yy in (y0 + 7, y1 - 7):
            holes.append(cyl(2.2, (s * (xw - 7), yy, zb - L.base_t - 1), (s * (xw - 7), yy, zb + 1), 24))
    # passaggi cavi
    holes.append(box((-6, 6), (L.ys[0] - 4, L.ys[0] + 4), (zb - L.base_t - 1, zb + 0.5)))
    holes += [sg90_body(frames[k]) for k in ("Y", "LID_R", "LID_L")]
    return diff(m, holes), (y0, y1, xw)


def split_base(L, B, dims):
    """Divide la base in due meta' (taglio a x = 0) + due piastrine di giunzione."""
    y0, y1, xw = dims
    zb, t = L.z_base, L.base_t
    halves = []
    for s in (-1, 1):
        h = inter(B, box((min(0, s * (xw + 5)), max(0, s * (xw + 5))), (y0 - 5, y1 + 5), (zb - t - 5, 80)))
        halves.append(h)
    holes = []
    pads = []
    for yy in ((y0 + 6, y0 + 30), (y1 - 12, y1 - 3)):
        for xx in (-9, 9):
            for py in yy:
                holes.append(cyl(M3_FREE / 2, (xx, py, zb - t - 10), (xx, py, zb + 1), 16))
        pads.append(box((-15, 15), (min(yy) - 5, max(yy) + 5), (zb - 2 * t, zb - t)))
    halves = [diff(h, holes) for h in halves]
    splice = diff(pads[0], holes)
    splice2 = diff(pads[1], holes)
    return halves, [splice, splice2]


# ======================================================================================
# assieme e verifiche
# ======================================================================================
def build_parts(L):
    P = {}
    eye, screws = eyeball(L)
    lev = yaw_lever(L)
    for s, n in ((1, "R"), (-1, "L")):
        P[f"eye_{n}"] = moved(eye, trimesh.transformations.translation_matrix([s * L.xe, 0, 0]))
        P[f"lever_{n}"] = moved(lev, trimesh.transformations.translation_matrix([s * L.xe, 0, 0]))
    P["core"] = core(L)
    P["xcrank"] = x_crank(L)
    P["tiebar"] = tie_bar(L)
    for kind in ("up", "lo"):
        m = lid(L, kind)
        P[f"lid_{kind}_R"], P[f"lid_{kind}_L"] = m, mirror_x(m, 0.0)
        k = lid_link(L, kind)
        P[f"link_{kind}_R"], P[f"link_{kind}_L"] = k, mirror_x(k, 0.0)
    c = lid_crank(L)
    P["lidcrank_R"], P["lidcrank_L"] = c, mirror_x(c, 0.0)
    P["ycrank"] = y_crank(L)
    P["ylink"] = y_link(L)
    op = outer_post(L)
    P["opost_R"], P["opost_L"] = op, mirror_x(op, 0.0)
    frames = servo_frames(L)
    B, dims = base(L, frames)
    P["base"] = B
    P["_dims"] = dims
    P["_screws"] = screws
    P["_frames"] = frames
    return P


def pose_transforms(L, a=0.0, phi=0.0, th_L=None, th_R=None):
    """Trasformazioni (rispetto alla posa modellata) di tutti i pezzi mobili.
    a = su/giu' (+ = guarda in alto), phi = sx/dx (+ = verso sinistra, antiorario visto
    dall'alto), th = angolo servo palpebre (-L.lid_servo aperte, +L.lid_servo chiuse)."""
    th_L = -L.lid_servo if th_L is None else th_L
    th_R = -L.lid_servo if th_R is None else th_R
    T = {}
    Rc = rot_x(a)
    T["core"] = Rc
    for s, n in ((1, "R"), (-1, "L")):
        T[f"eye_{n}"] = Rc @ rot_z(phi, (s * L.xe, 0, 0))
        T[f"lever_{n}"] = T[f"eye_{n}"]
    T["xcrank"] = Rc @ rot_z(phi)
    v = rot2(np.array([0.0, -L.Lv]), phi)
    T["tiebar"] = Rc @ trimesh.transformations.translation_matrix([v[0], v[1] + L.Lv, 0])
    for n, th in (("R", th_R), ("L", th_L)):
        for kind in ("up", "lo"):
            psi = lid_angle(L, kind, th)
            T[f"lid_{kind}_{n}"] = rot_x(psi)
            A0 = L.lid[kind]["A0"]
            T[f"link_{kind}_{n}"] = planar_T(A0, lid_pin(L, -L.lid_servo), rot2(A0, psi), lid_pin(L, th))
        T[f"lidcrank_{n}"] = rot_x(-(th + L.lid_servo), (0, *L.ls))
    b = y_servo_angle(L, a)
    T["ycrank"] = rot_x(-b, (0, *L.ys))
    Q = rot2(L.pitch["Q0"], a)
    T["ylink"] = planar_T(L.pitch["Q0"], L.ys + (0, L.ry), Q, y_crank_pin(L, b))
    T["_servoX"] = Rc
    return T


def obstacles(L, frames):
    """Corpi dei servo (fissi, tranne X che segue il Core)."""
    return {f"servo_{k}": sg90_body(T) for k, T in frames.items()}


def check(L, P, verbose=True):
    import manifold3d as mf

    def to_mf(m):
        return mf.Manifold(mesh=mf.Mesh(vert_properties=np.asarray(m.vertices, np.float32),
                                        tri_verts=np.asarray(m.faces, np.uint32)))

    bodies = {k: v for k, v in P.items() if not k.startswith("_")}
    bodies.update(obstacles(L, P["_frames"]))
    MF = {k: to_mf(v) for k, v in bodies.items()}
    # coppie che si toccano per progetto (viti/perni, appoggi)
    skip = {frozenset(p) for p in [("eye_R", "lever_R"), ("eye_L", "lever_L"),
                                   ("core", "servo_X"), ("xcrank", "servo_X"),
                                   ("base", "servo_Y"), ("base", "servo_LID_R"), ("base", "servo_LID_L"),
                                   ("base", "opost_R"), ("base", "opost_L"),
                                   ("ycrank", "servo_Y"), ("lidcrank_R", "servo_LID_R"), ("lidcrank_L", "servo_LID_L")]}
    poses = []
    for a in (-PITCH_MAX, 0.0, PITCH_MAX):
        for phi in (-YAW_MAX, 0.0, YAW_MAX):
            for th in (-L.lid_servo, 0.0, L.lid_servo):
                poses.append((a, phi, th, -th))
    worst = {}
    for (a, phi, thL, thR) in poses:
        T = pose_transforms(L, a, phi, thL, thR)
        T["servo_X"] = T["_servoX"]
        cur = {}
        for k, m in MF.items():
            M = T.get(k)
            cur[k] = m.transform(M[:3, :].astype(np.float64)) if M is not None else m
        bb = {k: np.array(v.bounding_box()).reshape(2, 3) if hasattr(v, "bounding_box") else None for k, v in cur.items()}
        keys = sorted(cur)
        for i, ka in enumerate(keys):
            for kb in keys[i + 1:]:
                if frozenset((ka, kb)) in skip:
                    continue
                A, B = bb[ka], bb[kb]
                if np.any(A[1] < B[0]) or np.any(B[1] < A[0]):
                    continue
                vol = (cur[ka] ^ cur[kb]).volume()
                if vol > 0.5:
                    key = (ka, kb)
                    if vol > worst.get(key, (0,))[0]:
                        worst[key] = (vol, (a, phi, thL, thR))
    if verbose:
        if worst:
            print("  INTERFERENZE:")
            for (ka, kb), (vol, pose) in sorted(worst.items(), key=lambda t: -t[1][0]):
                print(f"    {ka:12s} x {kb:12s} {vol:8.1f} mm3  posa (su/giu, sx/dx, th_L, th_R) = {pose}")
        else:
            print(f"  nessuna interferenza su {len(poses)} pose")
    return worst


def bbox_of(m):
    return np.array(m.bounds)


def lay_flat(m, T):
    m = moved(m, T)
    m.apply_translation(-m.bounds[0] * np.array([1, 1, 1]) + [0, 0, 0])
    return m


def export(L, P, od, bed):
    od.mkdir(parents=True, exist_ok=True)
    for f in od.glob("*.stl"):
        f.unlink()
    tag = f"D{L.D:g}".replace(".", "p")
    R_up = rot_x(90)                            # +y -> +z
    files = {
        f"Eyeball_{tag}_x2": lay_flat(P["eye_R"], R_up),
        f"YawLever_{tag}_x2": lay_flat(P["lever_R"], rot_x(180)),
        f"Core_{tag}": lay_flat(P["core"], rot_x(180)),
        f"XCrank_{tag}": lay_flat(P["xcrank"], rot_x(180)),
        f"TieBar_{tag}": lay_flat(P["tiebar"], np.eye(4)),
        f"LidLink_Upper_{tag}_x2": lay_flat(P["link_up_R"], rot_y(-90)),
        f"LidLink_Lower_{tag}_x2": lay_flat(P["link_lo_R"], rot_y(-90)),
        f"LidCrank_{tag}_x2": lay_flat(P["lidcrank_R"], rot_y(-90)),
        f"YCrank_{tag}": lay_flat(P["ycrank"], rot_y(-90)),
        f"YLink_{tag}": lay_flat(P["ylink"], rot_y(-90)),
        f"OuterPost_{tag}_x2": lay_flat(P["opost_R"], rot_y(90)),
    }
    # palpebre "a cupola": bordi sul piatto, superficie esterna senza supporti
    for kind, (e0, e1) in (("up", (LID_UP_OPEN, LID_UP_REAR)), ("lo", (LID_LO_REAR, LID_LO_OPEN))):
        ang = 90.0 - (e0 + e1) / 2
        for n in ("L", "R"):
            files[f"Eyelid_{'Upper' if kind == 'up' else 'Lower'}_{n}_{tag}"] = lay_flat(P[f"lid_{kind}_{n}"], rot_x(ang))
    width = P["base"].extents[0]
    files[f"Base_{tag}"] = lay_flat(P["base"], np.eye(4))
    if width > bed:
        halves, splices = split_base(L, P["base"], P["_dims"])
        files[f"Base_L_{tag}"] = lay_flat(halves[0], np.eye(4))
        files[f"Base_R_{tag}"] = lay_flat(halves[1], np.eye(4))
        files[f"BaseSplice_Rear_{tag}"] = lay_flat(splices[0], np.eye(4))
        files[f"BaseSplice_Front_{tag}"] = lay_flat(splices[1], np.eye(4))
    for n, m in files.items():
        m.export(od / f"{n}.stl")
    return files, width


def fit_test(od):
    """Provino della sede SG90 (stessa geometria delle sedi nella base)."""
    c, T = sg90_cradle((0, 0, 0), (1, 0, 0), (0, 1, 0))
    lo, hi = c.bounds
    m = union([c, diff(box((lo[0], hi[0]), (lo[1], hi[1]), (lo[2] - 12, lo[2] + 0.5)), [sg90_body(T, extra=20)])])
    m = diff(m, [sg90_body(T, extra=20)])
    m.apply_translation(-m.bounds[0])
    m.export(od / "SG90_FitTest.stl")


def report(L, P, files, width, od, worst):
    lid = L.lid
    pa = [y_servo_angle(L, a) for a in (-PITCH_MAX, 0, PITCH_MAX)]
    la = {k: [lid_angle(L, k, t) for t in (-L.lid_servo, 0, L.lid_servo)] for k in ("up", "lo")}
    cpost_seat = central_post(L, 1)[1]
    pitch_screw = std_len(cpost_seat - (SG_W / 2 + SG_CLEAR + 0.5))
    info = {
        "diametro_bulbo_mm": L.D,
        "interasse_occhi_mm": round(L.P, 1),
        "ingombro_base_XxY_mm": f"{width:.0f} x {P['base'].extents[1]:.0f}",
        "servo": "4 x SG90 o MG90S: X (nel Core), Y (base), palpebre sx, palpebre dx",
        "corsa_sx_dx": f"+-{YAW_MAX:g} deg (servo X +-{YAW_MAX:g} deg, parallelogramma 1:1)",
        "corsa_su_giu": f"+-{PITCH_MAX:g} deg (servo Y {pa[0]:+.0f} / {pa[2]:+.0f} deg)",
        "palpebre": (f"servo -{L.lid_servo:g} (aperte) .. +{L.lid_servo:g} (chiuse): sup. {la['up'][0]:+.0f} -> "
                     f"{la['up'][2]:+.0f} deg, inf. {la['lo'][0]:+.0f} -> {la['lo'][2]:+.0f} deg"),
        "attacco_palpebra_sup": f"r = {lid['up']['r']:.1f} mm a {lid['up']['a']:.0f} deg, tirante {lid['up']['l']:.1f} mm",
        "attacco_palpebra_inf": f"r = {lid['lo']['r']:.1f} mm a {lid['lo']['a']:.0f} deg, tirante {lid['lo']['l']:.1f} mm",
        "leve_X_mm": round(L.Lv, 1),
        "leva_Y_mm": round(abs(L.q_z), 1),
        "manovella_Y_mm": L.ry,
        "manovella_palpebre_mm": LID_CRANK_R,
        "viti_perno_bulbo": f"4 x M3 x {P['_screws']['top']} (2 per bulbo, testa incassata ai poli)",
        "viti_perno_Core": f"2 x M3 x {pitch_screw} (dal boss del montante centrale nel Core)",
        "viti_tirante_X": "3 x M3 x 8 dal basso (avvitate negli occhielli di leve e manovella; non piu' lunghe)",
        "viti_tiranti_palpebre": "per occhio 3 x M3 x 10: manovella+tiranti (avvitata nel tirante inf.), "
                                 "tirante sup. -> palpebra sup., tirante inf. -> palpebra inf. (avvitate nelle palpebre)",
        "viti_leva_Y": "2 x M3 x 6 (una avvitata nella leva del Core, una nella manovella Y)",
        "viti_montanti_esterni": "4 x M3 x 8 dal basso",
        "viti_servo": "8 x M2 autofilettanti (in dotazione ai servo)",
        "fissaggio_manovelle": "sulla squadretta a un braccio: forare Ø1.5 attraverso i fori della squadretta, 2 viti M2",
        "horn_h_mm": L.horn_h,
        "interferenze_rilevate": "nessuna" if not worst else f"{len(worst)} coppie (vedi output script)",
    }
    (od / "info.txt").write_text("\n".join(f"{a}: {b}" for a, b in info.items()), encoding="utf8")
    for n, m in sorted(files.items()):
        print(f"  {n:34s} wt={m.is_watertight!s:5s} ext={np.round(m.extents, 1)}")
    for a, b in info.items():
        print(f"  {a}: {b}")


# ======================================================================================
def render(L, P, path, poses):
    """Viste assonometriche: proiezione ortografica con ordinamento globale dei triangoli."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection

    col = {"eye": "#f2efe6", "lever": "#6c8ebf", "core": "#5b7db1", "xcrank": "#d79b00", "tiebar": "#d79b00",
           "lid": "#7aa874", "link": "#c0504d", "lidcrank": "#c0504d", "ycrank": "#8e44ad", "ylink": "#8e44ad",
           "opost": "#999999", "base": "#c8c8c8", "servo": "#2b5797"}
    nc = 2
    nr = (len(poses) + 1) // 2
    fig, axs = plt.subplots(nr, nc, figsize=(9 * nc, 6.5 * nr))
    for ax, (title, pose, (el, az)) in zip(np.ravel(axs), poses):
        T = pose_transforms(L, *pose)
        T["servo_X"] = T["_servoX"]
        bodies = {k: v for k, v in P.items() if not k.startswith("_")}
        bodies.update(obstacles(L, P["_frames"]))
        # camera: az = 180 vista frontale, 0 vista da dietro; el = elevazione
        V = rot_x(-90 + el)[:3, :3] @ rot_z(-az)[:3, :3]
        light = np.array([0.4, 0.5, 0.75])
        light /= np.linalg.norm(light)
        tris, cs, ds = [], [], []
        for k, m in bodies.items():
            m = moved(m, T[k]) if k in T else m
            if len(m.faces) > 40000 or (len(m.faces) > 12000 and not k.startswith(("eye", "lid_"))):
                m = m.simplify_quadric_decimation(face_count=40000 if k.startswith(("eye", "lid_")) else 12000)
            v = m.vertices @ V.T
            n = m.face_normals @ V.T
            vis = n[:, 2] > -0.05
            t = v[m.faces][vis]
            sh = 0.35 + 0.65 * np.clip(n[vis] @ light, 0, 1)
            c = np.tile(np.array(matplotlib.colors.to_rgb(col[k.split("_")[0]])), (len(m.faces), 1))
            if k.startswith("eye_"):
                # iride e pupilla colorate (nel modello sono solo incise), per vedere lo sguardo
                ctr = bodies[k].triangles_center - [L.xe if k.endswith("R") else -L.xe, 0, 0]
                if len(ctr) != len(m.faces):
                    ctr = (moved(m, np.linalg.inv(T[k])).triangles_center - [L.xe if k.endswith("R") else -L.xe, 0, 0])
                rr = np.hypot(ctr[:, 0], ctr[:, 2])
                front = (ctr[:, 1] > 0) & (np.linalg.norm(ctr, axis=1) > L.R - 1.0)
                c[front & (rr < 0.42 * L.R)] = matplotlib.colors.to_rgb("#c8961e")
                pup = (ctr[:, 1] > 0.8 * L.R) & ((ctr[:, 0] / (0.075 * L.R)) ** 2 + (ctr[:, 2] / (0.30 * L.R)) ** 2 < 1)
                c[pup] = (0.05, 0.05, 0.05)
            tris.append(t[:, :, :2])
            cs.append(np.clip(c[vis] * sh[:, None], 0, 1))
            ds.append(t[:, :, 2].mean(1))
        tris, cs, ds = np.concatenate(tris), np.concatenate(cs), np.concatenate(ds)
        o = np.argsort(ds)
        ax.add_collection(PolyCollection(tris[o], facecolors=cs[o], edgecolors=cs[o], linewidths=0.45))
        ax.autoscale()
        ax.set_aspect("equal")
        ax.set_axis_off()
        ax.set_title(title, fontsize=14)
    for ax in np.ravel(axs)[len(poses):]:
        ax.set_axis_off()
    plt.tight_layout()
    fig.savefig(path, dpi=80)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sizes", nargs="*", type=float, help="diametri bulbo in mm")
    ap.add_argument("--cm", type=float, nargs="*", default=[])
    ap.add_argument("--plus", type=float, nargs="*", default=[], help="cm in piu' rispetto a 8.5 cm")
    ap.add_argument("--horn-h", type=float, default=HORN_H)
    ap.add_argument("--bed", type=float, default=250.0)
    ap.add_argument("--no-check", action="store_true")
    ap.add_argument("--render", action="store_true")
    a = ap.parse_args()
    sizes = list(a.sizes) + [10 * c for c in a.cm] + [D_BASE + 10 * p for p in a.plus]
    sizes = sizes or [D_BASE]
    for D in sizes:
        if D < 65:
            print(f"!! D = {D} mm: sotto i ~65 mm il servo X non sta piu' tra i bulbi; risultato non garantito")
        L = Layout(D, a.horn_h)
        tag = f"D{D:g}".replace(".", "p")
        print(f"== ibrido EyeMech + MorganManly {tag}")
        P = build_parts(L)
        od = OUT / tag
        files, width = export(L, P, od, a.bed)
        fit_test(OUT)
        worst = {} if a.no_check else check(L, P)
        report(L, P, files, width, od, worst)
        if a.render:
            IMG.mkdir(parents=True, exist_ok=True)
            render(L, P, IMG / f"hybrid_{tag}.png",
                   [("riposo", (0, 0, -L.lid_servo, -L.lid_servo), (20, 210)),
                    ("su + sinistra, palpebre aperte", (PITCH_MAX, YAW_MAX, -L.lid_servo, -L.lid_servo), (8, 180)),
                    ("giu' + destra, occhiolino", (-PITCH_MAX, -YAW_MAX, -L.lid_servo, L.lid_servo), (8, 180)),
                    ("retro, palpebre chiuse", (0, 0, L.lid_servo, L.lid_servo), (35, -30))])


if __name__ == "__main__":
    main()
