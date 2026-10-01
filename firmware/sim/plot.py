"""Simula le 4 teste per 5 minuti e disegna 60 s dell'occhio A di ognuna."""
import csv, io, subprocess
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
OUT = HERE.parents[1] / "docs" / "img" / "simulazione_movimento_teste.png"
EXE = HERE / ("sim.exe" if (HERE / "sim.exe").exists() else "sim")


def run(addr, seed, secs=300):
    txt = subprocess.run([str(EXE), str(addr), str(seed), str(secs)], capture_output=True, text=True, check=True).stdout
    rows = list(csv.DictReader(io.StringIO(txt)))
    return {k: np.array([float(r[k]) for r in rows]) for k in rows[0]}


fig, ax = plt.subplots(4, 1, figsize=(13, 9), sharex=True)
for i in range(4):
    d = run(i + 1, i + 1)
    m = (d["t"] >= 20000) & (d["t"] < 80000)
    t = d["t"][m] / 1000
    ax[i].plot(t, d["a_lr"][m], label="sx/dx", lw=1.2)
    ax[i].plot(t, d["a_ud"][m], label="su/giù", lw=1.2)
    ax[i].plot(t, d["a_lid"][m], label="palpebre", lw=1, alpha=.7)
    ax[i].set_ylabel(f"Testa {i + 1}\nµs"); ax[i].set_ylim(1050, 1900); ax[i].grid(alpha=.3)
ax[0].legend(ncol=3, loc="upper right", fontsize=8)
ax[-1].set_xlabel("tempo [s] (simulazione del firmware, occhio A)")
fig.suptitle("Movimento casuale indipendente per ogni testa — stesso firmware, 4 indirizzi DIP")
fig.tight_layout()
fig.savefig(OUT, dpi=100)
print(OUT)
