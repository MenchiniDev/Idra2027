"""
Supporto del servo della mandibola (DS3225, 25 kg) sotto la base degli occhi D85: 2 pezzi stampati.

  1. Guida   - flangia avvitata SOTTO l'estremita' SINISTRA della base (Base_L) con 4 bulloni M4 (fori da fare
               nella base, la flangia fa da dima) e un canale verticale a U, aperto verso l'esterno (lato
               dell'albero del servo) e in basso, con una fessura verticale su tutti e due i fianchi.
  2. Slitta  - l'incasso preciso del DS3225 (corpo nella tasca, orecchie appoggiate sulla faccia, 4 viti del
               servo); scorre nel canale per regolare l'ALTEZZA (corsa 80 mm) e si blocca con 2 viti M4 che
               passano nella fessura di un fianco della guida e si avvitano nei dadi della slitta.

Albero del servo orizzontale, parallelo all'asse degli occhi (asse x) e rivolto verso l'esterno: il servo sta
all'estremita' della base, vicino alla cerniera della mandibola, e la squadretta si avvita alla mandibola con un
braccio corto.

Coordinate della base assemblata (x verso destra, y verso dietro, z in su, fondo della base a z = 0; i piedi
dei supporti a L sporgono fino a z = -21.5 a x = +-28.7..43.6 e +-157.3..168.3).
Posizione di serie: sotto il blocco pieno all'estremita' sinistra della base (x = -193.9..-169, spesso 20.8 mm),
parete di fondo della guida a 1.5 mm dal piede del supporto esterno; fori a x = -175.8 e -186.8, y = -50 e +22.
La guida e' simmetrica davanti/dietro: girata di 180 gradi va anche all'estremita' destra (se la base la' e'
intera, Base_R).

Servo DS3225 (datasheet Dsservo): corpo 40 x 20 x 40.5, orecchie 54.5, fori 49.5 x 10, faccia inferiore
delle orecchie a 27.7 dal fondo, albero a ~10 mm da un'estremita' del corpo.

Uso:  python supporto_mandibola.py     -> pezzi/*.stl, stampa/*.3mf (+ anteprime)
Dipendenze: pip install trimesh manifold3d numpy matplotlib
"""
import json
import uuid
import zipfile
from pathlib import Path

import manifold3d as m3
import numpy as np
import trimesh
from manifold3d import Manifold

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SEG = 48
ADD = m3.OpType.Add

# ------------------------------------------------------------------ viteria
M4_FREE, M4_NUT_AF, M4_NUT_H = 4.5, 7.0, 3.2
SERVO_PILOT = 2.6           # fori per le viti del servo (autofilettanti del kit, ~M3)

# ------------------------------------------------------------------ servo DS3225
SV = dict(L=40.0, W=20.0, H=40.5, EAR_L=54.5, HOLE_L=49.5, HOLE_W=10.0, EAR_Z=27.7, EAR_T=2.5, SHAFT=10.0)
CL_POCKET = 0.3             # gioco per lato nella tasca del corpo
CL_SLIDE = 0.3              # gioco per lato tra slitta e canale

# ------------------------------------------------------------------ slitta (coordinate locali)
# x = 0 faccia posteriore -> x = D faccia con le orecchie; y larghezza; z altezza (centro a 0).
SL = dict(D=32.0, W=32.6, H=72.0, FLOOR=3.8,
          LOCK_X=22.0, LOCK_Z=30.0, LOCK_DEPTH=14.0,      # 2 viti di blocco (lungo y, dalla faccia +y)
          CABLE_W=8.0, CABLE_X1=12.0)                     # passaggio del cavo alle due estremita'

# ------------------------------------------------------------------ guida
# Coordinate locali della guida: u = distanza dalla faccia esterna della parete di fondo verso l'esterno (lato
# aperto), v = di fianco (centro del canale a 0), z = come la base. Nella base: x = x_back - u, y = cy - v.
GD = dict(x_back=-169.8, cy=-14.0,                         # parete di fondo a 1.5 mm dal piede esterno (x -168.3)
          bolt_u=(6.0, 17.0), bolt_v=36.0,                # 4 fori: x = -175.8 / -186.8, y = -50 / +22
          fl_v=42.0, fl_t=6.0,                            # flangia: mezza lunghezza (v), spessore
          wall=6.0, cable_gap=8.0,                        # pareti; spazio per il cavo sopra la slitta in alto
          travel=80.0, slot_w=4.6)                        # corsa della slitta (regolazione in altezza)


def box(lo, hi):
    lo, hi = np.asarray(lo, float), np.asarray(hi, float)
    return Manifold.cube(tuple(hi - lo)).translate(tuple(lo))


def cyl(r, p0, p1, seg=SEG):
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


# ======================================================================== slitta
def slitta():
    s = SL
    D, W2, H2 = s["D"], s["W"] / 2, s["H"] / 2
    m = box((0, -W2, -H2), (D, W2, H2))
    pl, pw = SV["L"] / 2 + CL_POCKET, SV["W"] / 2 + CL_POCKET
    m = m - box((s["FLOOR"], -pw, -pl), (D + 1, pw, pl))                       # tasca del corpo
    for dz in (-SV["HOLE_L"] / 2, SV["HOLE_L"] / 2):                          # viti delle orecchie
        for dy in (-SV["HOLE_W"] / 2, SV["HOLE_W"] / 2):
            m = m - cyl(SERVO_PILOT / 2, (D - 16.0, dy, dz), (D + 1, dy, dz))
    for sz in (-1, 1):                                                         # cavo: esce in fondo al corpo
        m = m - box((s["FLOOR"], -s["CABLE_W"] / 2, min(sz * (pl - 0.1), sz * (H2 + 1))),
                    (s["CABLE_X1"], s["CABLE_W"] / 2, max(sz * (pl - 0.1), sz * (H2 + 1))))
        # vite di blocco: foro lungo y dalla faccia +y, dado M4 nella sede sulla faccia
        x, z = s["LOCK_X"], sz * s["LOCK_Z"]
        m = m - cyl(M4_FREE / 2, (x, W2 - s["LOCK_DEPTH"], z), (x, W2 + 1, z))
        nut = cyl((M4_NUT_AF + 0.3) / np.sqrt(3), (x, W2 - (M4_NUT_H + 0.4), z), (x, W2 + 1, z), seg=6)
        m = m - nut
    return m


# ======================================================================== guida
def dims():
    """quote della guida (locali) e della corsa, ricavate da GD, SL e SV."""
    g = GD
    u_b = g["wall"] + CL_SLIDE                     # faccia posteriore della slitta
    u1 = u_b + SL["D"]                             # lato aperto (a filo della faccia delle orecchie)
    vi = SL["W"] / 2 + CL_SLIDE                    # cavita'
    vo = vi + g["wall"]                            # esterno dei fianchi
    cav_top = -g["fl_t"] - g["cable_gap"]
    hi = cav_top - SL["H"] / 2                     # centro della slitta: tutta in alto ...
    lo = hi - g["travel"]                          # ... e tutta in basso
    slot_top = hi + SL["LOCK_Z"] + g["slot_w"] / 2
    slot_bot = lo - SL["LOCK_Z"] - g["slot_w"] / 2
    zb = slot_bot - 6.0                            # fondo della guida
    return dict(u_b=u_b, u1=u1, vi=vi, vo=vo, cav_top=cav_top, hi=hi, lo=lo,
                slot_top=slot_top, slot_bot=slot_bot, zb=zb, u_lock=u_b + SL["LOCK_X"])


def to_base(m):
    """guida in coordinate locali -> base (giro di 180 gradi attorno a z: x = x_back - u, y = cy - v)."""
    return m.rotate((0, 0, 180)).translate((GD["x_back"], GD["cy"], 0))


def bolts():
    """i 4 fori nella base (x, y)."""
    return [(GD["x_back"] - u, GD["cy"] - v) for v in (GD["bolt_v"], -GD["bolt_v"]) for u in GD["bolt_u"]]


def guida_locale():
    g, d = GD, dims()
    zt = -g["fl_t"]
    m = Manifold.batch_boolean([
        box((0, -g["fl_v"], zt), (d["u1"], g["fl_v"], 0.0)),                     # flangia
        box((0, -d["vo"], d["zb"]), (d["u1"], d["vo"], zt + 0.01)),               # canale
    ], ADD)
    m = m - box((d["u_b"] - CL_SLIDE, -d["vi"], d["zb"] - 1), (d["u1"] + 1, d["vi"], d["cav_top"]))   # cavita'
    for u in g["bolt_u"]:
        for v in (-g["bolt_v"], g["bolt_v"]):
            m = m - cyl(M4_FREE / 2, (u, v, zt - 1), (u, v, 1))
    # fessura delle viti di blocco su tutti e due i fianchi (la guida resta simmetrica davanti/dietro)
    m = m - slot(g["slot_w"], (d["u_lock"], 0, d["slot_top"]), (d["u_lock"], 0, d["slot_bot"]), 1,
                 -d["vo"] - 1, d["vo"] + 1)
    return m


def guida():
    return to_base(guida_locale())


def slider_range():
    """centro della slitta (z) possibile: viti di blocco dentro la fessura, cavo libero sopra la slitta."""
    d = dims()
    return d["lo"], d["hi"]


def place_slider(zc):
    """trasformazione slitta (locale) -> base, con il centro a z = zc (giro di 180 gradi attorno a z: l'orecchia
    del servo guarda verso -x, i dadi delle viti di blocco verso il davanti)."""
    T = trimesh.transformations.rotation_matrix(np.pi, (0, 0, 1))
    T[:3, 3] = (GD["x_back"] - dims()["u_b"], GD["cy"], zc)
    return T


def servo_model(albero_su=True):
    """DS3225 nella slitta (coordinate locali della slitta): albero lungo +x, asse lungo del corpo lungo z."""
    s = SV
    face = SL["D"]
    top = face + s["EAR_T"] + (s["H"] - s["EAR_Z"] - s["EAR_T"])
    zs = (s["L"] / 2 - s["SHAFT"]) * (1 if albero_su else -1)
    parts = [box((face - (s["EAR_Z"] - 0.0), -s["W"] / 2, -s["L"] / 2), (top, s["W"] / 2, s["L"] / 2)),
             box((face, -s["W"] / 2 + 1, -s["EAR_L"] / 2), (face + s["EAR_T"], s["W"] / 2 - 1, s["EAR_L"] / 2)),
             cyl(3.0, (top - 0.1, 0, zs), (top + 4.5, 0, zs)),
             box((top + 4.5, -4, zs - 4), (top + 7.5, 4, zs + 28))]
    m = Manifold.batch_boolean(parts, ADD)
    return m, zs


# ======================================================================== stampa
def pose_di_stampa():
    G = to_tm(guida())                    # flangia sul piatto, canale in su
    G.apply_transform(trimesh.transformations.rotation_matrix(np.pi, (1, 0, 0)))
    G.apply_translation(-G.bounds[0])
    S = to_tm(slitta())                   # faccia posteriore sul piatto: tasca aperta in alto
    S.apply_transform(trimesh.transformations.rotation_matrix(-np.pi / 2, (0, 1, 0)))
    S.apply_translation(-S.bounds[0])
    return {"Guida": G, "Slitta_DS3225": S}


def project_settings():
    """impostazioni del progetto Bambu: quelle dei piatti delle teste (A1 0.4, 0.20 mm, PLA Basic) con 4 pareti,
    25% gyroid e senza supporti (questi pezzi non ne hanno bisogno)."""
    src = ROOT / "mechanical" / "eyes" / "eyemech_D85" / "Testa_1" / "Piatto_3" / "Piatto_3.3mf"
    with zipfile.ZipFile(src) as z:
        d = json.loads(z.read("Metadata/project_settings.config"))
    over = {"enable_support": "0", "wall_loops": "4", "sparse_infill_density": "25%",
            "sparse_infill_pattern": "gyroid", "curr_bed_type": "Textured PEI Plate"}
    d.update(over)
    diff = list(d.get("different_settings_to_system", ["", "", ""])) + ["", "", ""]
    diff[0] = ";".join(sorted(k for k in over if k != "curr_bed_type"))
    d["different_settings_to_system"] = diff[:3]
    return json.dumps(d, indent=4, ensure_ascii=False)


def write_3mf(path, names, meshes, title, png=None):
    U = lambda a, b: f"{a:08x}-{b}"
    objs, items, cfg, rels = [], [], [], []
    files = {}
    for k, (name, m) in enumerate(zip(names, meshes), start=1):
        c = (m.bounds[0] + m.bounds[1]) / 2
        v = m.vertices - c
        verts = "\n".join(f'     <vertex x="{x:.6f}" y="{y:.6f}" z="{z:.6f}"/>' for x, y, z in v)
        tris = "\n".join(f'     <triangle v1="{a}" v2="{b}" v3="{cc}"/>' for a, b, cc in m.faces)
        oid, wid = 2 * k - 1, 2 * k
        files[f"3D/Objects/object_{k}.model"] = (
            '<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" '
            'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
            'xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" '
            'xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" requiredextensions="p">\n'
            ' <metadata name="BambuStudio:3mfVersion">1</metadata>\n <resources>\n'
            f'  <object id="{oid}" p:UUID="{U(k << 16, "81cb-4c03-9d28-80fed5dfa1dc")}" type="model">\n'
            f'   <mesh>\n    <vertices>\n{verts}\n    </vertices>\n    <triangles>\n{tris}\n    </triangles>\n'
            '   </mesh>\n  </object>\n </resources>\n <build/>\n</model>\n')
        t = f"1 0 0 0 1 0 0 0 1 {c[0]:.6f} {c[1]:.6f} {c[2]:.6f}"
        objs.append(f'  <object id="{wid}" p:UUID="{U(k, "61cb-4c03-9d28-80fed5dfa1dc")}" type="model">\n'
                    f'   <components>\n    <component p:path="/3D/Objects/object_{k}.model" objectid="{oid}" '
                    f'p:UUID="{U(k << 16, "b206-40ff-9872-83e8017abed1")}" transform="{t}"/>\n   </components>\n  </object>')
        items.append(f'  <item objectid="{wid}" p:UUID="{U(wid, "b1ec-4553-aec9-835e5b724bb4")}" '
                     'transform="1 0 0 0 1 0 0 0 1 0 0 0" printable="1"/>')
        rels.append(f' <Relationship Target="/3D/Objects/object_{k}.model" Id="rel-{k}" '
                    'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>')
        nm = f"{k - 1:02d}_{name}"
        mat = f"1 0 0 {c[0]:.6f} 0 1 0 {c[1]:.6f} 0 0 1 {c[2]:.6f} 0 0 0 1"
        cfg.append(f'  <object id="{wid}">\n    <metadata key="name" value="{nm}"/>\n    <metadata key="extruder" value="1"/>\n'
                   f'    <part id="{oid}" subtype="normal_part">\n      <metadata key="name" value="{nm}"/>\n'
                   f'      <metadata key="matrix" value="{mat}"/>\n      <metadata key="source_file" value="{nm}.stl"/>\n'
                   '    </part>\n  </object>')
    files["3D/3dmodel.model"] = (
        '<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" '
        'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
        'xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" '
        'xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" requiredextensions="p">\n'
        ' <metadata name="Application">BambuStudio-02.05.00.66</metadata>\n'
        ' <metadata name="BambuStudio:3mfVersion">1</metadata>\n'
        f' <metadata name="Title">{title}</metadata>\n <resources>\n' + "\n".join(objs) + "\n </resources>\n"
        f' <build p:UUID="{uuid.uuid4()}">\n' + "\n".join(items) + "\n </build>\n</model>\n")
    files["3D/_rels/3dmodel.model.rels"] = ('<?xml version="1.0" encoding="UTF-8"?>\n<Relationships '
                                            'xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
                                            + "\n".join(rels) + "\n</Relationships>\n")
    thumb = '    <metadata key="thumbnail_file" value="Metadata/plate_1.png"/>\n' if png else ""
    files["Metadata/model_settings.config"] = (
        '<?xml version="1.0" encoding="UTF-8"?>\n<config>\n' + "\n".join(cfg) +
        '\n  <plate>\n    <metadata key="plater_id" value="1"/>\n    <metadata key="plater_name" value=""/>\n'
        '    <metadata key="locked" value="false"/>\n' + thumb + '  </plate>\n  <assemble>\n  </assemble>\n</config>\n')
    files["Metadata/project_settings.config"] = project_settings()
    files["Metadata/slice_info.config"] = (
        '<?xml version="1.0" encoding="UTF-8"?>\n<config>\n  <header>\n'
        '    <header_item key="X-BBL-Client-Type" value="slicer"/>\n'
        '    <header_item key="X-BBL-Client-Version" value="02.05.00.66"/>\n  </header>\n</config>\n')
    rel_thumb = ('\n <Relationship Target="/Metadata/plate_1.png" Id="rel-2" '
                 'Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/thumbnail"/>' if png else "")
    files["_rels/.rels"] = ('<?xml version="1.0" encoding="UTF-8"?>\n<Relationships '
                            'xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
                            ' <Relationship Target="/3D/3dmodel.model" Id="rel-1" '
                            'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>' + rel_thumb +
                            "\n</Relationships>\n")
    files["[Content_Types].xml"] = (
        '<?xml version="1.0" encoding="UTF-8"?>\n<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\n'
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


def piatto(nome, n_set, P):
    """n_set guide in fila e le slitte davanti, 5 mm tra i pezzi e dal bordo."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    G, S = P["Guida"], P["Slitta_DS3225"]
    names, meshes = [], []
    gx, gy = G.extents[:2]
    S = S.copy()                          # slitte girate di 90 gradi: in fila davanti alle guide
    S.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, (0, 0, 1)))
    S.apply_translation(-S.bounds[0])
    for i in range(n_set):
        g = G.copy()
        g.apply_translation((5 + i * (gx + 6), 5, 0))
        s = S.copy()
        s.apply_translation((5 + i * (gx + 6) + (gx - S.extents[0]) / 2, 5 + gy + 6, 0))
        names += ["Guida", "Slitta_DS3225"]
        meshes += [g, s]
    hi = np.max([m.bounds[1] for m in meshes], axis=0)
    assert hi[0] <= 251 and hi[1] <= 251 and hi[2] <= 250, (nome, hi)
    out = HERE / "stampa"
    (out / "anteprime").mkdir(parents=True, exist_ok=True)
    png = out / "anteprime" / f"{nome}.png"
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.add_patch(plt.Rectangle((0, 0), 256, 256, fc="#eeeeee", ec="k"))
    for nm, m in zip(names, meshes):
        lo, hi2 = m.bounds
        ax.add_patch(plt.Rectangle(lo[:2], *(hi2 - lo)[:2], fc="#2f6fd6" if nm == "Guida" else "#9b3fc4", alpha=.7))
        ax.text(*(lo[:2] + (hi2 - lo)[:2] / 2), nm.replace("_DS3225", ""), ha="center", va="center", fontsize=7)
    ax.set_xlim(-5, 261)
    ax.set_ylim(-5, 261)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(f"{nome}: {n_set} set (guida + slitta)")
    fig.savefig(png, dpi=80, bbox_inches="tight")
    plt.close(fig)
    write_3mf(out / f"{nome}.3mf", names, meshes, nome, png=png)
    return meshes


def export():
    P = pose_di_stampa()
    (HERE / "pezzi").mkdir(exist_ok=True)
    for n, m in P.items():
        assert m.is_watertight, n
        m.export(HERE / "pezzi" / f"{n}.stl")
        print(f"{n:14s} {np.round(m.extents, 1).tolist()}  {m.volume / 1000:.1f} cm3")
    for nome, n in (("Mandibola_supporto_1_set", 1), ("Mandibola_supporto_4_set", 4)):
        piatto(nome, n, P)
        print("piatto", nome)
    lo, hi = slider_range()
    d = dims()
    print(f"corsa della slitta {hi - lo:.0f} mm (centro da z = {hi:.0f} a {lo:.0f}); albero del servo da "
          f"{-(hi + 10):.0f} a {-(lo + 10):.0f} mm sotto il fondo della base (albero in alto) o da "
          f"{-(hi - 10):.0f} a {-(lo - 10):.0f} (albero in basso); guida alta {-d['zb']:.1f} mm")
    print("fori nella base:", [(round(x, 1), round(y, 1)) for x, y in bolts()])


if __name__ == "__main__":
    export()
