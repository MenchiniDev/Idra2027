"""Genera EyeNode.kicad_pcb (da eseguire con il python di KiCad).
Piazzamento fisso, reti da netmap.json (prodotto da gen_sch.py), nessuna pista:
il routing lo fa route.py (Freerouting) e poi si aggiungono i piani di massa."""
import json
import sys
import uuid
from pathlib import Path

import pcbnew

sys.path.insert(0, str(Path(__file__).parent))
import eyenode_design as D  # noqa: E402

FPLIB = Path(r"C:/Program Files/KiCad/10.0/share/kicad/footprints")
OUT = Path(__file__).resolve().parents[1] / D.PROJECT
NS = uuid.UUID("6f1c2a52-0d0e-4d55-9a70-1d7a1e0c0de5")
W, H = 110.0, 90.0

# (x, y, rot) — origine footprint = pad 1 per i THT, centro per gli SMD
SERVO_Y = [10, 17, 24, 35, 42, 49]
PLACE = {
    "J1": (5.5, 12.0, 270), "F1": (17.0, 6.0, 0), "D1": (25.0, 6.0, 180), "C4": (31.0, 15.0, 0),
    "U1": (33.0, 9.5, 0), "C5": (43.0, 15.0, 0),
    "A1": (35.0, 40.0, 90),
    "J2": (5.5, 55.0, 270), "F2": (16.0, 55.0, 0), "D2": (35.0, 64.0, 0),
    "C1": (45.0, 60.0, 0), "C2": (60.0, 60.0, 0),
    "R10": (72.0, 57.0, 0), "D3": (72.0, 61.0, 180),
    "R11": (79.0, 55.0, 90), "R12": (79.0, 61.0, 90), "C3": (83.0, 61.0, 90),
    "U2": (70.0, 73.0, 0), "C6": (78.0, 73.0, 90), "R7": (62.0, 73.0, 90), "JP1": (55.0, 71.5, 0),
    "J9": (58.0, 84.0, 0), "J10": (75.0, 84.0, 0),
    "SW1": (10.0, 70.0, 0), "J11": (24.0, 86.0, 90),
    "R13": (81.0, 45.0, 0), "D4": (86.0, 45.0, 180),
}
for i, y in enumerate(SERVO_Y):
    PLACE[f"R{i + 1}"] = (91.0, y + 2.54 if False else y, 0)
    PLACE[f"J{i + 3}"] = (104.0, y, 270)
HOLES = [(3.5, 3.5), (W - 3.5, 3.5), (3.5, H - 3.5), (W - 3.5, H - 3.5)]
SILK = [("12V LOGICA\n1=+  2=GND", 8.0, 22.5), ("SERVO 5-6V\n1=+  2=GND", 8.0, 66.0),
        ("SIG V+ GND", 101.5, 5.5), ("OCCHIO A", 96.0, 30.0), ("OCCHIO B", 96.0, 55.0),
        ("IN: A  B  GND", 63.0, 78.0), ("OUT: A  B  GND", 80.0, 78.0),
        ("ADDR", 14.0, 82.5), ("+5V SDA SCL A6 GND", 29.0, 82.5),
        ("EyeNode v0.1 - Idra di Guerra", 60.0, 2.0)]


def mm(v):
    return pcbnew.FromMM(v)


def V(x, y):
    return pcbnew.VECTOR2I(mm(x), mm(y))


def U(*k):
    return str(uuid.uuid5(NS, "/".join(map(str, k))))


def main():
    # reti dalla netlist esportata da KiCad (nomi identici allo schema, es. "/GND")
    from sexp import parse, find, find1
    nl = parse((OUT / f"{D.PROJECT}.net").read_text(encoding="utf8"))
    pad2net, netmap = {}, {}
    for n in find(find1(nl, "nets"), "net"):
        name = find1(n, "name")[1]
        for node in find(n, "node"):
            rp = f"{find1(node, 'ref')[1]}.{find1(node, 'pin')[1]}"
            pad2net[rp] = name
            netmap.setdefault(name, []).append(rp)

    b = pcbnew.BOARD()
    b.SetCopperLayerCount(2)
    nets = {}
    for n in sorted(netmap):
        ni = pcbnew.NETINFO_ITEM(b, n)
        b.Add(ni)
        nets[n] = ni

    root = U("root")
    for c in D.parts:
        lib, name = c["fp"].split(":")
        fp = pcbnew.FootprintLoad(str(FPLIB / f"{lib}.pretty"), name)
        fp.SetReference(c["ref"])
        fp.SetValue(c["value"])
        x, y, r = PLACE[c["ref"]]
        fp.SetPosition(V(x, y))
        fp.SetOrientationDegrees(r)
        fp.SetPath(pcbnew.KIID_PATH(f"/{U('sym', c['ref'])}"))
        fp.SetFPIDAsString(c["fp"])
        if c["ref"] in ("J9", "J10"):
            fp.Reference().SetVisible(False)
        if c["ref"] == "D4":
            fp.Reference().SetPosition(V(x, y - 2.2))
        for p in fp.Pads():
            n = pad2net.get(f"{c['ref']}.{p.GetNumber()}")
            if n:
                p.SetNet(nets[n])
        b.Add(fp)

    for i, (x, y) in enumerate(HOLES):
        fp = pcbnew.FootprintLoad(str(FPLIB / "MountingHole.pretty"), "MountingHole_3.2mm_M3")
        ref = f"H{i + 1}"
        fp.SetReference(ref)
        fp.SetValue("M3")
        fp.SetPosition(V(x, y))
        fp.SetPath(pcbnew.KIID_PATH(f"/{U('sym', ref)}"))
        fp.SetFPIDAsString("MountingHole:MountingHole_3.2mm_M3")
        b.Add(fp)

    # contorno scheda con angoli arrotondati
    r = 3.0
    pts = [((r, 0), (W - r, 0)), ((W, r), (W, H - r)), ((W - r, H), (r, H)), ((0, H - r), (0, r))]
    for a, z in pts:
        s = pcbnew.PCB_SHAPE(b)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(V(*a))
        s.SetEnd(V(*z))
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetWidth(mm(0.1))
        b.Add(s)
    import math
    for cx, cy, sx, sy, ex, ey in ((r, r, 0, r, r, 0), (W - r, r, W - r, 0, W, r),
                                   (W - r, H - r, W, H - r, W - r, H), (r, H - r, r, H, 0, H - r)):
        mx = cx + ((sx - cx) + (ex - cx)) / math.sqrt(2)
        my = cy + ((sy - cy) + (ey - cy)) / math.sqrt(2)
        s = pcbnew.PCB_SHAPE(b)
        s.SetShape(pcbnew.SHAPE_T_ARC)
        s.SetArcGeometry(V(sx, sy), V(mx, my), V(ex, ey))
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetWidth(mm(0.1))
        b.Add(s)

    for txt, x, y in SILK:
        t = pcbnew.PCB_TEXT(b)
        t.SetText(txt)
        t.SetPosition(V(x, y))
        t.SetLayer(pcbnew.F_SilkS)
        t.SetTextSize(pcbnew.VECTOR2I(mm(1.0), mm(1.0)))
        t.SetTextThickness(mm(0.15))
        b.Add(t)

    # dorsale VSERVO pre-tracciata sui connettori servo (lato inferiore, 2 mm)
    vs = b.FindNet("/VSERVO")
    xs = PLACE["J3"][0] - 2.54
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(V(xs, SERVO_Y[0]))
    t.SetEnd(V(xs, SERVO_Y[-1]))
    t.SetWidth(mm(2.0))
    t.SetLayer(pcbnew.B_Cu)
    t.SetNet(vs)
    t.SetLocked(True)
    b.Add(t)

    path = OUT / f"{D.PROJECT}.kicad_pcb"
    pcbnew.SaveBoard(str(path), b)
    print("salvato", path)


if __name__ == "__main__":
    main()
