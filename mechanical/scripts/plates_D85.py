"""
Piatti Bambu A1 della D85, con i pezzi incastrati sulle impronte reali (5 piatti, numerati da 0).

La disposizione (pezzo, rotazione attorno a z, angolo minimo dell'ingombro sul piatto) e' in
mechanical/eyes/eyemech_D85/bambu_A1/layout_piatti.json (un elenco per piatto, il primo e' il piatto 0);
lo script mette gli STL attuali di mechanical/eyes/eyemech_D85 in quelle posizioni, controlla che stiano
nel piano e distanti, e li taglia con Bambu Studio (A1 0.4, 0.20mm Standard, PLA Basic, supporti
tree(auto) 30 gradi).

Uso:  python plates_D85.py          (tutti i piatti)
      python plates_D85.py 2 3 4    (solo questi, es. dopo aver cambiato le squadrette)
Uscita: una cartella per piatto, bambu_A1/Piatto_<n>/, con Piatto_<n>.3mf (gia' tagliato), gli STL gia'
posizionati sul piatto (per rifare lo slicing a mano) e piatto.png con la disposizione.
Se un pezzo cambia ingombro, la disposizione va rifatta (le distanze minime vengono stampate).
"""
import itertools
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import numpy as np
import trimesh
from shapely.geometry import Polygon
from shapely.ops import unary_union

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pack_plate as pp

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "mechanical" / "eyes" / "eyemech_D85"
OUT = D / "bambu_A1"
BED = 256.0


def footprint(m):
    tri = m.vertices[m.faces][:, :, :2]
    return unary_union([Polygon(t) for t in tri if Polygon(t).area > 1e-6]).buffer(0.01)


def main():
    layout = json.load(open(OUT / "layout_piatti.json", encoding="utf-8"))
    todo = [int(a) for a in sys.argv[1:]] or list(range(len(layout)))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        m_, p_, f_ = pp.profiles(tmp)
        for k in todo:
            plate = layout[k]
            pdir = OUT / f"Piatto_{k}"
            if pdir.exists():
                shutil.rmtree(pdir)
            pdir.mkdir()
            sub = tmp / f"p{k}"
            sub.mkdir()
            loc, fps = [], []
            for i, it in enumerate(plate):
                n = it["pezzo"]
                m = trimesh.load(D / f"{n}.stl")
                m.apply_translation(-m.bounds[0])
                m.apply_transform(trimesh.transformations.rotation_matrix(np.radians(it["rot_z"]), [0, 0, 1]))
                b = m.bounds
                m.apply_translation([it["x"] - b[0, 0], it["y"] - b[0, 1], -b[0, 2]])
                lo, hi = m.bounds
                if lo[0] < 1 or lo[1] < 1 or hi[0] > BED - 1 or hi[1] > BED - 1:
                    raise SystemExit(f"piatto {k}: {n} esce dal piano ({lo.round(1)}, {hi.round(1)})")
                q = sub / f"{i:02d}_{n}.stl"
                m.export(q)
                shutil.copy(q, pdir / q.name)
                loc.append(str(q))
                fps.append((n, footprint(m)))
            dmin = min((a[1].distance(b[1]) for a, b in itertools.combinations(fps, 2)), default=99.0)
            name = f"Piatto_{k}.3mf"
            cmd = [str(pp.BAMBU / "bambu-studio.exe"), "--slice", "0", "--arrange", "0", "--orient", "0",
                   "--load-settings", f"{m_};{p_}", "--load-filaments", f_,
                   "--outputdir", str(sub / "o"), "--export-3mf", name, *loc]
            subprocess.run(cmd, capture_output=True, check=True)
            shutil.copy(sub / "o" / name, pdir / name)
            with zipfile.ZipFile(pdir / name) as z:
                si = z.read("Metadata/slice_info.config").decode()
            t = int(re.search(r'key="prediction" value="(\d+)"', si).group(1))
            w = float(re.search(r'key="weight" value="([\d.]+)"', si).group(1))
            print(f"piatto {k}: {', '.join(n for n, _ in fps)}; distanza minima {dmin:.1f} mm; "
                  f"{t // 3600} h {(t % 3600) // 60:02d} min, {w:.0f} g")
            fig, ax = plt.subplots(figsize=(6, 6))
            ax.add_patch(plt.Rectangle((0, 0), BED, BED, fc="#eeeeee", ec="k"))
            for n, g in fps:
                for gg in getattr(g, "geoms", [g]):
                    ax.fill(*gg.exterior.xy, alpha=.75)
                c = g.representative_point()
                ax.text(c.x, c.y, n.replace("_PIP", "").replace("_x2", ""), ha="center", fontsize=8)
            ax.set_xlim(-5, BED + 5); ax.set_ylim(-5, BED + 5); ax.set_aspect("equal"); ax.axis("off")
            ax.set_title(f"D85 piatto {k}: {t // 3600} h {(t % 3600) // 60:02d} min, {w:.0f} g")
            fig.savefig(pdir / "piatto.png", dpi=80, bbox_inches="tight")
            plt.close(fig)


if __name__ == "__main__":
    main()
