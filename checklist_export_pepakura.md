# Checklist pre-export Blender → Pepakura

## PaperDiceTower — verifica finale prima dell'unfold

Da eseguire ogni volta che si modifica il modello, non solo alla prima esportazione.

Il modello si rigenera da [build_tower.py](build_tower.py), che è la fonte di verità: buona parte dei controlli qui sotto è automatizzata lì e non va rifatta a mano. Questa checklist copre (1) come leggere il report dello script, (2) i passaggi che lo script non può fare.

---

## 1. Controlli automatici — leggi il report dello script

Rigenera il modello da dentro Blender:

```python
exec(open(r"E:\repos\PaperDiceTower\build_tower.py").read())
```

Nel report devono valere **tutte** queste condizioni, per `Torre` e per `Rampa`:

| campo | valore richiesto | perché conta |
|---|---|---|
| `non_manifold_edges` | 0 | Pepakura si basa su facce collegate correttamente; uno spigolo con 3 facce produce un unfold rotto |
| `loose_verts` | 0 | vertici orfani residuo di cancellazioni parziali |
| `non_planar_faces` | 0 | **il controllo più importante**: una faccia svergolata nello spazio non si piega mai combaciando sulla carta, anche con topologia impeccabile |
| `boundary_edges` | uguale a `expected_boundary_edges` | i bordi non devono essere zero (le aperture sono volute), ma se il conteggio non torna c'è un buco involontario |
| `fit rampa` | `True` | la rampa non deve sbucare dalle pareti |

Se `non_planar_faces` non è 0, la causa tipica è un quad tra due anelli di cui uno ha raggi irregolari: va triangolato (`triangulate_twisted()` lo fa già per il plinto) o riprogettato.

**Non serve** ripetere a mano `Select → All by Trait → Non Manifold`: lo script lo verifica a ogni esecuzione.

---

## 2. Scala — l'unico passaggio davvero critico

In Blender il modello è alto **6,5 unità** (scena in unità metriche, `scale_length = 1`). La conversione va decisa prima dell'export o impostata in Pepakura.

| altezza torre stampata | 1 unità Blender = | larghezza finestra | altezza varco | interno del fusto |
|---|---|---|---|---|
| **20 cm** (consigliata) | 3,08 cm | 8 mm | 29 mm | 46 mm |
| 15 cm | 2,31 cm | 6 mm | 22 mm | 35 mm |

**Verifica che i dadi passino** con la scala scelta: un d20 misura ~20 mm. A 20 cm di torre il varco è 29 mm e l'interno 46 mm — comodi. A 15 cm il varco scende a 22 mm: passa a filo, e conviene provare con il dado più grosso del set prima di stampare tutto.

Le finestre restano invece **troppo strette perché un dado esca** in entrambi i casi (6-8 mm), che è voluto.

**Perché conta:** Pepakura scala in base alle unità del file. Sbagliare qui rende inutile tutto il resto, e non è recuperabile dopo la stampa.

---

## 3. Normali

Già a posto: lo script chiude con `recalc_face_normals` su tutte le facce. Il volume orientato del guscio è positivo, cioè le normali puntano verso l'esterno.

Se vuoi verificarlo visivamente: Viewport Overlays → **Face Orientation**. Tutto blu = corretto, rosso = invertito.

Attenzione a un falso allarme: i fianchi della vaschetta hanno normale **tangenziale** all'asse della torre, non radiale. Un controllo del tipo "la normale punta via dall'asse?" li segnala erroneamente. Usa il volume orientato (`bm.calc_volume(signed=True)` > 0) come verifica affidabile.

---

## 4. Cosa NON fare

Tre trappole, tutte controintuitive:

- **Non rimuovere l'interno cavo.** In un modello generico si consiglia di eliminare le facce interne nascoste, ma qui il guscio *deve* restare cavo: è lo scivolo dei dadi. Non usare `Select → All by Trait → Interior Faces` per "ripulire".
- **Non giudicare la difficoltà dal numero di facce.** `Torre` ha 127 facce (12 triangoli, 77 quad, 38 n-gon) e `Rampa` 5. Un limite tipo "max 60 facce" non si applica: le 9 finestre passanti aggiungono facce ma **zero** pezzi da incollare. Quello che misura la fatica di assemblaggio è il numero di pezzi separati e la loro dimensione reale — un pezzo sotto i ~5 mm è il vero problema.
- **Non convertire le finestre in tasche incassate** perché "sembrano più ricche" nel viewport: diventerebbero 9 pezzi per finestra, con pareti da 3 mm. Vedi `memory/reference_vincoli_papercraft.md`.

---

## 5. Export

- `File → Export → Wavefront (.obj)`
- Opzioni: **Forward = -Y**, **Up = Z** (orientamento standard per Pepakura)
- Esporta **solo gli oggetti selezionati** e valuta se esportare `Torre` e `Rampa` in due file separati: sono due sotto-assemblaggi distinti e tenerli separati rende l'unfold più leggibile
- Includi UV se hai già applicato texture

---

## 6. In Pepakura

- Se l'unfold produce **schegge strette e allungate**, torna nel modello e allarga la faccia in quel punto (in `build_tower.py`, non a mano sulla mesh)
- Se una faccia grande viene spezzata in troppi pezzi, valuta di unire facce adiacenti prima di ri-esportare
- Controlla dove Pepakura mette le linguette attorno ai **fori delle finestre**: non deve generarne, sono tagli e non pieghe

---

## 7. Assemblaggio — note che nascono dal modello

- **Finestre**: dietro va incollato un foglietto di **carta velina colorata** (ambra o blu) come vetro. Un pezzo piatto per finestra. Se prevedi un LED interno, la velina fa l'effetto vetrata illuminata.
- **Interno scuro**: perché le finestre leggano scure come nella reference, la faccia interna del foglio va stampata scura, altrimenti si vede il retro bianco della carta attraverso i fori.
- **Rampa**: è un sotto-assemblaggio a sé (cuneo chiuso di 5 facce, pendenza ~17°). Va incollata dentro il guscio **prima** di chiudere la torre, con il bordo basso a filo del varco.
