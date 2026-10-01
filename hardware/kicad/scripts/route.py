"""Autorouting con Freerouting + piani di massa + riempimento zone (python di KiCad)."""
import subprocess, sys
from pathlib import Path
import pcbnew
sys.path.insert(0, str(Path(__file__).parent))
import eyenode_design as D

OUT = Path(__file__).resolve().parents[1] / D.PROJECT
PCB = OUT / f"{D.PROJECT}.kicad_pcb"
JAR = Path.home() / "tools" / "fr-2.1.0.jar"
mm = pcbnew.FromMM


def add_zone(b, layer, net, prio=0):
    z = pcbnew.ZONE(b)
    z.SetLayer(layer)
    z.SetNet(b.FindNet(net) or b.FindNet("/" + net))
    z.SetAssignedPriority(prio)
    z.SetLocalClearance(mm(0.4))
    z.SetMinThickness(mm(0.25))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetThermalReliefGap(mm(0.5))
    z.SetThermalReliefSpokeWidth(mm(0.6))
    ol = z.Outline()
    ol.NewOutline()
    for x, y in ((0.5, 0.5), (109.5, 0.5), (109.5, 89.5), (0.5, 89.5)):
        ol.Append(mm(x), mm(y))
    b.Add(z)


def main():
    b = pcbnew.LoadBoard(str(PCB))
    dsn, ses = OUT / "EyeNode.dsn", OUT / "EyeNode.ses"
    pcbnew.ExportSpecctraDSN(b, str(dsn))
    cmd = ["java", "-jar", str(JAR), "-de", str(dsn), "-do", str(ses), "-mp", "40", "--gui.enabled=false"]
    print(" ".join(cmd))
    subprocess.run(cmd, check=True, timeout=1800)
    b = pcbnew.LoadBoard(str(PCB))
    pcbnew.ImportSpecctraSES(b, str(ses))
    # rimuove (una sola passata, prima dei piani) gli spezzoni con un estremo libero
    b.BuildConnectivity()
    con = b.GetConnectivity()
    dang = [t for t in b.GetTracks() if t.Type() == pcbnew.PCB_TRACE_T and con.TestTrackEndpointDangling(t, False)]
    for t in dang:
        b.Remove(t)
    print("rimossi spezzoni:", len(dang))
    add_zone(b, pcbnew.B_Cu, "GND")
    add_zone(b, pcbnew.F_Cu, "GND")
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(str(PCB), b)
    print("tracks:", len(b.GetTracks()))


if __name__ == "__main__":
    main()
