"""
Dispone tutti i pezzi di una versione (idra_version o eyemech_D85) su piatti Bambu A1 (256 x 256)
e li taglia con Bambu Studio da riga di comando: stampa in meno piatti possibile.

Uso:  python pack_plate.py idra_version            (tutti i pezzi su 1 piatto)
      python pack_plate.py idra_version --gap 8     (piu' spazio tra i pezzi, per supporti larghi)
      python pack_plate.py eyemech_D85 --plates 8   (D85: i pezzi grandi hanno gia' i loro piatti in
                                                     bambu_A1, qui solo come prova di impacchettamento)

Impacchettamento: rettangoli degli ingombri xy (rotazioni di 90 gradi consentite), ordine per
area decrescente con scambi casuali finche' ci stanno. Il risultato (3MF gia' tagliato, con tempo e
filamento) va in mechanical/eyes/<versione>/bambu_A1/. Profili: stampante/processo/filamento che
Bambu Studio ha selezionati (A1 0.4, 0.20mm Standard, PLA Basic) con supporti tree(auto) 30 gradi.
"""
import argparse
import json
import os
import random
import re
import subprocess
import tempfile
import zipfile
from pathlib import Path

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[2]
BAMBU = Path(r"C:\Program Files\Bambu Studio")
BED, MARGIN = 256.0, 3.0


def pack(items, nplates, gap, tries=20000, seed=1):
    """posizioni (id, piatto, rotazione, x, y) o None."""
    def one(order):
        free = [[(MARGIN, MARGIN, BED - 2 * MARGIN, BED - 2 * MARGIN)] for _ in range(nplates)]
        res = []
        for it in order:
            best = None
            for b in range(nplates):
                for rot in (0, 1):
                    w, h = (it["w"], it["h"]) if not rot else (it["h"], it["w"])
                    w += gap
                    h += gap
                    for (x, y, fw, fh) in free[b]:
                        if w <= fw + gap and h <= fh + gap:
                            sc = (b, y + h, x)
                            if best is None or sc < best[0]:
                                best = (sc, b, rot, x, y, w, h)
            if best is None:
                return None
            _, b, rot, x, y, w, h = best
            res.append((it["id"], b, rot, x, y))
            new = []
            for (fx, fy, fw, fh) in free[b]:
                if x >= fx + fw or x + w <= fx or y >= fy + fh or y + h <= fy:
                    new.append((fx, fy, fw, fh))
                    continue
                if x > fx:
                    new.append((fx, fy, x - fx, fh))
                if x + w < fx + fw:
                    new.append((x + w, fy, fx + fw - (x + w), fh))
                if y > fy:
                    new.append((fx, fy, fw, y - fy))
                if y + h < fy + fh:
                    new.append((fx, y + h, fw, fy + fh - (y + h)))
            free[b] = [r for i, r in enumerate(new) if not any(
                j != i and r[0] >= s[0] and r[1] >= s[1] and r[0] + r[2] <= s[0] + s[2]
                and r[1] + r[3] <= s[1] + s[3] for j, s in enumerate(new))]
        return res

    rnd = random.Random(seed)
    base = sorted(items, key=lambda it: -(it["w"] * it["h"]))
    for t in range(tries):
        order = base[:]
        if t:
            for _ in range(rnd.randint(1, 6)):
                i, j = rnd.randrange(len(order)), rnd.randrange(len(order))
                order[i], order[j] = order[j], order[i]
        r = one(order)
        if r:
            return r
    return None


def profiles(tmp):
    """profili A1 0.4 / 0.20mm Standard / PLA Basic di Bambu Studio, in JSON piatto."""
    B = BAMBU / "resources" / "profiles" / "BBL"

    def load(kind, name):
        d = json.load(open(B / kind / f"{name}.json", encoding="utf-8"))
        if d.get("inherits"):
            base = load(kind, d["inherits"])
            base.update(d)
            d = base
        return d

    m = load("machine", "Bambu Lab A1 0.4 nozzle")
    p = load("process", "0.20mm Standard @BBL A1")
    f = load("filament", "Bambu PLA Basic @BBL A1")
    p.update({"enable_support": "1", "support_type": "tree(auto)", "support_threshold_angle": "30"})
    paths = []
    for d, n in ((m, "machine"), (p, "process"), (f, "filament")):
        d.pop("inherits", None)
        d["from"] = "system" if n != "process" else "user"
        q = Path(tmp) / f"{n}.json"
        json.dump(d, open(q, "w", encoding="utf-8"), indent=1)
        paths.append(str(q))
    return paths


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("version", help="cartella in mechanical/eyes (idra_version, eyemech_D85)")
    ap.add_argument("--plates", type=int, default=1)
    ap.add_argument("--gap", type=float, default=6.0, help="mm tra i pezzi (supporti, brim)")
    a = ap.parse_args()
    d = ROOT / "mechanical" / "eyes" / a.version
    # pezzi: tutti gli STL della cartella; i multipli (_x2, _x3) vengono ripetuti
    files = []
    for f in sorted(d.glob("*.stl")):
        n = re.search(r"_x(\d)$", f.stem)
        files += [f] * (int(n.group(1)) if n else 1)
    items = []
    for i, f in enumerate(files):
        e = trimesh.load(f).extents
        items.append(dict(id=i, w=float(e[0]), h=float(e[1])))
    place = pack(items, a.plates, a.gap)
    if place is None:
        raise SystemExit(f"i {len(files)} pezzi non stanno su {a.plates} piatto/i con gap {a.gap}")
    with tempfile.TemporaryDirectory() as tmp:
        for b in range(a.plates):
            sub = Path(tmp) / f"p{b + 1}"
            sub.mkdir()
            for (i, bb, rot, x, y) in place:
                if bb != b:
                    continue
                m = trimesh.load(files[i])
                if rot:
                    m.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 0, 1]))
                lo = m.bounds[0]
                m.apply_translation([x - lo[0], y - lo[1], -lo[2]])
                m.export(sub / f"{i:02d}_{files[i].stem}.stl")
            out = d / "bambu_A1"
            out.mkdir(exist_ok=True)
            name = f"{a.version}_Piatto_unico.3mf" if a.plates == 1 else f"{a.version}_Piatto_{b + 1}.3mf"
            m_, p_, f_ = profiles(tmp)
            cmd = [str(BAMBU / "bambu-studio.exe"), "--slice", "0", "--arrange", "0", "--orient", "0",
                   "--load-settings", f"{m_};{p_}", "--load-filaments", f_,
                   "--outputdir", str(sub / "out"), "--export-3mf", name,
                   *map(str, sorted(sub.glob("*.stl")))]
            subprocess.run(cmd, capture_output=True, check=True)
            os.replace(sub / "out" / name, out / name)
            z = zipfile.ZipFile(out / name)
            s = z.read("Metadata/slice_info.config").decode()
            t = int(re.search(r'key="prediction" value="(\d+)"', s).group(1))
            w = float(re.search(r'key="weight" value="([\d.]+)"', s).group(1))
            print(f"piatto {b + 1}: {len(list(sub.glob('*.stl')))} pezzi, {t // 3600} h {(t % 3600) // 60:02d} min, {w:.0f} g -> {out / name}")


if __name__ == "__main__":
    main()
