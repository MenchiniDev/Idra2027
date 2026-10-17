"""
Prepara i progetti .3mf per Bambu Studio (piatto 256 x 256 mm: X1 / P1 / A1) della coppia di
occhi a 2 servo MG995: pezzi orientati per la stampa e distribuiti su piu' piatti, un file per piatto.

Uso:  python make_print_3mf.py            -> taglia D50
      python make_print_3mf.py 70         -> taglia D70
Output: mechanical/print/MG995_D<taglia>/Piatto_N_<contenuto>.3mf
"""
import sys
from pathlib import Path

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[1]
EYES = ROOT / "eyes" / "scaled"
BED = 256.0                # piatto Bambu X1/P1/A1
MARGIN = 8.0               # bordo libero sul piatto
GAP = 6.0                  # distanza tra i pezzi


def parts(D):
    """(nome, file, copie, orientamento) — orientamento: 'flat' = cosi' com'e',
    'ydown' = retro (-Y) sul piatto, 'xdown' = faccia -X sul piatto (pezzi piatti nel piano YZ),
    'auto' = sceglie la posa con meno sbalzi."""
    t = f"D{D}"
    m, d = EYES / "double_2servo_mg995" / t, EYES / "double" / t
    return [
        ("BasePlate", m / f"BasePlate_Double_MG995_{t}.stl", 1, "flat"),
        ("Eyeball", d / f"Eyeball_{t}_x2.stl", 2, "ydown"),
        ("BallJoint", d / f"EyeBall_Ball_Joint_{t}_x2.stl", 2, "ydown"),
        ("EyelidUpL", d / f"Eyelid_Upper_L_{t}.stl", 1, "auto"),
        ("EyelidUpR", d / f"Eyelid_Upper_R_{t}.stl", 1, "auto"),
        ("EyelidLoL", d / f"Eyelid_Lower_L_{t}.stl", 1, "auto"),
        ("EyelidLoR", d / f"Eyelid_Lower_R_{t}.stl", 1, "auto"),
        ("LinkUpL", d / f"Linkage_Upper_L_{t}.stl", 1, "auto"),
        ("LinkUpR", d / f"Linkage_Upper_R_{t}.stl", 1, "auto"),
        ("LinkLoL", d / f"Linkage_Lower_L_{t}.stl", 1, "auto"),
        ("LinkLoR", d / f"Linkage_Lower_R_{t}.stl", 1, "auto"),
        ("LidCrankL", d / f"LidCrank_L_{t}.stl", 1, "xdown"),
        ("LidCrankR", m / f"LidCrank_R_Pivot_{t}.stl", 1, "xdown"),
        ("LidBail", m / f"LidBail_{t}.stl", 1, "auto"),
        ("XHorn", m / f"XHorn_MG995_{t}.stl", 1, "flat"),
    ]


def overhang(m, limit_deg=45.0):
    """Area (mm^2) delle facce a sbalzo oltre limit_deg che non poggiano sul piatto."""
    n = m.face_normals
    z0 = m.bounds[0, 2]
    on_bed = m.triangles[:, :, 2].max(axis=1) < z0 + 0.3
    down = n[:, 2] < -np.cos(np.radians(limit_deg))
    return float(m.area_faces[down & ~on_bed].sum())


def best_pose(m):
    """Prova le 6 pose sugli assi principali + le pose stabili; tiene quella con meno
    sbalzi (a parita', la piu' bassa)."""
    cands = []
    for ax, ang in (([1, 0, 0], 0), ([1, 0, 0], np.pi / 2), ([1, 0, 0], -np.pi / 2),
                    ([1, 0, 0], np.pi), ([0, 1, 0], np.pi / 2), ([0, 1, 0], -np.pi / 2)):
        cands.append(trimesh.transformations.rotation_matrix(ang, ax))
    try:
        Ts, _ = trimesh.poses.compute_stable_poses(m, n_samples=1)
        cands += list(Ts[:6])
    except Exception:
        pass
    best = None
    for T in cands:
        c = m.copy()
        c.apply_transform(T)
        c.apply_translation(-c.bounds[0])
        score = (round(overhang(c) / 50.0), c.extents[2])
        if best is None or score < best[0]:
            best = (score, c)
    return best[1]


POSE = {
    "ydown": trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]),    # z' = y
    "xdown": trimesh.transformations.rotation_matrix(-np.pi / 2, [0, 1, 0]),   # z' = x
}


def footprint_min(m):
    """Ruota attorno a Z per minimizzare l'ingombro sul piatto (passi di 15 deg)."""
    best = None
    for a in range(0, 180, 15):
        c = m.copy()
        c.apply_transform(trimesh.transformations.rotation_matrix(np.radians(a), [0, 0, 1]))
        area = c.extents[0] * c.extents[1]
        if best is None or area < best[0] - 1e-6:
            best = (area, c)
    c = best[1]
    if c.extents[1] > c.extents[0]:             # lato lungo lungo X
        c.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 0, 1]))
    c.apply_translation(-c.bounds[0])
    return c


def pack(items):
    """Impaccamento a ripiani: lista di (nome, mesh) -> lista di piatti [(nome, mesh)]."""
    items = sorted(items, key=lambda it: -it[1].extents[1])
    use = BED - 2 * MARGIN
    plates, cur, x, y, shelf_h = [], [], 0.0, 0.0, 0.0
    for name, m in items:
        w, h = m.extents[0], m.extents[1]
        if w > use or h > use:
            raise SystemExit(f"{name} ({w:.0f} x {h:.0f} mm) non entra nel piatto {BED:.0f} mm")
        if x + w > use:                          # nuovo ripiano
            x, y, shelf_h = 0.0, y + shelf_h + GAP, 0.0
        if y + h > use:                          # nuovo piatto
            plates.append(cur)
            cur, x, y, shelf_h = [], 0.0, 0.0, 0.0
        p = m.copy()
        p.apply_translation([MARGIN + x, MARGIN + y, 0])
        cur.append((name, p))
        x += w + GAP
        shelf_h = max(shelf_h, h)
    if cur:
        plates.append(cur)
    return plates


def main():
    D = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    out = ROOT / "print" / f"MG995_D{D}"
    out.mkdir(parents=True, exist_ok=True)
    for f in out.glob("*.3mf"):
        f.unlink()

    # piatto 0: provino della sede MG995, da stampare per primo
    fit = trimesh.load(EYES / "double_2servo_mg995" / "MG995_FitTest.stl")
    fit.apply_translation(-fit.bounds[0] + [BED / 2 - fit.extents[0] / 2, BED / 2 - fit.extents[1] / 2, 0])
    scene = trimesh.Scene()
    scene.add_geometry(fit, node_name="MG995_FitTest", geom_name="MG995_FitTest")
    scene.export(out / "Piatto_0_PROVA_sede_MG995.3mf")
    print("Piatto 0: MG995_FitTest")

    items = []
    for name, path, n, mode in parts(D):
        m = trimesh.load(path)
        if mode == "auto":
            m = best_pose(m)
        elif mode in POSE:
            m = m.copy()
            m.apply_transform(POSE[mode])
        m = footprint_min(m)
        for i in range(n):
            items.append((f"{name}_{i + 1}" if n > 1 else name, m))

    # la piastra da sola (stampa lunga: se fallisce non si perdono gli altri pezzi)
    base = [it for it in items if it[0] == "BasePlate"]
    rest = [it for it in items if it[0] != "BasePlate"]
    for i, plate in enumerate(pack(base) + pack(rest), start=1):
        scene = trimesh.Scene()
        for name, m in plate:
            scene.add_geometry(m, node_name=name, geom_name=name)
        tag = "Piastra" if any(n == "BasePlate" for n, _ in plate) else "pezzi"
        scene.export(out / f"Piatto_{i}_{tag}.3mf")
        print(f"Piatto {i}: " + ", ".join(n for n, _ in plate))


if __name__ == "__main__":
    main()
