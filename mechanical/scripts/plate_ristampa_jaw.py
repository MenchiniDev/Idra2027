"""
Piatto Bambu A1 di ristampa (11/2026): XAxisA_PIP della D85 (rotto), 2 Eyeball D85 nuovi e il supporto
del servo mandibola (JawMount_Culla + JawMount_Testa, da generate_jaw_mount.py).
Stesso procedimento di plates_D85.py (A1 0.4, 0.20mm Standard, PLA Basic, supporti tree(auto) 30 gradi).

Uso:  python plate_ristampa_jaw.py
Uscita: mechanical/jaw/bambu_A1/Piatto_ristampa/ con Piatto_ristampa.3mf (gia' tagliato), STL posizionati
e piatto.png.
"""
import itertools
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import numpy as np
import trimesh

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pack_plate as pp
from plates_D85 import footprint, BED

ROOT = Path(__file__).resolve().parents[2]
D85 = ROOT / "mechanical" / "eyes" / "eyemech_D85"
JAW = ROOT / "mechanical" / "jaw"
OUT = JAW / "bambu_A1" / "Piatto_ristampa"
LAYOUT = [  # pezzo, file, rotazione z, angolo minimo dell'ingombro
    ("XAxisA_PIP", D85 / "XAxisA_PIP.stl", 30, 3, 3),
    ("Eyeball", D85 / "Eyeball_x2.stl", 0, 161, 3),
    ("Eyeball", D85 / "Eyeball_x2.stl", 0, 3, 109),
    ("JawMount_Culla", JAW / "JawMount_Culla.stl", 30, 77, 139),
    ("JawMount_Testa", JAW / "JawMount_Testa.stl", 120, 181, 141),
]


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        m_, p_, f_ = pp.profiles(tmp)
        loc, fps = [], []
        for i, (n, f, rot, x, y) in enumerate(LAYOUT):
            m = trimesh.load(f)
            m.apply_translation(-m.bounds[0])
            m.apply_transform(trimesh.transformations.rotation_matrix(np.radians(rot), [0, 0, 1]))
            b = m.bounds
            m.apply_translation([x - b[0, 0], y - b[0, 1], -b[0, 2]])
            lo, hi = m.bounds
            if lo[0] < 1 or lo[1] < 1 or hi[0] > BED - 1 or hi[1] > BED - 1:
                raise SystemExit(f"{n} esce dal piano ({lo.round(1)}, {hi.round(1)})")
            q = tmp / f"{i:02d}_{n}.stl"
            m.export(q)
            shutil.copy(q, OUT / q.name)
            loc.append(str(q))
            fps.append((n, footprint(m)))
        dmin = min(a[1].distance(b[1]) for a, b in itertools.combinations(fps, 2))
        name = "Piatto_ristampa.3mf"
        cmd = [str(pp.BAMBU / "bambu-studio.exe"), "--slice", "0", "--arrange", "0", "--orient", "0",
               "--load-settings", f"{m_};{p_}", "--load-filaments", f_,
               "--outputdir", str(tmp / "o"), "--export-3mf", name, *loc]
        subprocess.run(cmd, capture_output=True, check=True)
        shutil.copy(tmp / "o" / name, OUT / name)
    with zipfile.ZipFile(OUT / name) as z:
        si = z.read("Metadata/slice_info.config").decode()
    t = int(re.search(r'key="prediction" value="(\d+)"', si).group(1))
    w = float(re.search(r'key="weight" value="([\d.]+)"', si).group(1))
    print(f"distanza minima {dmin:.1f} mm; {t // 3600} h {(t % 3600) // 60:02d} min, {w:.0f} g -> {OUT / name}")
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.add_patch(plt.Rectangle((0, 0), BED, BED, fc="#eeeeee", ec="k"))
    for n, g in fps:
        for gg in getattr(g, "geoms", [g]):
            ax.fill(*gg.exterior.xy, alpha=.75)
        c = g.representative_point()
        ax.text(c.x, c.y, n.replace("_PIP", ""), ha="center", fontsize=8)
    ax.set_xlim(-5, BED + 5); ax.set_ylim(-5, BED + 5); ax.set_aspect("equal"); ax.axis("off")
    ax.set_title(f"Ristampa: {t // 3600} h {(t % 3600) // 60:02d} min, {w:.0f} g")
    fig.savefig(OUT / "piatto.png", dpi=80, bbox_inches="tight")


if __name__ == "__main__":
    main()
