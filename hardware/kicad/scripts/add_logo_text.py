"""Aggiunge la scritta del carro sulla serigrafia del PCB esistente (senza rifare il routing)."""
from pathlib import Path
import pcbnew

PCB = Path(__file__).resolve().parents[1] / "EyeNode" / "EyeNode.kicad_pcb"
TEXTS = [("L'IDRA", 53.0, 45.6, 2.6, 0.4), ("carnevale di viareggio 2027", 53.0, 49.6, 1.5, 0.25)]


def main():
    b = pcbnew.LoadBoard(str(PCB))
    for t in list(b.Drawings()):
        if isinstance(t, pcbnew.PCB_TEXT) and t.GetText() in [x[0] for x in TEXTS]:
            b.Remove(t)
    for txt, x, y, size, th in TEXTS:
        t = pcbnew.PCB_TEXT(b)
        t.SetText(txt)
        t.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
        t.SetLayer(pcbnew.F_SilkS)
        t.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(size), pcbnew.FromMM(size)))
        t.SetTextThickness(pcbnew.FromMM(th))
        t.SetBold(True)
        b.Add(t)
    pcbnew.SaveBoard(str(PCB), b)


if __name__ == "__main__":
    main()
