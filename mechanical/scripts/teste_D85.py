"""
Piatti Bambu Lab A1 per le teste dell'Idra (occhi EyeMech D85), una cartella per testa.

In mechanical/eyes/eyemech_D85/:
  pezzi/                 un STL per pezzo (li genera generate_eyemech.py)
  Testa_<n>.../          per ogni testa i suoi piatti; ogni cartella con piatti ha un layout_piatti.json
                         (cosa c'e' su ogni piatto e dove) e una sottocartella per piatto con:
                           <Testa>_<Piatto>.3mf  progetto Bambu Studio NON tagliato (pezzi gia' disposti,
                                                 A1 0.4, 0.20mm Standard, PLA Basic, supporti tree(auto) 30 gradi)
                           NN_<pezzo>.stl        gli stessi pezzi gia' posizionati (per rifarlo a mano)
                           piatto.png            la disposizione vista dall'alto

Le disposizioni sono incastri sulle impronte reali dei pezzi (proiezione sul piano), rotazioni a 15 gradi,
almeno 4 mm tra i pezzi e 3 mm dal bordo (come i piatti della testa 1).

Uso:
  python teste_D85.py impacchetta <kit> <n_piatti> [--copie N] [--base] [--tentativi T]
        cerca una disposizione dei pezzi del kit su n piatti (con --base il primo piatto e' quello delle due
        basi incastrate, gia' occupato, e i pezzi piccoli finiscono negli spazi liberi) e la stampa in JSON,
        da mettere in <cartella>/layout_piatti.json (poi cambiare "testa" e, se serve, i nomi dei piatti)
  python teste_D85.py costruisci <cartella> [--taglia]
        rifa' le sottocartelle dei piatti da <cartella>/layout_piatti.json (STL, 3MF, png) e la tabella dei
        piatti in fondo a <cartella>/README.md; con --taglia (solo sul PC con Bambu Studio) i 3MF escono gia'
        tagliati, con tempi e grammi esatti
Kit: coppia (testa a 2 occhi completa), coppia_senza_basi_occhi (testa 2), singolo (testa a 1 occhio, lato sx),
     singolo_senza_basi; --copie 2 = due teste uguali incastrate insieme (teste 3 e 4).

Tempi e grammi nel README sono stime: per ogni pezzo la media misurata nel G-code dei piatti della testa 1
(Bambu Studio 2.05, A1, 0.20 mm, 2 pareti, 15%, supporti tree 30 gradi). Bambu Studio da' quelli esatti.
Dipendenze: pip install trimesh shapely scipy matplotlib
"""
import argparse
import itertools
import json
import random
import re
import shutil
import sys
import uuid
import zipfile
from pathlib import Path

import numpy as np
import trimesh
from shapely import affinity
from shapely.geometry import Polygon
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[2]
D85 = ROOT / "mechanical" / "eyes" / "eyemech_D85"
PEZZI = D85 / "pezzi"
BED, GAP, MARGIN = 256.0, 4.0, 3.0
ROTS = list(range(0, 360, 15))

# pezzi per kit (i nomi sono gli STL in pezzi/; i _x2 vanno stampati 2 volte e compaiono 2 volte)
KIT = {
    "coppia": ["Base_L", "Base_R", "BaseKey_x2", "BaseKey_x2", "PinB_x2", "PinB_x2", "Eyeball_x2", "Eyeball_x2",
               "LidBottom_L_PIP", "LidBottom_R_PIP", "LidTop_L_PIP", "LidTop_R_PIP", "PivotOuter_L", "PivotOuter_R",
               "PivotCentral_x2", "PivotCentral_x2", "CoreY_PIP", "XAxisA_PIP", "XAxisB_PIP"],
    # occhio singolo (sinistro): tutto il meccanismo centrale, i pezzi del solo lato sx
    "singolo": ["Base_L", "Base_R", "BaseKey_x2", "BaseKey_x2", "PinB_x2", "Eyeball_x2",
                "LidBottom_L_PIP", "LidTop_L_PIP", "PivotOuter_L", "PivotCentral_x2", "PivotCentral_x2",
                "CoreY_PIP", "XAxisA_PIP", "XAxisB_PIP"],
}
KIT["coppia_senza_basi_occhi"] = [n for n in KIT["coppia"] if n not in ("Base_L", "Base_R", "Eyeball_x2")]
KIT["singolo_senza_basi"] = [n for n in KIT["singolo"] if n not in ("Base_L", "Base_R")]

# piatto delle due basi incastrate (come Piatto_1 della testa 1): pezzo, rotazione, angolo minimo
BASE_PLATE = [dict(pezzo="Base_L", rot_z=0, x=3.0, y=3.0), dict(pezzo="Base_R", rot_z=195, x=24.0, y=114.0)]

# stima per pezzo: grammi e ore, medie dal G-code dei 5 piatti della testa 1 (supporti compresi)
STIMA = {
    "Base_L": (117.6, 3.27), "Base_R": (112.5, 3.13), "BaseKey_x2": (3.2, 0.13), "PinB_x2": (2.1, 0.065),
    "Eyeball_x2": (54.9, 1.65), "LidBottom_L_PIP": (54.1, 2.02), "LidBottom_R_PIP": (54.1, 2.02),
    "LidTop_L_PIP": (63.2, 2.68), "LidTop_R_PIP": (63.2, 2.68), "PivotOuter_L": (19.9, 0.75),
    "PivotOuter_R": (19.9, 0.75), "PivotCentral_x2": (25.0, 0.71), "CoreY_PIP": (92.9, 3.75),
    "XAxisA_PIP": (79.0, 3.32), "XAxisB_PIP": (71.1, 2.93),
}
NOME = {  # descrizione breve per i README
    "Base_L": "base sx", "Base_R": "base dx", "BaseKey_x2": "chiavetta base", "PinB_x2": "perno PinB",
    "Eyeball_x2": "bulbo", "LidBottom_L_PIP": "palpebra inf. sx + LinkB", "LidBottom_R_PIP": "palpebra inf. dx + LinkB",
    "LidTop_L_PIP": "palpebra sup. sx", "LidTop_R_PIP": "palpebra sup. dx", "PivotOuter_L": "supporto esterno sx",
    "PivotOuter_R": "supporto esterno dx", "PivotCentral_x2": "supporto centrale", "CoreY_PIP": "telaio Y (CoreY)",
    "XAxisA_PIP": "asse X A (sede servo X)", "XAxisB_PIP": "asse X B (squadretta X)",
}


# ------------------------------------------------------------------------------------------- geometria
_mesh = {}


def mesh(name):
    if name not in _mesh:
        m = trimesh.load(PEZZI / f"{name}.stl")
        m.apply_translation(-m.bounds[0])
        _mesh[name] = m
    return _mesh[name].copy()


def footprint(m):
    tri = m.vertices[m.faces][:, :, :2]
    return unary_union([Polygon(t) for t in tri if Polygon(t).area > 1e-6]).buffer(0.01)


def placed(it):
    """mesh del pezzo ruotato attorno a z e con l'angolo minimo dell'ingombro in (x, y)."""
    m = mesh(it["pezzo"])
    m.apply_transform(trimesh.transformations.rotation_matrix(np.radians(it["rot_z"]), [0, 0, 1]))
    b = m.bounds
    m.apply_translation([it["x"] - b[0, 0], it["y"] - b[0, 1], -b[0, 2]])
    return m


# ------------------------------------------------------------------------------------- impacchettamento
class Packer:
    """raster 0.5 mm; impronta dilatata di GAP/2 (+ mezza diagonale di cella), posizioni libere via FFT."""
    R = 0.5

    def __init__(self):
        import scipy.fft as sfft
        from scipy import ndimage
        self.sfft, self.ndimage = sfft, ndimage
        self.N = int(BED / self.R)
        self.dil = GAP / 2 + self.R * 0.72
        r = int(np.ceil(self.dil / self.R))
        yy, xx = np.mgrid[-r:r + 1, -r:r + 1]
        self.disk = np.hypot(xx, yy) * self.R <= self.dil
        self.r = r
        self.fp, self.simp, self.kc = {}, {}, {}

    def foot(self, name):
        if name not in self.fp:
            self.fp[name] = footprint(mesh(name))
            self.simp[name] = self.fp[name].simplify(0.08)
        return self.fp[name]

    def raster(self, P, ox, oy, w, h):
        from matplotlib.path import Path as MPath
        xs = ox + (np.arange(w) + 0.5) * self.R
        ys = oy + (np.arange(h) + 0.5) * self.R
        X, Y = np.meshgrid(xs, ys)
        pts = np.c_[X.ravel(), Y.ravel()]
        K = np.zeros(w * h, bool)
        for g in getattr(P, "geoms", [P]):
            ins = MPath(np.asarray(g.exterior.coords)).contains_points(pts)
            for hole in g.interiors:
                ins &= ~MPath(np.asarray(hole.coords)).contains_points(pts)
            K |= ins
        return self.ndimage.binary_dilation(K.reshape(h, w), self.disk)

    def kernel(self, name, rot):
        key = (name, rot)
        if key not in self.kc:
            self.foot(name)
            P = affinity.rotate(self.simp[name], rot, origin=(0, 0))
            x0, y0, x1, y1 = P.bounds
            pad = self.r + 1
            w = int(np.ceil((x1 - x0) / self.R)) + 2 * pad
            h = int(np.ceil((y1 - y0) / self.R)) + 2 * pad
            ox, oy = x0 - pad * self.R, y0 - pad * self.R
            self.kc[key] = (self.raster(P, ox, oy, w, h).astype(np.float32), (-ox, -oy))
        return self.kc[key]

    def plate(self, fixed=()):
        N = self.N
        O = np.zeros((N, N), np.float32)
        c = (np.arange(N) + 0.5) * self.R
        bad = (c < MARGIN - self.dil) | (c > BED - MARGIN + self.dil)
        O[bad, :] = 1
        O[:, bad] = 1
        for P in fixed:
            O[self.raster(P.simplify(0.08), 0.0, 0.0, N, N)] = 1
        return O

    def place(self, O, name, score):
        N, sfft = self.N, self.sfft
        Of = sfft.rfft2(O)
        best = None
        for rot in ROTS:
            K, _ = self.kernel(name, rot)
            kh, kw = K.shape
            if kh > N or kw > N:
                continue
            Kp = np.zeros((N, N), np.float32)
            Kp[:kh, :kw] = K
            F = sfft.irfft2(Of * np.conj(sfft.rfft2(Kp)), s=(N, N))[:N - kh + 1, :N - kw + 1] < 0.5
            if not F.any():
                continue
            js, is_ = np.nonzero(F)
            if score == "bl":
                s = (js + kh) * 1000.0 + is_
            elif score == "lb":
                s = (is_ + kw) * 1000.0 + js
            else:
                s = np.maximum(js + kh, is_ + kw) * 1000.0 + (js + kh + is_ + kw)
            k = int(np.argmin(s))
            if best is None or s[k] < best[0]:
                best = (s[k], rot, int(is_[k]), int(js[k]))
        if best is None:
            return None
        _, rot, i, j = best
        K, (sx, sy) = self.kernel(name, rot)
        O[j:j + K.shape[0], i:i + K.shape[1]] += K
        poly = affinity.translate(affinity.rotate(self.foot(name), rot, origin=(0, 0)),
                                  sx + i * self.R, sy + j * self.R)
        x0, y0 = poly.bounds[:2]
        return dict(pezzo=name, rot_z=rot, x=round(x0 + 0.01, 2), y=round(y0 + 0.01, 2), poly=poly)

    def pack(self, names, nplates, pre=(), tries=20, seed=1):
        """pre: piatti gia' occupati (liste di item con 'poly'), messi in coda: i pezzi grandi vanno
        prima nei piatti vuoti, i piccoli riempiono anche i buchi dei piatti pre-occupati."""
        rnd = random.Random(seed)
        base = sorted(names, key=lambda n: -self.foot(n).buffer(GAP / 2).area)
        for t in range(tries):
            order = base[:]
            if t:
                for _ in range(rnd.randint(1, 5)):
                    i, j = rnd.randrange(len(order)), rnd.randrange(len(order))
                    order[i], order[j] = order[j], order[i]
            for score in ("bl", "lb", "corner"):
                plates = [self.plate() for _ in range(nplates)] + [self.plate([p["poly"] for p in pl]) for pl in pre]
                res = [[] for _ in range(nplates)] + [list(pl) for pl in pre]
                ok = True
                for n in order:
                    for b in range(len(plates)):
                        p = self.place(plates[b], n, score)
                        if p:
                            res[b].append(p)
                            break
                    else:
                        ok = False
                        break
                if ok:
                    print(f"  trovato al tentativo {t + 1} ({score})", file=sys.stderr)
                    return res[nplates:] + res[:nplates]
        return None


def check(items):
    """distanza minima tra i pezzi e dal bordo, sulle impronte vere."""
    fps = [footprint(placed(it)) for it in items]
    d = min((a.distance(b) for a, b in itertools.combinations(fps, 2)), default=99.0)
    lo = min(min(f.bounds[0], f.bounds[1]) for f in fps)
    hi = max(max(f.bounds[2], f.bounds[3]) for f in fps)
    return d, lo, hi, fps


# ------------------------------------------------------------------------------------- 3MF Bambu Studio
TEMPLATE_SETTINGS = None


def project_settings(over=None):
    """impostazioni di progetto: A1 0.4 / 0.20mm Standard / PLA Basic con supporti tree(auto) 30 gradi,
    prese dal progetto gia' tagliato della testa 1 e segnate come modifiche al profilo di sistema;
    over = altre impostazioni di processo (es. {"wall_loops": "4"})."""
    src = D85 / "Testa_1" / "Piatto_3" / "Piatto_3.3mf"
    with zipfile.ZipFile(src) as z:
        d = json.loads(z.read("Metadata/project_settings.config"))
    d.update({"enable_support": "1", "support_type": "tree(auto)", "support_threshold_angle": "30",
              "curr_bed_type": "Textured PEI Plate"})
    diff = list(d.get("different_settings_to_system", ["", "", ""]))
    while len(diff) < 3:
        diff.append("")
    keys = ["enable_support", "support_threshold_angle", "support_type"]
    for k, v in (over or {}).items():
        d[k] = v
        if k not in keys:
            keys.append(k)
    diff[0] = ";".join(sorted(keys))
    d["different_settings_to_system"] = diff
    return json.dumps(d, indent=4, ensure_ascii=False)


def write_3mf(path, items, meshes, title, png=None, impostazioni=None):
    U = lambda a, b: f"{a:08x}-{b}"
    objs, comps, items_xml, model_cfg, rels, cut = [], [], [], [], [], []
    files = {}
    for k, (it, m) in enumerate(zip(items, meshes), start=1):
        c = (m.bounds[0] + m.bounds[1]) / 2
        v = m.vertices - c
        verts = "\n".join(f'     <vertex x="{x:.6f}" y="{y:.6f}" z="{z:.6f}"/>' for x, y, z in v)
        tris = "\n".join(f'     <triangle v1="{a}" v2="{b}" v3="{cc}"/>' for a, b, cc in m.faces)
        oid, wid = 2 * k - 1, 2 * k
        files[f"3D/Objects/object_{k}.model"] = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
            'xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" '
            'xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" requiredextensions="p">\n'
            ' <metadata name="BambuStudio:3mfVersion">1</metadata>\n <resources>\n'
            f'  <object id="{oid}" p:UUID="{U(k << 16, "81cb-4c03-9d28-80fed5dfa1dc")}" type="model">\n'
            f'   <mesh>\n    <vertices>\n{verts}\n    </vertices>\n    <triangles>\n{tris}\n    </triangles>\n   </mesh>\n'
            '  </object>\n </resources>\n <build/>\n</model>\n')
        t = f"1 0 0 0 1 0 0 0 1 {c[0]:.6f} {c[1]:.6f} {c[2]:.6f}"
        objs.append(f'  <object id="{wid}" p:UUID="{U(k, "61cb-4c03-9d28-80fed5dfa1dc")}" type="model">\n'
                    f'   <components>\n    <component p:path="/3D/Objects/object_{k}.model" objectid="{oid}" '
                    f'p:UUID="{U(k << 16, "b206-40ff-9872-83e8017abed1")}" transform="{t}"/>\n   </components>\n  </object>')
        items_xml.append(f'  <item objectid="{wid}" p:UUID="{U(wid, "b1ec-4553-aec9-835e5b724bb4")}" '
                         f'transform="1 0 0 0 1 0 0 0 1 0 0 0" printable="1"/>')
        rels.append(f' <Relationship Target="/3D/Objects/object_{k}.model" Id="rel-{k}" '
                    'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>')
        name = f"{k - 1:02d}_{it['pezzo']}"
        mat = f"1 0 0 {c[0]:.6f} 0 1 0 {c[1]:.6f} 0 0 1 {c[2]:.6f} 0 0 0 1"
        model_cfg.append(
            f'  <object id="{wid}">\n    <metadata key="name" value="{name}"/>\n    <metadata key="extruder" value="1"/>\n'
            f'    <metadata face_count="{len(m.faces)}"/>\n    <part id="{oid}" subtype="normal_part">\n'
            f'      <metadata key="name" value="{name}"/>\n      <metadata key="matrix" value="{mat}"/>\n'
            f'      <metadata key="source_file" value="{name}.stl"/>\n      <metadata key="source_object_id" value="0"/>\n'
            f'      <metadata key="source_volume_id" value="0"/>\n'
            f'      <metadata key="source_offset_x" value="{c[0]:.6f}"/>\n'
            f'      <metadata key="source_offset_y" value="{c[1]:.6f}"/>\n'
            f'      <metadata key="source_offset_z" value="{c[2]:.6f}"/>\n'
            f'      <mesh_stat face_count="{len(m.faces)}" edges_fixed="0" degenerate_facets="0" facets_removed="0" '
            'facets_reversed="0" backwards_edges="0"/>\n    </part>\n  </object>')
        cut.append(f' <object id="{k}">\n  <cut_id id="0" check_sum="1" connectors_cnt="0"/>\n </object>')
    files["3D/3dmodel.model"] = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
        'xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" '
        'xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" requiredextensions="p">\n'
        ' <metadata name="Application">BambuStudio-02.05.00.66</metadata>\n'
        ' <metadata name="BambuStudio:3mfVersion">1</metadata>\n'
        f' <metadata name="Title">{title}</metadata>\n <resources>\n' + "\n".join(objs) + "\n </resources>\n"
        f' <build p:UUID="{uuid.uuid4()}">\n' + "\n".join(items_xml) + "\n </build>\n</model>\n")
    files["3D/_rels/3dmodel.model.rels"] = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
        + "\n".join(rels) + "\n</Relationships>\n")
    thumb = ('    <metadata key="thumbnail_file" value="Metadata/plate_1.png"/>\n' if png else "")
    files["Metadata/model_settings.config"] = (
        '<?xml version="1.0" encoding="UTF-8"?>\n<config>\n' + "\n".join(model_cfg) +
        '\n  <plate>\n    <metadata key="plater_id" value="1"/>\n    <metadata key="plater_name" value=""/>\n'
        '    <metadata key="locked" value="false"/>\n' + thumb + '  </plate>\n  <assemble>\n  </assemble>\n</config>\n')
    files["Metadata/project_settings.config"] = project_settings(impostazioni)
    files["Metadata/cut_information.xml"] = ('<?xml version="1.0" encoding="utf-8"?>\n<objects>\n'
                                              + "\n".join(cut) + "\n</objects>\n")
    files["Metadata/slice_info.config"] = (
        '<?xml version="1.0" encoding="UTF-8"?>\n<config>\n  <header>\n'
        '    <header_item key="X-BBL-Client-Type" value="slicer"/>\n'
        '    <header_item key="X-BBL-Client-Version" value="02.05.00.66"/>\n  </header>\n</config>\n')
    rel_thumb = ('\n <Relationship Target="/Metadata/plate_1.png" Id="rel-2" '
                 'Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/thumbnail"/>'
                 if png else "")
    files["_rels/.rels"] = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
        ' <Relationship Target="/3D/3dmodel.model" Id="rel-1" '
        'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>' + rel_thumb + "\n</Relationships>\n")
    files["[Content_Types].xml"] = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\n'
        ' <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>\n'
        ' <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>\n'
        ' <Default Extension="png" ContentType="image/png"/>\n'
        ' <Default Extension="gcode" ContentType="text/x.gcode"/>\n</Types>\n')
    order = ["[Content_Types].xml", "_rels/.rels", "3D/3dmodel.model", "3D/_rels/3dmodel.model.rels"]
    order += sorted(k for k in files if k.startswith("3D/Objects/")) + sorted(k for k in files if k.startswith("Metadata/"))
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for k in order:
            z.writestr(k, files[k])
        if png:
            z.write(png, "Metadata/plate_1.png")


# ---------------------------------------------------------------------------------------- costruzione
def stima(names):
    g = sum(STIMA[n][0] for n in names)
    h = sum(STIMA[n][1] for n in names)
    return g, h


def hm(h):
    return f"{int(h)} h {int(round((h % 1) * 60)):02d} min"


def contenuto(names):
    cnt = {}
    for n in names:
        cnt[n] = cnt.get(n, 0) + 1
    return " + ".join((f"{c} " if c > 1 else "") + f"`{n.replace('_x2', '')}`" for n, c in cnt.items())


def build(folder, slicer=False):
    folder = Path(folder)
    lay = json.load(open(folder / "layout_piatti.json", encoding="utf-8"))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    testa = lay["testa"]
    for pl in lay["piatti"]:
        pdir = folder / pl["nome"]
        if pdir.exists():
            shutil.rmtree(pdir)
        pdir.mkdir(parents=True)
        items = pl["pezzi"]
        meshes = [placed(it) for it in items]
        d, lo, hi, fps = check(items)
        if lo < 1 or hi > BED - 1:
            raise SystemExit(f"{pl['nome']}: un pezzo esce dal piano ({lo:.1f}, {hi:.1f})")
        for k, (it, m) in enumerate(zip(items, meshes)):
            m.export(pdir / f"{k:02d}_{it['pezzo']}.stl")
        names = [it["pezzo"] for it in items]
        g, h = stima(names)
        zmax = max(m.bounds[1, 2] for m in meshes)
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.add_patch(plt.Rectangle((0, 0), BED, BED, fc="#eeeeee", ec="k"))
        for n, f in zip(names, fps):
            for gg in getattr(f, "geoms", [f]):
                ax.fill(*gg.exterior.xy, alpha=.75)
            c = f.representative_point()
            ax.text(c.x, c.y, n.replace("_PIP", "").replace("_x2", ""), ha="center", fontsize=8)
        ax.set_xlim(-5, BED + 5)
        ax.set_ylim(-5, BED + 5)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_title(f"{testa} - {pl['nome']}: {len(items)} pezzi, ~{hm(h)}, ~{g:.0f} g")
        fig.savefig(pdir / "piatto.png", dpi=80, bbox_inches="tight")
        plt.close(fig)
        name = f"{testa}_{pl['nome']}"
        write_3mf(pdir / f"{name}.3mf", items, meshes, name, png=pdir / "piatto.png")
        esatto = taglia(pdir, name) if slicer else None
        pl["_info"] = (names, g, h, zmax, esatto)
        print(f"{name}: {len(items)} pezzi, distanza minima {d:.1f} mm, bordo {lo:.1f}..{hi:.1f}, "
              f"alt. {zmax:.0f} mm, ~{hm(h)}, ~{g:.0f} g" + (f"; Bambu Studio: {hm(esatto[1])}, {esatto[0]:.0f} g"
                                                            if esatto else ""))
    tabella(folder, lay)
    return lay


def taglia(pdir, name):
    """taglia il piatto con Bambu Studio da riga di comando (solo sul PC, vedi pack_plate.BAMBU):
    il 3MF non tagliato viene sostituito da quello tagliato; ritorna (grammi, ore)."""
    import subprocess
    import tempfile
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import pack_plate as pp
    with tempfile.TemporaryDirectory() as tmp:
        m_, p_, f_ = pp.profiles(tmp)
        cmd = [str(pp.BAMBU / "bambu-studio.exe"), "--slice", "0", "--arrange", "0", "--orient", "0",
               "--load-settings", f"{m_};{p_}", "--load-filaments", f_, "--outputdir", tmp,
               "--export-3mf", f"{name}.3mf", *map(str, sorted(pdir.glob("*.stl")))]
        subprocess.run(cmd, capture_output=True, check=True)
        shutil.copy(Path(tmp) / f"{name}.3mf", pdir / f"{name}.3mf")
    with zipfile.ZipFile(pdir / f"{name}.3mf") as z:
        si = z.read("Metadata/slice_info.config").decode()
    t = int(re.search(r'key="prediction" value="(\d+)"', si).group(1))
    w = float(re.search(r'key="weight" value="([\d.]+)"', si).group(1))
    return w, t / 3600


MARK = "<!-- tabella piatti: generata da mechanical/scripts/teste_D85.py -->"


def tabella(folder, lay):
    """tabella dei piatti in fondo al README.md della cartella (il testo prima del segno resta)."""
    righe = [MARK, "", "| Piatto | Pezzi | Contenuto | Tempo | Filamento | Altezza max |", "|---|---|---|---|---|---|"]
    G = H = 0.0
    for pl in lay["piatti"]:
        names, g, h, zmax, esatto = pl["_info"]
        if esatto:
            g, h = esatto
            t, w = hm(h), f"{g:.0f} g"
        else:
            t, w = f"~{hm(h)}", f"~{g:.0f} g"
        G += g
        H += h
        righe.append(f"| `{pl['nome']}` | {len(names)} | {contenuto(names)} | {t} | {w} | {zmax:.0f} mm |")
    righe.append(f"| **Totale** | **{sum(len(p['_info'][0]) for p in lay['piatti'])}** | "
                 f"**{len(lay['piatti'])} piatti** | **~{hm(H)}** | **~{G / 1000:.2f} kg** | |")
    righe += ["", "Tempi e grammi con `~` sono stime (media per pezzo misurata nei G-code dei piatti della testa 1, "
              "supporti compresi, senza riscaldamento e calibrazione iniziale): quelli esatti li dà Bambu Studio "
              "dopo *Slice*.", ""]
    rd = folder / "README.md"
    testo = rd.read_text(encoding="utf-8") if rd.exists() else f"# {lay['testa']}\n\n"
    testo = testo.split(MARK)[0].rstrip() + "\n\n"
    rd.write_text(testo + "\n".join(righe), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a1 = sub.add_parser("impacchetta")
    a1.add_argument("kit", choices=sorted(KIT))
    a1.add_argument("piatti", type=int, help="piatti vuoti a disposizione (oltre a quello delle basi con --base)")
    a1.add_argument("--base", action="store_true", help="basi sul piatto incastrato di sempre, il resto attorno")
    a1.add_argument("--copie", type=int, default=1, help="quante teste uguali insieme")
    a1.add_argument("--tentativi", type=int, default=20)
    a2 = sub.add_parser("costruisci")
    a2.add_argument("cartella")
    a2.add_argument("--taglia", action="store_true",
                    help="taglia anche i piatti con Bambu Studio (solo sul PC Windows, tempi e grammi esatti)")
    a = ap.parse_args()
    if a.cmd == "costruisci":
        build(a.cartella, slicer=a.taglia)
        return
    names = KIT[a.kit] * a.copie
    pk = Packer()
    pre = []
    if a.base:
        for _ in range(a.copie):
            names.remove("Base_L")
            names.remove("Base_R")
            pre.append([dict(it, poly=footprint(placed(it))) for it in BASE_PLATE])
    res = pk.pack(names, a.piatti, pre=pre, tries=a.tentativi)
    if res is None:
        raise SystemExit("non ci stanno")
    nomi = [f"Piatto_basi_{k + 1}" for k in range(len(pre))] + [f"Piatto_{chr(65 + k)}" for k in range(a.piatti)]
    out = {"testa": "TestaN", "piatti": [
        {"nome": n, "pezzi": [{k: v for k, v in it.items() if k != "poly"} for it in pl]} for n, pl in zip(nomi, res)]}
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
