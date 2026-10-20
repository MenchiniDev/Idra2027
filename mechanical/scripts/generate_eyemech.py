"""
EyeMech e3.2 (Will Cogley) ingrandito a bulbo D85, con palpebre a UN servo per occhio.

Parte dai pezzi ORIGINALI di Will (file "EyeMech e3.2 SG90 - A.3mf", versione print-in-place
con sedi SG90 lettera A) e li ingrandisce tutti dello stesso fattore s = 85/32: bulbi, base
con gli incastri, supporti a L, telaio centrale, palpebre e tiranti.
Gli incastri a scatto ingranditi lavorano con la stessa deformazione degli originali.

Cambia solo cio' che non puo' essere ingrandito o che riguarda le palpebre:
  * i servo restano SG90/MG90S veri (1:1) e le loro sedi sono 1:1: nella base (Y, palpebre sx
    e dx) e nel telaio X (XAxisA) la sede ingrandita di Will e' riempita e dentro c'e' la sede
    del servo vero, albero sullo stesso asse, orecchie su un piano con 2 viti M2. I fermi di
    Will non servono piu';
  * le squadrette di Will (palpebre, X, Y) hanno il mozzo rifatto: un codolo che scende fino
    allo scanalato del servo vero, con sede 1:1 e vite M2;
  * palpebre: Will usa 2 servo per occhio. Qui resta solo il servo ANTERIORE (quello della
    palpebra superiore, tirante corto originale). Sulla sua squadretta c'e' un secondo
    braccio con perno, e un tirante nuovo ("LinkB") porta il moto all'orecchia della
    palpebra inferiore. Braccio e tirante sono ottimizzati perche' la palpebra inferiore
    faccia la stessa corsa, speculare, di quella superiore (errore < 1.5 deg). Il servo
    posteriore, la sua squadretta e il tirante lungo spariscono. Totale 4 servo: X, Y,
    palpebre sx, palpebre dx;
  * la base ingrandita (386 x 252 mm) e' divisa in due meta' unite da chiavette a coda di
    rondine, per stare su un piatto da 256 mm.

Licenza dei pezzi di partenza: CC BY-NC-SA 4.0 (Will Cogley / NM Robotics).

Versione di prova (--small): gli stessi pezzi nella scala di Will (bulbo 32 mm, occhi a 75 mm):
sedi dei servo, squadrette, base e fermi sono quelli originali di Will; cambiano solo le palpebre
(1 servo per occhio, secondo braccio + tirante B, con quote ridotte e viti M2). Serve a provare
il meccanismo delle palpebre prima di stampare la D85.

Uso:  python generate_eyemech.py                  (D85: interasse occhi 200 mm -> bulbo 85.3 mm)
      python generate_eyemech.py --small          (versione di prova, scala di Will)
      python generate_eyemech.py --interasse 0 --d 90   (scala dal diametro del bulbo)
      python generate_eyemech.py --render         (immagine in docs/img)
Uscita in mechanical/eyes/eyemech_D85 (+ print_A1 con i piatti dei pezzi grandi) o
mechanical/eyes/idra_version (file idra_version_*.stl).
"""
import argparse
import re
import sys
import zipfile
from pathlib import Path

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[2]
SRC3MF = (ROOT / "mechanical" / "eyes" / "original" / "eyemech_e3.2" / "src" / "3D Prints"
          / "EyeMech e3.2 SG90 - A.3mf")
OUTROOT = ROOT / "mechanical" / "eyes"
IMG = ROOT / "docs" / "img"

D_WILL = 32.0                    # bulbo originale di Will

# --- SG90 / MG90S veri (1:1). Stime da datasheet: VERIFICARE col calibro -------------
SG_L, SG_W, SG_H = 22.8, 12.4, 22.7   # corpo: lunghezza, larghezza, fondo -> faccia superiore
SG_SHAFT = 6.0                         # asse albero -> estremita' vicina del corpo
SG_EAR = (15.9, 18.4)                  # orecchie: faccia inferiore / superiore (dal fondo)
SG_EAR_SPAN = 32.6                     # lunghezza orecchia-orecchia
SG_EAR_HOLES = 27.8                    # interasse fori orecchie
SG_BOSS_TOP = 4.3                      # faccia superiore -> cima del mozzo ingranaggi
SG_SPLINE_TOP = 7.3                    # faccia superiore -> cima dello scanalato
SPLINE_D = 4.75                        # sede scanalato (forzata sui denti, come Will)
SPLINE_DEPTH = 3.0
WILL_HORN_FACE = 5.1                   # faccia superiore servo -> squadretta, nel modello di Will

CL = 0.25                              # gioco per lato dei pezzi nuovi

# --- geometria ricostruita dell'assieme originale (1:1, mm) -------------------------
# assi: x = destra, y = avanti negativo (gli occhi guardano verso -y), z = alto
EYE_X = 37.5
E = np.array([-67.7, 11.2])        # asse palpebre/su-giu' nel piano (y, z)
F = np.array([-22.2, 11.2])        # albero servo palpebre ANTERIORE (resta)
BK = np.array([7.7, 11.2])         # albero servo palpebre POSTERIORE (eliminato)

# cinematica ottimizzata del secondo braccio (vedi docs/mechanical_eyes.md), unita' 1:1
ARM_B_R, ARM_B_PSI, LINK_B_L = 13.174, 58.759, 39.321


# =====================================================================================
# utilita'
# =====================================================================================
def U(ms):
    ms = [m for m in ms if m is not None and len(m.faces)]
    return trimesh.boolean.union(ms, engine="manifold") if len(ms) > 1 else ms[0].copy()


def D(a, bs):
    bs = [b for b in bs if b is not None and len(b.faces)]
    return trimesh.boolean.difference([a] + bs, engine="manifold") if bs else a.copy()


def I(a, b):
    return trimesh.boolean.intersection([a, b], engine="manifold")


def vol_inter(a, b):
    try:
        r = I(a, b)
        return 0.0 if r is None or r.is_empty else float(r.volume)
    except Exception:
        return 0.0


def Tm(t=(0, 0, 0), fx=1, fy=1, fz=1):
    M = np.diag([fx, fy, fz, 1.0])
    M[:3, 3] = t
    return M


def Rx(a_deg, c_yz=(0, 0)):
    a = np.radians(a_deg)
    c, s = np.cos(a), np.sin(a)
    M = np.eye(4)
    M[1:3, 1:3] = [[c, -s], [s, c]]
    C = np.eye(4); C[1:3, 3] = c_yz
    Ci = np.eye(4); Ci[1:3, 3] = -np.asarray(c_yz)
    return C @ M @ Ci


def tf(m, M):
    m = m.copy()
    m.apply_transform(M)
    return m


def cyl_x(r, x0, x1, y, z, n=96):
    c = trimesh.creation.cylinder(radius=r, height=abs(x1 - x0), sections=n)
    c.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0]))
    c.apply_translation([(x0 + x1) / 2, y, z])
    return c


def cyl_axis(r, p0, p1, n=96):
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    v = p1 - p0
    c = trimesh.creation.cylinder(radius=r, height=np.linalg.norm(v), sections=n)
    c.apply_transform(trimesh.geometry.align_vectors([0, 0, 1], v / np.linalg.norm(v)))
    c.apply_translation((p0 + p1) / 2)
    return c


def box(lo, hi):
    lo, hi = np.asarray(lo, float), np.asarray(hi, float)
    b = trimesh.creation.box(extents=hi - lo)
    b.apply_translation((lo + hi) / 2)
    return b


def hull(ms):
    return trimesh.util.concatenate(ms).convex_hull


def ang(v):
    return np.degrees(np.arctan2(v[1], v[0]))


def pol(c, r, a_deg):
    a = np.radians(a_deg)
    return np.asarray(c) + r * np.array([np.cos(a), np.sin(a)])


# =====================================================================================
# 1. lettura dei pezzi originali dal 3MF di Will
# =====================================================================================
def read_3mf(path):
    """{oggetto: {volume: mesh}} nel sistema dell'oggetto (posa di stampa)."""
    z = zipfile.ZipFile(path)
    main = z.read("3D/3dmodel.model").decode()
    ms = z.read("Metadata/model_settings.config").decode()
    pname, oname = {}, {}
    for m in re.finditer(r'<object id="(\d+)">(.*?)</object>', ms, re.S):
        oname[m.group(1)] = re.search(r'key="name" value="([^"]*)"', m.group(2)).group(1)
        for p in re.finditer(r'<part id="(\d+)"[^>]*>(.*?)</part>', m.group(2), re.S):
            pname[p.group(1)] = re.search(r'key="name" value="([^"]*)"', p.group(2)).group(1)
    cache, out = {}, {}
    for m in re.finditer(r'<object id="(\d+)"[^>]*>\s*<components>(.*?)</components>', main, re.S):
        oid = m.group(1)
        vols = {}
        for c in re.finditer(r'p:path="([^"]+)" objectid="(\d+)"[^>]*transform="([^"]+)"', m.group(2)):
            path, sub, t = c.groups()
            if path not in cache:
                cache[path] = z.read(path.lstrip("/")).decode()
            xml = cache[path]
            i = xml.find(f'<object id="{sub}"')
            s = xml[i:xml.find("</object>", i)]
            v = np.array(re.findall(r'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"', s), float)
            f = np.array(re.findall(r'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"', s), int)
            a = np.array(t.split(), float).reshape(4, 3)
            M = np.eye(4); M[:3, :3] = a[:3].T; M[:3, 3] = a[3]
            mesh = trimesh.Trimesh(v, f, process=True)
            mesh.apply_transform(M)
            key = pname.get(sub, sub)
            k, n = key, 2
            while k in vols:
                k = f"{key}_{n}"; n += 1
            vols[k] = mesh
        out[oid] = (oname.get(oid, oid), vols)
    return out


def item_rotations(path=SRC3MF):
    """rotazioni di stampa scelte da Will (item di build del 3MF), per oggetto."""
    main = zipfile.ZipFile(path).read("3D/3dmodel.model").decode()
    rot = {}
    for m in re.finditer(r'<item objectid="(\d+)"[^>]*transform="([^"]+)"', main):
        a = np.array(m.group(2).split(), float).reshape(4, 3)
        R = np.eye(4)
        R[:3, :3] = np.round(a[:3].T, 6)
        rot[m.group(1)] = R
    return rot


# pezzo esportato -> oggetto di Will da cui prende l'orientamento di stampa
PRINT_ROT = {"Retainer_Single": "4", "Retainer_Double_A": "6", "Retainer_Double_B": "8",
             "PivotCentral_x2": "10", "PivotOuter_L": "12", "PivotOuter_R": "14",
             "Eyeball_x2": "22", "CoreY_PIP": "28", "XAxisA_PIP": "47", "XAxisB_PIP": "52",
             "LidTop_R_PIP": "36", "LidTop_L_PIP": "44", "LidBottom_R": "32", "LidBottom_L": "40"}


def will_parts():
    raw = read_3mf(SRC3MF)
    P = {oid: vols for oid, (_, vols) in raw.items()}
    W = {
        "base": P["2"]["SnapEyemech v20"],
        "ret_single": P["4"]["SnapEyemech v20"],
        "ret_double_1": P["6"]["SnapEyemech v20"],
        "ret_double_2": P["8"]["SnapEyemech v20"],
        "cpiv_1": P["10"]["Base"], "cpiv_2": P["16"]["Base"],          # supporti centrali
        "opiv_L": P["12"]["Base_1"], "opiv_R": P["14"]["Base_2"],      # supporti esterni
        "eye_1": P["22"]["Component74"], "eye_2": P["24"]["Component74"],
        "core": P["28"],                    # telaio Y: EyeCorePivotHolder + PivotLarge + VerticalHorn
        "xA": P["47"],                      # asse X, sottogruppo A
        "xB": P["52"],                      # asse X, sottogruppo B (CentralServoHorn)
        "lidTop_L": P["44"], "lidBot_L": P["40"],   # AA, AB
        "lidTop_R": P["36"], "lidBot_R": P["32"],   # AC, AD
    }
    return W


# =====================================================================================
# 2. assieme originale ricostruito (posizioni nella base, 1:1)
# =====================================================================================
LID = {  # perno palpebra, scanalato squadretta, giunto squadretta, orecchia, centro x lid
    "top": dict(piv=(-16.65, -10.39), spl=(28.65, -6.39), jnt=(28.65, 6.66), ear=(-14.02, 6.65)),
    "bot": dict(piv=(-31.65, 10.52), spl=(43.65, 6.52), jnt=(43.65, -6.53), ear=(-29.02, -6.51)),
}
# posizione in x dei gruppi palpebra (centro bulbo -> x di stampa = 0 meno questo scarto).
# Superiore: squadretta in linea con la fessura del servo; inferiore: anello esterno libero dal
# supporto esterno; tra le due 0.32 mm (0.24 nelle pose di Will): anelli affiancati sul perno.
LID_DX_TOP, LID_DX_BOT = 1.30, 0.98
LID_XC = {"lidTop_L": (-EYE_X, LID_DX_TOP), "lidBot_L": (-EYE_X, LID_DX_BOT),
          "lidTop_R": (EYE_X, -LID_DX_TOP), "lidBot_R": (EYE_X, -LID_DX_BOT)}


def lid_group_M(name):
    """posa di stampa del gruppo palpebra -> assieme, con l'albero sul servo giusto."""
    kind = "top" if "Top" in name else "bot"
    g = LID[kind]
    xc, lx = LID_XC[name]
    piv, spl = np.array(g["piv"]), np.array(g["spl"])
    M = Tm([xc - lx, E[0] - piv[0], E[1] - piv[1]])
    s_ = spl + E - piv
    shaft = F if kind == "top" else BK
    a = ang(shaft - E) - ang(s_ - E)
    return Rx(a, E) @ M


def place_static():
    """trasformazioni posa di stampa -> assieme per le parti fisse."""
    return {
        "base": np.eye(4),
        "cpiv_1": Tm([13.55, -40.6, 0.6]), "cpiv_2": Tm([-13.55, -40.6, 0.6]),
        "opiv_R": Tm([58.55, -40.6, 0.6]), "opiv_L": Tm([-58.55, -40.6, 0.6]),
        "eye_1": Tm([EYE_X, E[0] - 4.35, E[1]]), "eye_2": Tm([-EYE_X, E[0] - 4.35, E[1]]),
    }


# gruppi X/Y (print-in-place, posa neutra) nell'assieme, 1:1. Ricavati dai vincoli:
#  * CoreY: perni (asse y -18.23, z -13.655 nel gruppo) sull'asse E dei supporti centrali;
#  * XAxisA: anelli degli occhi (y -6.05) sotto i centri dei bulbi; in z il servo X sta dentro
#    il box del CoreY con la faccia superiore quasi a filo del bordo (come nella guida di Will):
#    quota cercata in modo che il telaio laterale di XAxisB passi sopra il box (gli incastri
#    a scatto CoreY/XAxisA restano a contatto, come devono);
#  * XAxisB: mozzo della CentralServoHorn (y -11.5, faccia z 2.0) sull'albero del servo X,
#    5.1 sopra la faccia superiore del servo.
# Verifica (check_xy): in posa neutra niente tocca, tranne gli incastri voluti.
# Con questa posa il mozzo della VerticalHorn cade a y -22.4, z 11.2: sull'albero del servo Y.
X_SHAFT_Y = 10.65 - SG_SHAFT - 0.75   # albero servo X in XAxisA: corpo 0.75 dal lato +y della finestra
CORE_T = np.array([0.0, E[0] + 18.23, E[1] + 13.655])
XA_T = np.array([0.0, E[0] + 6.05, CORE_T[2] - 22.0 - (4.8 + 2.5) + 6.25])
XB_T = np.array([0.0, XA_T[1] + X_SHAFT_Y + 11.5, XA_T[2] + 4.8 + 6.8 + 5.1 - 2.0])


# =====================================================================================
# 3. cinematica palpebre (piano y-z, unita' 1:1)
# =====================================================================================
def fourbar(S, horn_deg, r_h, L, r_e, guess):
    J = pol(S, r_h, horn_deg)
    d = np.linalg.norm(J - E)
    if d > L + r_e or d < abs(L - r_e):
        return None
    a = (r_e ** 2 - L ** 2 + d ** 2) / (2 * d)
    hh = np.sqrt(max(r_e ** 2 - a ** 2, 0))
    u = (J - E) / d
    perp = np.array([-u[1], u[0]])
    sols = [E + a * u + hh * perp, E + a * u - hh * perp]
    angs = [ang(s - E) for s in sols]
    k = np.argmin([abs((x - guess + 180) % 360 - 180) for x in angs])
    return angs[k]


class LidKin:
    """posizioni dei giunti per il lato destro, nella posa di riferimento (dphi = 0)."""

    def __init__(self):
        MA, MD = lid_group_M("lidTop_R"), lid_group_M("lidBot_R")
        t2 = lambda M, p: (M @ np.array([0, p[0], p[1], 1.0]))[1:3]
        self.JA = t2(MA, LID["top"]["jnt"]); self.PA = t2(MA, LID["top"]["ear"])
        self.JD = t2(MD, LID["bot"]["jnt"]); self.PD = t2(MD, LID["bot"]["ear"])
        self.h = np.linalg.norm(self.JA - F)
        self.LA = np.linalg.norm(self.PA - self.JA)
        self.rA = np.linalg.norm(self.PA - E)
        self.rD = np.linalg.norm(self.PD - E)
        self.hornA0 = ang(self.JA - F)
        self.earA0 = ang(self.PA - E)
        self.earD0 = ang(self.PD - E)

    def top(self, dphi):
        return fourbar(F, self.hornA0 + dphi, self.h, self.LA, self.rA, self.earA0) - self.earA0

    def bot(self, dphi):
        return fourbar(F, self.hornA0 + ARM_B_PSI + dphi, ARM_B_R, LINK_B_L, self.rD,
                       self.earD0) - self.earD0

    def JB(self, dphi=0.0):
        return pol(F, ARM_B_R, self.hornA0 + ARM_B_PSI + dphi)

    def PB(self, dphi=0.0):
        return pol(E, self.rD, self.earD0 + self.bot(dphi))


# posa chiusa / aperta del servo anteriore (dphi rispetto alla posa di stampa di Will).
# Rx positivo porta in basso il bordo anteriore: dphi > 0 chiude. Chiuse = bordi a ~0 deg,
# aperte = 80 deg di servo dopo (come nel codice di Will), bordi a circa +-60 deg.
DPHI_CLOSED, DPHI_OPEN = 34.0, -46.0


# =====================================================================================
# 4. pezzi nuovi
# =====================================================================================
def sg90_real(c=0.0):
    """SG90/MG90S vero (1:1) per verifiche e immagini. Locale come servo_seat: origine
    sull'asse nel piano della faccia superiore, x = corpo, z = albero."""
    rx0, rx1 = -SG_SHAFT, SG_L - SG_SHAFT
    rcx = (rx0 + rx1) / 2
    body = box([rx0 - c, -SG_W / 2 - c, -SG_H], [rx1 + c, SG_W / 2 + c, 0])
    ears = box([rcx - SG_EAR_SPAN / 2, -SG_W / 2, -SG_H + SG_EAR[0]],
               [rcx + SG_EAR_SPAN / 2, SG_W / 2, -SG_H + SG_EAR[1]])
    tower = cyl_axis(5.9, [0, 0, -0.1], [0, 0, SG_BOSS_TOP], n=48)       # mozzo ingranaggi
    spline = cyl_axis(2.3, [0, 0, SG_BOSS_TOP - 0.1], [0, 0, SG_SPLINE_TOP], n=32)
    return U([body, ears, tower, spline])


def servo_frame(shaft_pt, shaft_dir, body_dir, top):
    """locale servo -> pezzo: origine sull'asse albero nel piano della faccia superiore,
    x = dall'albero verso il corpo, z = albero (fondo -> squadretta). top = quota della faccia
    superiore lungo l'albero (la stessa per il servo ingrandito di Will e per quello vero)."""
    ez = np.asarray(shaft_dir, float); ex = np.asarray(body_dir, float)
    M = np.eye(4)
    M[:3, 0], M[:3, 2], M[:3, 1] = ex, ez, np.cross(ez, ex)
    M[:3, 3] = np.asarray(shaft_pt, float) + ez * (top - np.dot(shaft_pt, ez))
    return M


def servo_seat(part, Mtop, s, plugs=(), zmin=None, sweep=40.0, depth=None, wall=None, open_side=0):
    """sede 1:1 per SG90/MG90S vero dentro la sede ingrandita di Will.
    Mtop: locale servo -> pezzo con l'origine sull'asse, nel piano della faccia SUPERIORE
    (z locale = albero). Si riempie il volume del SG90 ingrandito (che era vuoto per costruzione)
    fino al piano d'appoggio delle orecchie del servo vero, poi si scava la sede 1:1:
      * tunnel del corpo (aperto sul fondo, cavo che esce in fondo al corpo),
      * appoggio piano per le orecchie + 2 fori M2 autofilettanti,
      * via d'ingresso: tutto libero sopra il piano orecchie, lungo l'albero.
    plugs: mesh (nel sistema del pezzo) che chiudono fessure di Will da riempire;
    zmin: il riempimento non scende sotto questa quota (fondo del pezzo, piano di stampa);
    depth: il riempimento si ferma a questa distanza sotto il piano orecchie (None = tutto);
    wall: scala originale (s = 1), dove la sede ingrandita coincide col servo e non lascia pareti:
    il blocco e' una scatola attorno al servo vero, spessa wall su ogni lato tranne open_side
    (-1/+1 = lato y locale senza parete: dietro il servo passa il telaio laterale di XAxisB)."""
    c = CL
    T = lambda m: tf(m, Mtop)
    Hs = s * SG_H                                    # fondo SG90 ingrandito a z = -Hs
    ear = -SG_H + SG_EAR[0]                          # piano d'appoggio orecchie (servo vero)
    xb0, xb1 = -s * SG_SHAFT, s * (SG_L - SG_SHAFT)   # corpo ingrandito lungo x
    hw = s * SG_W / 2 - 0.2
    # solo il corpo ingrandito (+1 dentro il fondo tasca): le fessure delle orecchie le chiudono
    # i plugs, l'orecchia ingrandita superiore non serve
    if wall is None:
        body = box([xb0 + 0.2, -hw, -Hs], [xb1 + 1.0, hw, 0])
    else:
        body = box([-SG_SHAFT - c - wall, -SG_W / 2 - c - (0 if open_side < 0 else wall),
                    ear - (SG_H - SG_EAR[0]) - wall],
                   [SG_L - SG_SHAFT + c + wall, SG_W / 2 + c + (0 if open_side > 0 else wall), 0])
    fill = U([T(body)] + list(plugs))
    keep = T(box([-500, -500, -Hs - 500 if depth is None else ear - depth], [500, 500, ear]))
    fill = I(fill, keep)
    if zmin is not None:
        fill = I(fill, box([-1e4, -1e4, zmin], [1e4, 1e4, 1e4]))
    # servo vero (1:1)
    rx0, rx1 = -SG_SHAFT, SG_L - SG_SHAFT
    rcx = (rx0 + rx1) / 2
    tunnel = box([rx0 - c, -SG_W / 2 - c, -Hs - 2], [rx1 + c, SG_W / 2 + c, ear + 0.01])
    cable = box([rx1 - 1, -4.0, -Hs - 2], [rx1 + 4.5, 4.0, -SG_H + 5.0])
    free = box([rcx - SG_EAR_SPAN / 2 - 0.6, -SG_W / 2 - 0.6, ear],      # orecchie, sopra: libero
               [rcx + SG_EAR_SPAN / 2 + 0.6, SG_W / 2 + 0.6, sweep])
    holes = [cyl_axis(0.85, [rcx + sx * SG_EAR_HOLES / 2, 0, ear - 9],
                      [rcx + sx * SG_EAR_HOLES / 2, 0, ear + 0.5], n=24) for sx in (-1, 1)]
    return D(U([part, fill]), [T(tunnel), T(cable), T(free)] + [T(h) for h in holes])


def hub_boss(axis_pt, axis_dir, face_offset_out, s):
    """codolo del mozzo per una squadretta ingrandita.
    axis_pt: punto sull'asse sulla faccia lato servo della squadretta (assieme scalato);
    axis_dir: versore dal servo verso la squadretta; face_offset_out: spessore squadretta.
    Ritorna (da_unire, da_togliere)."""
    a = np.asarray(axis_dir, float) / np.linalg.norm(axis_dir)
    p = np.asarray(axis_pt, float)
    # quota della faccia squadretta sopra la faccia superiore del servo
    horn_above_top = s * WILL_HORN_FACE
    boss_bottom = SG_BOSS_TOP + 0.6                     # sopra la cima del mozzo ingranaggi
    Lb = horn_above_top - boss_bottom
    pb = p - a * Lb                                      # fondo del codolo
    add = [cyl_axis(5.0, pb, p + a * 0.5)]
    # riempi la vecchia sede ingrandita e il controforo
    fill = cyl_axis(s * 2.6, p - a * 0.01, p + a * (face_offset_out + 0.01))
    cut = [cyl_axis(SPLINE_D / 2, pb - a * 0.5, pb + a * SPLINE_DEPTH, n=48),
           cyl_axis(1.15, pb - a, p + a * (face_offset_out + 1), n=24),           # vite M2
           cyl_axis(2.4, p + a * (face_offset_out - 3.0), p + a * (face_offset_out + 1), n=48)]
    return [fill] + add, cut, Lb


def find_hub(horn):
    """asse della squadretta di Will: (centro sulla faccia lato servo, versore servo->squadretta,
    spessore). La sede dello scanalato (r ~2.46) e' aperta verso il servo."""
    ext = horn.extents
    ax = int(np.argmin(ext))
    lo, hi = horn.bounds[0, ax], horn.bounds[1, ax]
    idx = [k for k in range(3) if k != ax]

    def circles_at(v):
        n = np.zeros(3); n[ax] = 1
        o = np.zeros(3); o[ax] = v
        sec = horn.section(plane_origin=o, plane_normal=n)
        res = []
        if sec is None:
            return res
        for e in sec.discrete:
            p = e[:, idx]
            if len(p) < 8:
                continue
            A = np.c_[2 * p, np.ones(len(p))]
            c = np.linalg.lstsq(A, (p ** 2).sum(1), rcond=None)[0]
            r = np.sqrt(c[2] + c[0] ** 2 + c[1] ** 2)
            if np.abs(np.linalg.norm(p - c[:2], axis=1) - r).max() < 0.15:
                res.append((c[:2], r))
        return res

    for side, v in (("lo", lo + 0.25), ("hi", hi - 0.25)):
        for c, r in circles_at(v):
            if 2.3 < r < 2.6:
                centre = np.zeros(3); centre[idx] = c
                d = np.zeros(3)
                if side == "lo":
                    centre[ax] = lo; d[ax] = 1
                else:
                    centre[ax] = hi; d[ax] = -1
                return centre, d, hi - lo
    raise RuntimeError("mozzo non trovato")


def rehub(horn_s, s, centre1, dir_, thick1):
    """squadretta gia' scalata di s -> mozzo per servo vero."""
    add, cut, _ = hub_boss(centre1 * s, dir_, thick1 * s, s)
    return D(U([horn_s] + add), cut)


def mirror_x_mesh(m):
    m = m.copy()
    m.apply_transform(np.diag([-1, 1, 1, 1.0]))
    if m.volume < 0:
        m.invert()
    return m


def flat_link(m):
    """tirante con le facce piane parallele al piatto (asse x del tirante -> z)."""
    m = m.copy()
    m.apply_transform(trimesh.transformations.rotation_matrix(-np.pi / 2, [0, 1, 0]))
    m.apply_translation(-m.bounds[0])
    return m


# =====================================================================================
# 5. costruzione
# =====================================================================================
JOG = (12.0, 22.0)  # tratto obliquo del tirante B, lungo il tirante (unita' 1:1)

# quote assolute (mm) dei pezzi nuovi (secondo braccio, perno B, tirante B, orecchia della
# palpebra inferiore). D85: viti M3. Piccola (scala di Will, bulbo 32): circa 3/8, viti M2.
DIM = {
    "D85": dict(PIN_R=6.0,        # perno sul secondo braccio
                EAR_R=7.0,        # perno sull'orecchia della palpebra inferiore (cilindrico)
                LINK_T=9.5,       # spessore tirante B
                BAR_R=6.5,        # mezza larghezza tirante B
                RING=5.5,         # parete anelli tirante B
                SPIGOT_R=4.0, SPIGOT_L=5.0,    # codolo del perno B nel braccio della squadretta
                FLANGE_R=11.0, FLANGE_T=3.0,   # testa del perno B (trattiene il tirante)
                WASHER_R=11.0, WASHER_T=2.5,
                CLR=0.25,                      # gioco per lato perni/anelli
                GAP_O=0.6, GAP_R=0.3, GAP_P=0.4,   # giochi assiali: braccio, orecchia, testa
                EAR_IN=3.0, EAR_SCREW=12.0,    # perno orecchia: affondamento, foro vite
                R_FREE=1.7, R_TAP=1.25, R_HEAD=3.1, HEAD_D=2.0,
                PIN_SCREW="M3x20", EAR_SCREW_TXT="M3x10"),
    "small": dict(PIN_R=2.5, EAR_R=2.8, LINK_T=3.6, BAR_R=2.6, RING=1.6,
                  SPIGOT_R=1.9, SPIGOT_L=2.5, FLANGE_R=4.4, FLANGE_T=1.2,
                  WASHER_R=4.4, WASHER_T=1.2,
                  CLR=0.2, GAP_O=0.4, GAP_R=0.3, GAP_P=0.3,
                  EAR_IN=1.2, EAR_SCREW=5.0,
                  R_FREE=1.15, R_TAP=0.8, R_HEAD=2.1, HEAD_D=1.0,
                  PIN_SCREW="M2x8", EAR_SCREW_TXT="M2x5"),
}


def pin_b(hx1, xo1, JB, P):
    """perno B in assieme: codolo nel braccio, fusto per l'anello del tirante, testa."""
    x_sh = xo1 + P["GAP_P"]                            # fine fusto (gioco assiale)
    xf = x_sh + P["FLANGE_T"]
    m = U([cyl_x(P["SPIGOT_R"], hx1 - P["SPIGOT_L"] + 0.3, hx1 + 0.01, *JB),
           cyl_x(P["PIN_R"], hx1, x_sh, *JB),
           cyl_x(P["FLANGE_R"], x_sh, xf, *JB)])
    # foro passante + sede testa (la vite si filetta nel braccio della squadretta)
    return D(m, [cyl_x(P["R_FREE"], hx1 - P["SPIGOT_L"] - 1, xf + 1, *JB, n=24),
                 cyl_x(P["R_HEAD"], xf - P["HEAD_D"], xf + 1, *JB, n=32)])


def build(dia=85.0, small=False):
    """small=True: versione di prova in scala di Will (s = 1): sedi dei servo, squadrette,
    base e fermi restano i suoi; cambiano solo le palpebre (1 servo per occhio)."""
    s = dia / D_WILL
    P = DIM["small" if small else "D85"]
    S = np.diag([s, s, s, 1.0])
    Si = np.linalg.inv(S)
    W = will_parts()
    kin = LidKin()
    out = {}          # nome -> mesh o {nome: mesh} (posa di stampa, scalata)
    asm = {}          # nome -> mesh nell'assieme scalato (per verifiche e immagini)

    def sc(m):
        return tf(m, S)

    # ---------------- parti solo ingrandite ----------------
    out["PivotOuter_L"] = sc(W["opiv_L"])
    out["PivotOuter_R"] = sc(W["opiv_R"])
    out["PivotCentral_x2"] = sc(W["cpiv_1"])
    out["Eyeball_x2"] = sc(W["eye_1"])
    st = place_static()
    for k in ("base", "cpiv_1", "cpiv_2", "opiv_R", "opiv_L", "eye_1", "eye_2"):
        asm[k] = tf(W[k], S @ st[k])

    # ---------------- gruppi X/Y: solo mozzi delle squadrette (se ingrandite) ----------------
    core = {k: sc(v) for k, v in W["core"].items()}
    xb = {k: sc(v) for k, v in W["xB"].items()}
    if not small:
        c1, d1, t1 = find_hub(W["core"]["VerticalHorn"])
        core["VerticalHorn"] = rehub(core["VerticalHorn"], s, c1, d1, t1)
        c1, d1, t1 = find_hub(W["xB"]["CentralServoHorn"])
        xb["CentralServoHorn"] = rehub(xb["CentralServoHorn"], s, c1, d1, t1)
    out["CoreY_PIP"] = core
    out["XAxisA_PIP"] = {k: sc(v) for k, v in W["xA"].items()}
    out["XAxisB_PIP"] = xb

    # ---------------- palpebre: lato destro, il sinistro e' speculare ----------------
    MA = lid_group_M("lidTop_R")
    MD = lid_group_M("lidBot_R")
    gA = {k: tf(v, S @ MA) for k, v in W["lidTop_R"].items()}
    hornA, linkA, lidT = gA["4xTopLidHorn"], gA["PivotLarge"], gA["LidBR"]
    hx0, hx1 = hornA.bounds[:, 0]
    Fs = s * F

    c1, d1, t1 = find_hub(W["lidTop_R"]["4xTopLidHorn"])
    cA = (MA @ np.r_[c1, 1.0])[:3]
    if not small:
        hornA = rehub(hornA, s, cA, MA[:3, :3] @ d1, t1)

    # secondo braccio con perno, sullo stesso piano della squadretta
    JB = s * kin.JB(0.0)
    near_JA = linkA.vertices[np.linalg.norm(linkA.vertices[:, 1:] - JB, axis=1) < s * 8]
    armx0 = max(hx0, (near_JA[:, 0].max() if len(near_JA) else hx0) + 0.8)
    arm = hull([cyl_x(s * 4.0, armx0, hx1, *Fs), cyl_x(s * 4.0, armx0, hx1, *JB)])
    xo0, xo1 = hx1 + P["GAP_O"], hx1 + P["GAP_O"] + P["LINK_T"]
    # sede del perno B (pezzo a parte: nella posa di stampa di Will la faccia esterna della
    # squadretta e' sul piatto). Codolo nel braccio + foro da filettare, vite dall'esterno.
    hornA = U([hornA, arm])
    sl = P["SPIGOT_L"]
    hornA = D(hornA, [cyl_x(P["SPIGOT_R"] + 0.1, hx1 - sl, hx1 + 1, *JB),
                      cyl_x(P["R_TAP"], hx1 - 1.8 * sl, hx1, *JB, n=24)])
    pinB = pin_b(hx1, xo1, JB, P)

    # palpebra inferiore nella posa dphi = 0: perno dell'orecchia cilindrico + vite
    MDb = Rx(kin.bot(0.0), E) @ MD
    gD = {k: tf(v, S @ MDb) for k, v in W["lidBot_R"].items()}
    lidB, ring_old = gD["LidTR"], gD["2xBottomLidLever"]
    PB = s * kin.PB(0.0)
    near = ring_old.vertices[np.linalg.norm(ring_old.vertices[:, 1:] - PB, axis=1) < s * 6.0]
    xe0 = near[:, 0].min()
    xr0, xr1 = xe0 + P["GAP_R"], xe0 + P["GAP_R"] + P["LINK_T"]
    lidB = D(lidB, [cyl_x(s * 3.9, xe0 - 0.05, xe0 + s * 8, *PB)])
    lidB = U([lidB, cyl_x(P["EAR_R"], xe0 - P["EAR_IN"], xr1 + 0.5, *PB)])
    lidB = D(lidB, [cyl_x(P["R_TAP"], xr1 + 0.5 - P["EAR_SCREW"], xr1 + 2, *PB, n=24)])

    # tirante B: anello sul perno del braccio (strato esterno), tratto obliquo, anello sull'orecchia
    u = (PB - JB) / np.linalg.norm(PB - JB)
    Q1, Q2 = JB + u * (JOG[0] * s), JB + u * (JOG[1] * s)
    br, pr, er, cl, rg = P["BAR_R"], P["PIN_R"], P["EAR_R"], P["CLR"], P["RING"]
    linkB = U([hull([cyl_x(br, xo0, xo1, *JB), cyl_x(br, xo0, xo1, *Q1)]),
               hull([cyl_x(br, xo0, xo1, *Q1), cyl_x(br, xr0, xr1, *Q2)]),
               hull([cyl_x(br, xr0, xr1, *Q2), cyl_x(br, xr0, xr1, *PB)]),
               cyl_x(pr + cl + rg, xo0, xo1, *JB), cyl_x(er + cl + rg, xr0, xr1, *PB)])
    linkB = D(linkB, [cyl_x(pr + cl, xo0 - 1, xo1 + 1, *JB),
                      cyl_x(er + cl, xr0 - 1, xr1 + 1, *PB)])

    washer = D(trimesh.creation.cylinder(radius=P["WASHER_R"], height=P["WASHER_T"], sections=64),
               [trimesh.creation.cylinder(radius=P["R_FREE"], height=4, sections=24)])

    # ritorno alle pose di stampa di Will (scalate)
    backA = S @ np.linalg.inv(MA) @ Si
    backD = S @ np.linalg.inv(MDb) @ Si
    grpR = {"LidTop": tf(lidT, backA), "LinkA": tf(linkA, backA), "HornLid": tf(hornA, backA)}
    out["LidTop_R_PIP"] = grpR
    out["LidTop_L_PIP"] = {k: mirror_x_mesh(v) for k, v in grpR.items()}
    out["LidBottom_R"] = tf(lidB, backD)
    out["LidBottom_L"] = mirror_x_mesh(out["LidBottom_R"])
    out["LinkB_R"] = flat_link(linkB)
    out["LinkB_L"] = mirror_x_mesh(out["LinkB_R"])
    out["Washer_x2"] = washer
    pb = pinB.copy()
    pb.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0]))  # testa sul piatto
    out["PinB_x2"] = pb
    asm.update({"lidTop_R": lidT, "linkA_R": linkA, "hornA_R": hornA, "lidBot_R": lidB,
                "linkB_R": linkB, "pinB_R": pinB})

    # ---------------- sedi 1:1 dei servo veri ----------------
    # Ogni servo vero ha l'albero sull'asse di quello ingrandito e la faccia superiore alla
    # stessa quota (i mozzi delle squadrette sono fatti cosi'). Il resto della sede ingrandita
    # di Will viene riempito. Quote 1:1 delle sedi di Will (base: fessure orecchie e fondi tasca;
    # telaio X: finestra 12.8 x 25.6, corpo contro il lato +y, orecchie sulla faccia z = 4.8).
    top_lid = hx0 - s * WILL_HORN_FACE                    # faccia superiore servo palpebre (x)
    cY = find_hub(W["core"]["VerticalHorn"])[0] + CORE_T   # mozzo squadretta Y nell'assieme (1:1)
    seats = {
        # palpebre: in piedi, albero verso l'esterno, corpo verso il basso, albero sul mozzo della
        # squadretta (= F; le fessure di Will darebbero 0.25 mm 1:1 piu' in basso e indietro)
        "LID_R": servo_frame([0, *(s * cA[1:])], [1, 0, 0], [0, 0, -1], top_lid),
        "LID_L": servo_frame([0, *(s * cA[1:])], [-1, 0, 0], [0, 0, -1], top_lid),
        # Y: in piedi al centro, albero verso -x sul mozzo della VerticalHorn (CoreY in posa)
        "Y": servo_frame([0, *(s * cY[1:])], [-1, 0, 0], [0, 0, -1],
                         -s * (cY[0] + WILL_HORN_FACE)),
        # X: nel telaio di XAxisA, albero in su, corpo verso -y (cavo nella tacca a -y); la
        # finestra (25.6) e' piu' lunga del corpo: 0.75 dal lato +y, cosi' il telaio laterale di
        # XAxisB passa dietro le orecchie dei servo palpebre
        "X": servo_frame([0, s * X_SHAFT_Y, 0], [0, 0, 1], [0, -1, 0], s * (4.8 + SG_H - SG_EAR[0])),
    }
    asm["servo_R"] = tf(sg90_real(), seats["LID_R"])
    asm["servo_Y"] = tf(sg90_real(), seats["Y"])
    asm["servo_X"] = tf(sg90_real(), Tm(s * XA_T) @ seats["X"])
    for g, T in (("CoreY_PIP", CORE_T), ("XAxisB_PIP", XB_T)):
        for k, m in out[g].items():
            asm[f"{g}:{k}"] = tf(m, Tm(s * T))
    base = sc(W["base"])
    def s1(lo, hi, g=0.3):      # tappo: quote 1:1 scalate, allargato di g nel piano (si fonde ai bordi)
        lo, hi = s * np.asarray(lo, float), s * np.asarray(hi, float)
        return box(lo - [g, g, 0], hi + [g, g, 0])
    bz0 = W["base"].bounds[0, 2]
    plugs = {"LID_R": [s1([43.8, -28.71, bz0], [46.6, -16.21, -3.15])],
             "LID_L": [s1([-46.6, -28.71, bz0], [-43.8, -16.21, -3.15])],
             "Y": [s1([-4.55, -28.86, bz0], [-1.65, -16.06, -3.15])]}
    # base ridotta: serve solo a tenere i supporti a L (fessure y -32.6..-12.4) e i 3 servo.
    # Si tiene la striscia y -38..-8 (1:1); via il resto (sedi dei servo posteriori, porta-PCB,
    # blocchi rialzati dietro le sedi palpebre).
    base = I(base, box([-1e4, s * BASE_Y[0], -1e4], [1e4, s * BASE_Y[1], 1e4]))
    base = D(base, [box([s * x0, s * -16.4, s * -3.15 + 0.01], [s * x1, s * BASE_Y[1] + 1, 1e3])
                    for x0, x1 in ((-56.0, -17.0), (17.0, 56.0))])
    for k in ("LID_R", "LID_L", "Y"):
        base = servo_seat(base, seats[k], s, plugs[k], zmin=s * bz0, depth=SEAT_DEPTH,
                          wall=SEAT_WALL if small else None, open_side=-1 if k == "LID_R" else 1)
    # scarti staccati dal taglio (pezzetti d'angolo): si tiene solo il corpo principale
    parts = base.split(only_watertight=False)
    if len(parts) > 1:
        base = max(parts, key=lambda m: abs(m.volume))
    fr = W["xA"]["EyeCorePivotHolder"]
    xa = out["XAxisA_PIP"]
    if not small:   # a scala originale telaio X e box del CoreY sono gia' a misura di servo
        xa["EyeCorePivotHolder"] = servo_seat(
            xa["EyeCorePivotHolder"], seats["X"], s,
            [s1([-6.4, -14.95, fr.bounds[0, 2]], [6.4, 10.65, 4.8])], zmin=s * fr.bounds[0, 2],
            depth=SEAT_DEPTH)
    # box del CoreY sopra il servo X: in Will (1:1) ha una piastra con la finestra del servo
    # (x +-6.4, y -24.5..-0.47, z -12..-9 nel gruppo) e sotto la cavita' tra le pareti di testa
    # (y -29.2..3.3). Ingrandite sarebbero 2.7 volte il servo: si riempiono e si apre la finestra
    # 1:1 attorno al servo vero; il riempimento appoggia 0.2 sopra le orecchie (le trattiene).
    Mc = Tm(-s * CORE_T) @ Tm(s * XA_T) @ seats["X"]        # servo X -> gruppo CoreY
    z_ear = Mc[2, 3] - (SG_H - SG_EAR[1]) + 0.2
    g = 0.3
    fill = U([box([-8.4 * s - g, -29.2 * s - g, z_ear], [8.4 * s + g, 3.3 * s + g, -12.0 * s + 0.01]),
              box([-6.4 * s - g, -24.5 * s - g, -12.0 * s - 0.01], [6.4 * s + g, -0.47 * s + g, -9.0 * s])])
    rx0, rx1 = -SG_SHAFT, SG_L - SG_SHAFT
    rcx = (rx0 + rx1) / 2
    win = box([rx0 - CL, -SG_W / 2 - CL, -SG_H], [rx1 + CL, SG_W / 2 + CL, 60])
    heads = [cyl_axis(2.4, [rcx + sx * SG_EAR_HOLES / 2, 0, -SG_H + SG_EAR[1] - 0.5],
                      [rcx + sx * SG_EAR_HOLES / 2, 0, 60], n=32) for sx in (-1, 1)]   # teste viti M2
    core = out["CoreY_PIP"]
    if not small:
        core["EyeCorePivotHolder"] = D(U([core["EyeCorePivotHolder"], fill]),
                                       [tf(win, Mc)] + [tf(h, Mc) for h in heads])
    asm["CoreY_PIP:EyeCorePivotHolder"] = tf(core["EyeCorePivotHolder"], Tm(s * CORE_T))

    asm["base"] = base
    for k, m in xa.items():
        asm[f"XAxisA_PIP:{k}"] = tf(m, Tm(s * XA_T))

    # ---------------- base in due meta' (D85) / intera (idra_version) ----------------
    if small:
        out["Base"] = base
    else:
        out.update(split_base(base, s))

    info = dict(s=s, P=P, small=small, hx=(hx0, hx1), xo=(xo0, xo1), xr=(xr0, xr1), JB=JB, PB=PB, Fs=Fs,
                MA=MA, MDb=MDb, seats=seats, linkB_len=float(np.linalg.norm(PB - JB)))
    return out, asm, info, kin


def bowtie(cx, cy, z0, z1, half_len=24.0, w_mid=14.0, w_end=26.0, grow=0.0):
    from shapely.geometry import Polygon
    pts = np.array([[-half_len, -w_end / 2], [0, -w_mid / 2], [half_len, -w_end / 2],
                    [half_len, w_end / 2], [0, w_mid / 2], [-half_len, w_end / 2]])
    poly = Polygon(pts).buffer(grow, join_style=2)
    m = trimesh.creation.extrude_polygon(poly, z1 - z0)
    m.apply_translation([cx, cy, z0])
    return m


BASE_Y = (-38.0, -8.0)          # striscia di base tenuta (unita' 1:1)
KEY_Y = (-31.0, -14.0)          # posizioni delle chiavette sotto la base (unita' 1:1)
SEAT_DEPTH = SG_EAR[0] + 8.0    # blocchi delle sedi: corpo sotto le orecchie + cavo + parete
SEAT_WALL = 3.0                 # idra_version: parete attorno al servo (mm)
KEY_DEPTH = 7.0
KEY_SCREW_X = 15.0


def split_base(base, s):
    zb = base.bounds[0, 2]
    big = 2000.0
    L = I(base, box([-big, -big, -big], [0, big, big]))
    R = I(base, box([0, -big, -big], [big, big, big]))
    cuts = []
    for y in KEY_Y:
        cuts.append(bowtie(0, s * y, zb - 1, zb + KEY_DEPTH))
        for sx in (-1, 1):
            c = trimesh.creation.cylinder(radius=1.25, height=KEY_DEPTH + 6, sections=24)
            c.apply_translation([sx * KEY_SCREW_X, s * y, zb + (KEY_DEPTH + 6) / 2 - 0.5])
            cuts.append(c)
    L, R = D(L, cuts), D(R, cuts)
    key = bowtie(0, 0, 0, KEY_DEPTH - 0.2, grow=-0.15)
    kc = []
    for sx in (-1, 1):
        kc.append(trimesh.creation.cylinder(radius=1.7, height=20, sections=24).apply_translation(
            [sx * KEY_SCREW_X, 0, 0]))
        cone = trimesh.creation.cone(radius=3.4, height=3.4, sections=24)   # svasatura sotto
        cone.apply_translation([sx * KEY_SCREW_X, 0, -0.01])
        kc.append(cone)
    return {"Base_L": L, "Base_R": R, f"BaseKey_x{len(KEY_Y)}": D(key, kc)}


# =====================================================================================
# 6. verifica, esportazione, immagini
# =====================================================================================
def rigid_yz(a0, b0, a1, b1):
    """moto rigido nel piano y-z che porta il segmento a0-b0 su a1-b1."""
    R = Rx(ang(b1 - a1) - ang(b0 - a0))
    M = R.copy()
    M[1:3, 3] = a1 - R[1:3, 1:3] @ a0
    return M


def lid_pose(asm, kin, s, dphi):
    Es, Fs = s * E, s * F
    JA0, JA1 = pol(F, kin.h, kin.hornA0), pol(F, kin.h, kin.hornA0 + dphi)
    PA0 = pol(E, kin.rA, kin.earA0)
    PA1 = pol(E, kin.rA, kin.earA0 + kin.top(dphi))
    return {
        "hornA": U([tf(asm["hornA_R"], Rx(dphi, Fs)), tf(asm["pinB_R"], Rx(dphi, Fs))]),
        "lidT": tf(asm["lidTop_R"], Rx(kin.top(dphi), Es)),
        "linkA": tf(asm["linkA_R"], rigid_yz(s * JA0, s * PA0, s * JA1, s * PA1)),
        "lidB": tf(asm["lidBot_R"], Rx(kin.bot(dphi) - kin.bot(0.0), Es)),
        "linkB": tf(asm["linkB_R"], rigid_yz(s * kin.JB(0), s * kin.PB(0), s * kin.JB(dphi),
                                             s * kin.PB(dphi))),
    }


def check(asm, kin, s, with_servo=True):
    """interferenze del lato destro su tutta la corsa palpebre (il sinistro e' speculare).
    with_servo=False (versione piccola): sedi e squadrette sono quelle di Will, il servo
    stimato non si confronta con il suo CAD."""
    static = {k: asm[k] for k in ("eye_1", "opiv_R", "cpiv_1", "base", "servo_R")}
    if not with_servo:
        del static["servo_R"]
    allowed = [{"hornA", "linkA"}, {"lidT", "linkA"}, {"lidB", "linkB"}, {"hornA", "linkB"}]
    worst = []
    for d in np.linspace(DPHI_OPEN - 4, DPHI_CLOSED, 9):
        m = {**lid_pose(asm, kin, s, d), **static}
        ks = list(m)
        for i in range(len(ks)):
            for j in range(i + 1, len(ks)):
                if {ks[i], ks[j]} in allowed:
                    continue
                a, b = m[ks[i]], m[ks[j]]
                if np.any(a.bounds[0] > b.bounds[1]) or np.any(b.bounds[0] > a.bounds[1]):
                    continue
                v = vol_inter(a, b)
                if v > 1.0:
                    worst.append((round(float(d), 1), ks[i], ks[j], round(v)))
    return worst


def check_xy(asm, with_servo=True):
    """posa neutra: gruppi X/Y e servo X, Y contro base, bulbi, supporti e tra loro
    (le parti dello stesso gruppo print-in-place non si confrontano)."""
    keys = [k for k in asm if ":" in k] + ["base", "eye_1", "eye_2", "cpiv_1", "cpiv_2"]
    if with_servo:
        keys += ["servo_X", "servo_Y"]
    grp = lambda k: k.split(":")[0]
    # servo nelle loro sedi/squadrette: contatti voluti (spline nella sede, orecchie)
    allowed = [{"servo_X", "XAxisA_PIP"}, {"servo_X", "XAxisB_PIP"}, {"servo_Y", "base"},
               {"servo_Y", "CoreY_PIP"}, {"servo_X", "CoreY_PIP"}, {"XAxisA_PIP", "CoreY_PIP"},
               # i perni del CoreY nei supporti centrali, gli adattatori nei bulbi
               {"CoreY_PIP", "cpiv_1"}, {"CoreY_PIP", "cpiv_2"},
               {"XAxisA_PIP", "eye_1"}, {"XAxisA_PIP", "eye_2"},
               {"XAxisB_PIP", "eye_1"}, {"XAxisB_PIP", "eye_2"}]
    bad = []
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            a, b = keys[i], keys[j]
            if grp(a) == grp(b) or {grp(a), grp(b)} in allowed:
                continue
            A, B = asm[a], asm[b]
            if np.any(A.bounds[0] > B.bounds[1]) or np.any(B.bounds[0] > A.bounds[1]):
                continue
            v = vol_inter(A, B)
            if v > 1.0:
                bad.append((a, b, round(v)))
    return bad


def on_bed(m):
    m = m.copy()
    b = m.bounds
    m.apply_translation([-(b[0, 0] + b[1, 0]) / 2, -(b[0, 1] + b[1, 1]) / 2, -b[0, 2]])
    return m


def export(out, od, prefix=""):
    od.mkdir(parents=True, exist_ok=True)
    for f in od.glob("*.stl"):
        f.unlink()
    rot = item_rotations()
    files = []
    for name, m in out.items():
        if isinstance(m, dict):
            m = trimesh.util.concatenate(list(m.values()))
        if name in PRINT_ROT:
            m = tf(m, rot[PRINT_ROT[name]])
        m = on_bed(m)
        m.export(od / f"{prefix}{name}.stl")
        files.append((name, m.extents))
    return files


def info_text(s, info, kin, files, worst):
    k = kin
    rng_top = (k.top(DPHI_OPEN), k.top(DPHI_CLOSED))
    rng_bot = (k.bot(DPHI_OPEN), k.bot(DPHI_CLOSED))
    P, small = info["P"], info["small"]
    L = [
        ("IDRA_VERSION (scala di Will): stessi pezzi e stessa cinematica della D85, piu' piccoli"
         if small else "VERSIONE D85"),
        f"diametro_bulbo_mm: {s * D_WILL:.1f}",
        f"fattore_di_scala: {s:.5f} (pezzi di Will EyeMech e3.2, SG90 lettera A, print-in-place)",
        f"interasse_occhi_mm: {s * 2 * EYE_X:.1f}",
        ("servo: 4 x SG90 o MG90S: X, Y, palpebre sx, palpebre dx, nelle sedi originali di Will, con i suoi fermi"
         if small else
         "servo: 4 x SG90 o MG90S veri (1:1): X, Y, palpebre sx, palpebre dx, in sedi 1:1 (base: Y + palpebre; XAxisA: X)"),
        f"palpebre: servo anteriore, {DPHI_CLOSED - DPHI_OPEN:.0f} deg di corsa: "
        f"superiore {rng_top[0]:+.1f} .. {rng_top[1]:+.1f} deg, inferiore {rng_bot[0]:+.1f} .. {rng_bot[1]:+.1f} deg",
        f"secondo_braccio_squadretta: r = {s * ARM_B_R:.1f} mm, {ARM_B_PSI:.1f} deg avanti rispetto al braccio di Will",
        f"tirante_B_interasse_mm: {s * LINK_B_L:.1f}",
    ]
    tb = (f"per tirante B: 1 x {P['PIN_SCREW']} nel PinB + 1 x {P['EAR_SCREW_TXT']} con rondella "
          "stampata sull'orecchia")
    if small:
        L += ["squadrette: quelle di Will, come nell'originale",
              f"viti: {tb}; servo e squadrette come nella guida di Will"]
    else:
        L += [f"codolo_mozzo_mm: {s * WILL_HORN_FACE - SG_BOSS_TOP - 0.6:.1f} (sede scanalato D{SPLINE_D} x {SPLINE_DEPTH})",
              f"viti: per squadretta 1 x M2x12 (nel codolo, nello scanalato); {tb};",
              f"      per servo 2 x M2x8 autofilettanti (orecchie -> sede); base: {2 * len(KEY_Y)} x M3x10 svasate nelle chiavette"]
    L.append("pezzi (mm, X x Y x Z come esportati):")
    for n, e in files:
        L.append(f"  {n}: {e[0]:.0f} x {e[1]:.0f} x {e[2]:.0f}")
    L.append("interferenze_rilevate: " + ("nessuna" if not worst else str(worst)))
    return "\n".join(L) + "\n"


# piatti per Bambu A1 (256 x 256) dei pezzi grandi della D85: (pezzo, file, rotazione z,
# posizione). "c": centro xy dell'ingombro; "min": angolo minimo xy.
A1_PLATES = {
    # le due meta' della base (194 x 80) una sopra l'altra, minuteria nella fascia in alto
    "P1": [("Base_L", "00_Base_L", 0, ("c", 128.0, 50.0)),
           ("Base_R", "01_Base_R", 0, ("c", 128.0, 140.0)),
           ("BaseKey_x2", "02_BaseKey1", 0, ("min", 10.0, 200.0)),
           ("BaseKey_x2", "03_BaseKey2", 0, ("min", 66.0, 200.0)),
           ("PinB_x2", "04_PinB1", 0, ("min", 124.0, 200.0)),
           ("PinB_x2", "05_PinB2", 0, ("min", 154.0, 200.0)),
           ("Washer_x2", "06_Washer1", 0, ("min", 184.0, 200.0)),
           ("Washer_x2", "07_Washer2", 0, ("min", 214.0, 200.0))],
    "P2": [("XAxisA_PIP", "00_XAxisA_PIP", 135, ("c", 128.0, 128.0))],   # 264 mm: in diagonale
    "P3": [("XAxisB_PIP", "00_XAxisB_PIP", 135, ("c", 128.0, 128.0))],
}


def a1_plates(od):
    """copie dei pezzi grandi gia' posizionate sui piatti A1 (od/print_A1/P1..P4)."""
    import shutil
    pd = od / "print_A1"
    if pd.exists():
        shutil.rmtree(pd)
    for plate, items in A1_PLATES.items():
        (pd / plate).mkdir(parents=True)
        for name, fname, rot, (mode, x, y) in items:
            m = trimesh.load(od / f"{name}.stl")
            if rot:
                m.apply_transform(trimesh.transformations.rotation_matrix(np.radians(rot), [0, 0, 1]))
            b = m.bounds
            ref = (b[0, :2] + b[1, :2]) / 2 if mode == "c" else b[0, :2]
            m.apply_translation([x - ref[0], y - ref[1], -b[0, 2]])
            m.export(pd / plate / f"{fname}.stl")


def mirror_asm(m):
    return mirror_x_mesh(m)


def render(asm, kin, s, path):
    import pyvista as pv
    col = {"base": "#b8b8b8", "piv": "#9a9a9a", "eye": "#f2efe8", "lidT": "#6aa36f",
           "lidB": "#4f8a55", "link": "#c9a227", "horn": "#3b6fb6", "shell": "#2f4f8f"}

    def scene(dphi):
        p = lid_pose(asm, kin, s, dphi)
        R = [(asm["base"], col["base"]), (asm["cpiv_1"], col["piv"]), (asm["opiv_R"], col["piv"]),
             (asm["eye_1"], col["eye"]), (asm["servo_R"], col["shell"]),
             (p["lidT"], col["lidT"]), (p["lidB"], col["lidB"]), (p["linkA"], col["link"]),
             (p["linkB"], "#d9822b"), (p["hornA"], col["horn"])]
        Lm = [(mirror_asm(m), c) for m, c in R[1:]]
        xy = [(m, "#8a5fb5" if k.startswith("CoreY") else "#c25a7c" if k.startswith("XAxisA")
               else "#d89a3c") for k, m in asm.items() if ":" in k]
        sv = [(asm[k], col["shell"]) for k in ("servo_X", "servo_Y")]
        return R + Lm + xy + sv

    SERVO = "#1f6fff"
    servos = {id(asm[k]) for k in ("servo_R", "servo_X", "servo_Y")}

    def is_servo(m):
        return id(m) in servos

    # (titolo, posa palpebre, direzione di vista, zoom, servo in evidenza)
    views = [("riposo, palpebre a meta'", 0.0, (0.9, -1.6, 0.8), 1.6, False),
             ("palpebre chiuse", DPHI_CLOSED, (0.15, -1.0, 0.25), 1.9, False),
             ("palpebre aperte", DPHI_OPEN, (0.15, -1.0, 0.25), 1.9, False),
             ("lato dx: tiranti A (giallo) e B (arancio)", 0.0, (1.0, -0.15, 0.1), 1.9, False),
             ("i 4 servo (blu): X al centro, Y dietro, palpebre ai lati", 0.0, (0.6, -1.0, 1.1), 1.6, True),
             ("i 4 servo (blu), da dietro", 0.0, (-0.5, 1.2, 0.9), 1.6, True)]
    pl = pv.Plotter(off_screen=True, shape=(2, 3), window_size=(2700, 1300))
    for i, (title, d, v, zoom, xray) in enumerate(views):
        pl.subplot(i // 3, i % 3)
        R = scene(d)
        if xray:
            R.append((mirror_asm(asm["servo_R"]), col["shell"]))
            servos.add(id(R[-1][0]))
        for m, c in R:
            sv = is_servo(m)
            if xray:
                pl.add_mesh(pv.wrap(m), color=SERVO if sv else c, opacity=1.0 if sv else 0.18,
                            smooth_shading=False)
            else:
                pl.add_mesh(pv.wrap(m), color=SERVO if sv else c, smooth_shading=False)
        pl.view_vector(v)
        pl.camera.zoom(zoom)
        pl.add_text(title, font_size=11)
    try:
        pl.screenshot(str(path))
    except OSError:            # file aperto in un visualizzatore (Windows lo blocca)
        alt = path.with_name(path.stem + "_nuova.png")
        pl.screenshot(str(alt))
        print(f"immagine bloccata, salvata in {alt}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--d", type=float, default=85.0, help="diametro bulbo [mm]")
    ap.add_argument("--interasse", type=float, default=200.0,
                    help="distanza tra i centri degli occhi [mm]; se data, fissa la scala "
                         "(il diametro ne segue: 200 mm -> bulbo 85.3). 0 = usa --d")
    ap.add_argument("--small", action="store_true",
                    help="versione di prova in scala di Will (bulbo 32 mm, occhi a 75 mm)")
    ap.add_argument("--render", action="store_true")
    ap.add_argument("--no-check", action="store_true")
    a = ap.parse_args()
    if a.small:
        a.d = D_WILL
    elif a.interasse > 0:
        a.d = D_WILL * a.interasse / (2 * EYE_X)
    out, asm, info, kin = build(a.d, small=a.small)
    s = info["s"]
    worst = [] if a.no_check else check(asm, kin, s, with_servo=not a.small)
    if not a.no_check:
        worst += [("assi X/Y in posa neutra",) + w for w in check_xy(asm, with_servo=not a.small)]
    tag = "idra_version" if a.small else f"eyemech_D{a.d:.0f}"
    od = OUTROOT / tag
    files = export(out, od, prefix="idra_version_" if a.small else "")
    if not a.small:
        a1_plates(od)
    txt = info_text(s, info, kin, files, worst)
    (od / "info.txt").write_text(txt, encoding="utf-8")
    print(txt)
    if a.render:
        render(asm, kin, s, IMG / f"{tag}.png")


if __name__ == "__main__":
    main()
