# Testa 3 — occhio singolo — ⏳ DA STAMPARE

In questa cartella ci sono **solo i pezzi della testa 3**: 3 piatti in [`da_stampare/`](da_stampare/), che stampati
tutti e 3 danno la testa completa (le teste 3 e 4 sono uguali, ognuna ha i suoi piatti).

![Coppia e occhio singolo](../../../../docs/img/coppia_vs_singolo.png)

**Cosa c'è e cosa no rispetto a una testa a coppia** (meccanismo D85 con il solo occhio sinistro, 3 servo:
X, Y e palpebre sinistre):

| | Coppia | Occhio singolo |
|---|---|---|
| Bulbi | 2 | **1** |
| Palpebre (già montate) | `Palpebre_L_PIP` + `Palpebre_R_PIP` | **solo `Palpebre_L_PIP`** |
| Supporti esterni | `PivotOuter_L` + `PivotOuter_R` | **solo `PivotOuter_L`** |
| Supporti centrali | 2 `PivotCentral` | 2 `PivotCentral` (il destro regge il perno destro del `CoreY`) |
| Asse X, telaio | `XAxisA_PIP`, 264 mm | **`XAxisA_singolo`, 155 mm**: via braccio e adattatore destri |
| Asse X, tirante | `XAxisB_PIP`, 264 mm | **`XAxisB_singolo`, 143 mm**: via braccio e adattatore destri |
| Telaio Y | `CoreY_PIP` | `CoreY_PIP` (uguale) |
| Base | `Base_L` + `Base_R` (194 mm) + 2 chiavette | `Base_L` + **`Base_R_singolo` (75 mm)** + 2 chiavette: via la sede del servo delle palpebre destre e del supporto esterno destro; restano mezza sede del servo Y, il supporto centrale destro, mezza linguetta PCA9685 e il foro Ø12 per il supporto della mandibola |

In tutto **12 pezzi in 3 piatti** (~21 h 20 min, ~0.60 kg) invece dei 15 pezzi, più lunghi, di una testa a coppia.

Montaggio: come la coppia (`docs/mechanical_eyes.md`), senza i pezzi del lato destro; la sede del servo Y sta a
cavallo delle due metà della base, che si uniscono con le 2 chiavette come nella coppia. L'occhio sta a 100 mm a
sinistra del centro del meccanismo. Contenuto, tempi e grammi dei piatti: [`da_stampare/README.md`](da_stampare/README.md).
