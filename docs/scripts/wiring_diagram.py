"""Schema di cablaggio complessivo dell'Idra (disegno concettuale)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Ellipse, Circle, PathPatch
from matplotlib.path import Path as MPath
import numpy as np
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "img" / "schema_cablaggio_idra.png"
RED, BLK, BLUE, ORG, GRN, PUR = "#d62728", "#222222", "#1f5fd6", "#f08a00", "#2a9d4b", "#8e44ad"
SKIN, SKIN_E = "#cfe3c4", "#6a8f5a"

fig, ax = plt.subplots(figsize=(22, 14))
ax.set_xlim(0, 140); ax.set_ylim(-3, 90); ax.set_aspect("equal"); ax.axis("off")


def box(x, y, w, h, txt, fc="white", ec=BLK, fs=8.5, bold=False, z=5):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.25,rounding_size=0.8",
                                fc=fc, ec=ec, lw=1.4, zorder=z))
    ax.text(x + w / 2, y + h / 2, txt, ha="center", va="center", fontsize=fs, zorder=z + 1,
            fontweight="bold" if bold else "normal")


def bez(p0, p1, p2, p3, n=60):
    t = np.linspace(0, 1, n)[:, None]
    return (1 - t) ** 3 * np.array(p0) + 3 * (1 - t) ** 2 * t * np.array(p1) + 3 * (1 - t) * t ** 2 * np.array(p2) + t ** 3 * np.array(p3)


def wire(pts, color, lw=2.2, ls="-", z=3):
    pts = np.array(pts)
    ax.plot(pts[:, 0], pts[:, 1], color=color, lw=lw, ls=ls, zorder=z, solid_capstyle="round")


# ------------------------------------------------------------------ corpo
ax.add_patch(Ellipse((52, 14), 92, 24, fc=SKIN, ec=SKIN_E, lw=3, zorder=1))
ax.text(52, -1.8, "CORPO DELL'IDRA  (vano tecnico in basso)", ha="center", fontsize=13, fontweight="bold", color=SKIN_E)

# ------------------------------------------------------------------ colli e teste
heads = [  # (x testa, y testa, base collo x, nome, coppia?)
    (20, 62, 30, "TESTA 1", True),
    (45, 74, 44, "TESTA 2", True),
    (72, 72, 60, "TESTA 3", True),
    (96, 58, 74, "TESTA 4", False),
]
for hx, hy, bx, name, pair in heads:
    c = bez((bx, 22), (bx, 38), (hx, hy - 22), (hx, hy - 6))
    for off, col, lw in ((0, SKIN_E, 40), (0, SKIN, 34)):
        ax.plot(c[:, 0], c[:, 1], color=col, lw=lw, solid_capstyle="round", zorder=1)
    ax.add_patch(Ellipse((hx, hy + 2), 26, 17, fc=SKIN, ec=SKIN_E, lw=3, zorder=1.5))
    ax.text(hx, hy + 12.2, name + ("  —  coppia di occhi" if pair else "  —  occhio singolo"),
            ha="center", fontsize=11, fontweight="bold", color="#33502a", zorder=6)
    eyes = [hx - 6, hx + 6] if pair else [hx]
    for ex in eyes:
        ax.add_patch(Circle((ex, hy + 6), 3.2, fc="white", ec=BLK, lw=1.5, zorder=6))
        ax.add_patch(Circle((ex, hy + 6), 1.3, fc="#2b6cb0", ec=BLK, lw=0.8, zorder=7))
        ax.add_patch(Circle((ex, hy + 6), 0.55, fc=BLK, zorder=8))
    # contenuti della testa
    box(hx - 11.5, hy - 3.2, 10.5, 4.6, "DC-DC\n12V → 6V 10A", fc="#fff2cc", fs=7.5, z=6)
    box(hx + 1.0, hy - 3.2, 10.5, 4.6, "EyeNode\n" + ("6 servo" if pair else "3 servo"), fc="#d9ead3", fs=7.5, bold=True, z=6)
    # servo -> occhi
    for ex in eyes:
        wire([(hx + 6.2, hy + 1.4), (ex, hy + 2.8)], ORG, lw=2.6, z=5.5)
    # DC-DC -> EyeNode
    wire([(hx - 1.0, hy - 0.9), (hx + 1.0, hy - 0.9)], PUR, lw=3.0, z=5.5)
    ax.text(hx, hy - 5.4, "12V anche a J1 (logica)", ha="center", fontsize=6.8, color=RED, zorder=7)

# ------------------------------------------------------------------ vano tecnico nel corpo
box(12, 7.5, 15, 9, "BATTERIA\nLiFePO4 12V 50Ah\n(o 2×25Ah in parallelo)", fc="#f4cccc", fs=8.5, bold=True)
box(29.5, 12.2, 9, 4.3, "SEZIONATORE\ngenerale 50A", fc="#eeeeee", fs=7.5)
box(29.5, 7.0, 9, 4.3, "FUSIBILE\nATO/MIDI 20A", fc="#eeeeee", fs=7.5)
box(41, 7.0, 14, 9.5, "SCATOLA FUSIBILI\n(blocco 6 vie ATO)\n4 × 5A → teste\n1 × 3A → master", fc="#fff2cc", fs=8)
box(58, 7.0, 14, 9.5, "MASTER (opz.)\nEyeNode ADDR 0000\no ESP32 + MAX485\n(telecomando, sincronia)", fc="#cfe2f3", fs=8)
box(75, 7.0, 13, 9.5, "Presa ricarica\n+ caricabatterie\nLiFePO4 14.6V\n(a carro fermo)", fc="#eeeeee", fs=7.5)
wire([(27, 13), (29.5, 14.3)], RED, 3.5); wire([(34, 12.2), (34, 11.3)], RED, 3.5); wire([(38.5, 9.2), (41, 9.2)], RED, 3.5)
wire([(27, 9), (28.2, 9), (28.2, 5.2), (48, 5.2), (48, 7.0)], BLK, 3.5)
wire([(55, 12), (58, 12)], RED, 2.0)
wire([(75, 11.5), (72, 11.5)], "#888888", 1.5, ls="--")

# ------------------------------------------------------------------ cavi su per i colli
for i, (hx, hy, bx, name, pair) in enumerate(heads):
    c = bez((bx, 22), (bx, 38), (hx, hy - 22), (hx, hy - 6))
    # alimentazione 12V: scatola fusibili -> base del collo -> su per il collo -> DC-DC
    fx = 43 + i * 3.2
    p = np.vstack([[(fx, 16.5), (fx, 19.5), (bx - 1.4, 21)], c + np.array([-1.4, 0]), [(hx - 6.2, hy - 3.2)]])
    wire(p, RED, 2.4, z=2.5)
    wire(p + np.array([0.7, 0]), BLK, 2.4, z=2.5)
    # RS-485 (CAT5 con coppia IN e coppia OUT): master -> collo -> EyeNode
    mx = 60 + i * 3.2
    q = np.vstack([[(mx, 16.5), (mx, 19.0), (bx + 1.6, 21)], c + np.array([1.6, 0]), [(hx + 6.2, hy - 3.2)]])
    wire(q, BLUE, 2.4, ls=(0, (5, 2)), z=2.6)

# etichette dei cavi sul collo 2
ax.annotate("Alimentazione 12V\n2 × 1.5 mm² (≤5 m)\n2 × 2.5 mm² (5–10 m)\nrosso/nero, guaina",
            xy=(42.6, 42), xytext=(22, 38), fontsize=8.5, color=RED,
            arrowprops=dict(arrowstyle="->", color=RED), zorder=9,
            bbox=dict(fc="white", ec=RED, boxstyle="round,pad=0.3"))
ax.annotate("Bus RS-485: 1 cavo CAT5/CAT6 per collo\ncoppia 1 = IN (A/B), coppia 2 = OUT (A/B)\ncoppia 3 = GND riferimento\ncatena: master → T1 → T2 → T3 → T4",
            xy=(46.3, 42), xytext=(80, 34), fontsize=8.5, color=BLUE,
            arrowprops=dict(arrowstyle="->", color=BLUE), zorder=9,
            bbox=dict(fc="white", ec=BLUE, boxstyle="round,pad=0.3"))

# ------------------------------------------------------------------ legenda e contenuti
lx, ly = 112, 86
ax.text(lx, ly, "LEGENDA", fontsize=12, fontweight="bold", va="top")
for k, (col, ls, t) in enumerate([(RED, "-", "+12 V"), (BLK, "-", "GND (0 V)"), (BLUE, (0, (5, 2)), "RS-485 (CAT5)"),
                                   (PUR, "-", "+6V servo (DC-DC → J2)"), (ORG, "-", "cavi servo (3 fili)")]):
    y = ly - 4 - k * 2.6
    ax.plot([lx, lx + 4], [y, y], color=col, lw=2.6, ls=ls)
    ax.text(lx + 5, y, t, va="center", fontsize=9.5)

txt = (
    "IN OGNI TESTA (scatola IP54, fissata al telaio):\n"
    "• 1 × EyeNode (ADDR 0001…0100)\n"
    "• 1 × DC-DC 12V→6V ≥8–10A (resinato)\n"
    "• 2 moduli occhio = 6 servo MG90S\n"
    "   (testa 4: 1 modulo = 3 servo)\n"
    "• pressacavi: 12V in, CAT5 in/out,\n"
    "   servo verso gli occhi (≤ 1 m)\n"
    "• JP1 chiuso SOLO sull'ultima testa\n\n"
    "NEL CORPO (vano tecnico):\n"
    "• batteria 12V LiFePO4 50Ah\n"
    "• sezionatore + fusibile generale 20A\n"
    "• scatola fusibili: 5A per ogni testa\n"
    "• master RS-485 (opzionale, JP1 chiuso)\n"
    "• presa di ricarica\n\n"
    "CONSUMI (21 servo):\n"
    "• tipico ≈ 3 A a 12V (≈ 36 W)\n"
    "• picco ≈ 11 A a 12V\n"
    "• autonomia 50Ah: ≈ 12–15 h tipiche\n\n"
    "Cavi nei colli fissati con fascette\n"
    "ogni 20–30 cm, con un'ansa di\n"
    "scorta ai giunti mobili."
)
ax.text(lx, ly - 18, txt, fontsize=9.3, va="top", family="DejaVu Sans",
        bbox=dict(fc="#fafafa", ec="#999999", boxstyle="round,pad=0.6"))

ax.text(52, 88.5, "L'IDRA — Carnevale di Viareggio 2027 — schema di cablaggio (concettuale)",
        ha="center", fontsize=16, fontweight="bold")
plt.savefig(OUT, dpi=110, bbox_inches="tight", facecolor="white")
print(OUT)
