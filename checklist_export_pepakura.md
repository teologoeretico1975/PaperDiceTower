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

Nel report devono valere **tutte** queste condizioni, per `Torre`, `Rampa` e `Muro`:

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

## 3-bis. Superfici interne in vista — da risolvere quando si applica una skin

Le normali sono coerenti e corrette: 152 pareti verso l'esterno, 2 tangenziali (i fianchi della vaschetta, per costruzione), 0 verso l'interno. Le facce orizzontali a z=0 puntano in basso, ed è giusto: **l'interno della vaschetta è un unico spazio continuo con l'interno della torre**, collegato attraverso il varco, quindi il "sopra" del pianale è superficie interna. In Pepakura appare grigio perché guardandola dall'alto si vede il retro del foglio, come guardando dentro una scodella.

Finché il modello è senza texture non cambia nulla. **Con una skin applicata sì**: la texture viene stampata sul lato verso cui punta la normale, quindi il pianale della vaschetta risulterebbe decorato sul lato che guarda il tavolo e bianco sul lato in vista — dove invece si appoggiano i dadi ed è la parte più guardata del modello.

Tre modi per risolverlo, da valutare in fase di texture:

1. **Girare le sole facce del pianale** dopo `recalc_face_normals`. Costa zero pezzi. Effetto collaterale: quelle 3 facce risultano di verso opposto rispetto al fondo del plinto con cui confinano — invisibile, perché il fondo del plinto guarda il tavolo e non si vede mai. Attenzione: un successivo "Recalculate Outside" in Blender annullerebbe la modifica, quindi va fatta come ultimo passo e documentata.
2. **Pianale come pezzo separato**, da incollare sopra con il verso giusto. Un pezzo piatto in più, nessuna incoerenza nella mesh.
3. **Lasciarlo bianco**, se la carta grezza passa per pavimento in pietra. Zero lavoro, resa più debole.

Nota che il problema riguarda **solo** il pianale della vaschetta: gli altri interni (fusto, corpo principale) non si vedono, e per loro la carta bianca all'interno è la norma nel papercraft.

## 4. Cosa NON fare

Tre trappole, tutte controintuitive:

- **Non rimuovere l'interno cavo.** In un modello generico si consiglia di eliminare le facce interne nascoste, ma qui il guscio *deve* restare cavo: è lo scivolo dei dadi. Non usare `Select → All by Trait → Interior Faces` per "ripulire".
- **Non giudicare la difficoltà dal numero di facce.** `Torre` ha 158 facce, `Muro` 21, `Rampa` 5. Un limite tipo "max 60 facce" non si applica: finestre e feritoie passanti aggiungono facce ma **zero** pezzi da incollare. Quello che misura la fatica di assemblaggio è il numero di pezzi separati e la loro dimensione reale — un pezzo sotto i ~5 mm è il vero problema.
- **Non convertire finestre, feritoie o merlature in geometria in rilievo** perché "sembrano più ricche" nel viewport: le finestre diventerebbero 9 pezzi ciascuna con pareti da 3 mm, e i merli 4 scatoline da ~9×6 mm. Vedi `memory/reference_vincoli_papercraft.md`.

---

## 5. Export

Automatizzato. Dopo aver eseguito lo script:

```python
export_for_pepakura(target_height_mm=200)
```

Scrive `export/PaperDiceTower.obj` con tutti i sotto-assemblaggi in un file solo.

**Un file solo, non tre.** Pepakura crea un documento per file, e ogni documento occupa almeno una pagina. Misurando le aree a 200 mm di altezza:

| pezzo | area | % di un A4 |
|---|---|---|
| Torre | 36.858 mm² | 70,0% |
| Muro | 4.434 mm² | 8,4% |
| Rampa | 3.235 mm² | 6,1% |
| **totale** | **44.527 mm²** | **85%** |

Con tre file si stampano tre documenti separati. Nel file unico Pepakura annida i pezzi sugli stessi fogli tenendoli comunque distinti e numerati.

### Impostare il formato carta in Pepakura

**Il numero di pagine dipende dal formato configurato in Pepakura, non dal modello.** Con il formato lasciato su A2 il layout occupa un A2, che esportato in PDF diventa **4 pagine A4** con un riempimento di circa il 21%: Pepakura distribuisce i pezzi sulla tela grande senza alcun motivo per compattarli in unità A4.

Prima di esportare il PDF, quindi: impostare il formato pagina su **A4** e rilanciare la disposizione automatica dei pezzi. L'area totale dei pezzi è 44.527 mm² contro ~52.600 mm² di A4 stampabile, quindi con le linguette servono realisticamente 2 pagine.

Un vincolo di ingombro da conoscere: la catena di triangoli del plinto è una striscia lunga ~215 mm, più della larghezza stampabile di un A4 in verticale (~190 mm). Va ruotata di 90° per rientrare nei 277 mm dell'altra dimensione. Se Pepakura non lo fa da sé, ruotarla a mano.

Per ristampare un solo pezzo: `export_for_pepakura(combined=False)` torna a un file per oggetto.

Cosa fa e perché:

- **La scala è già dentro il file**: i numeri nell'OBJ sono millimetri, quindi la torre esce alta esattamente 200 mm. La scala si applica in export (`global_scale`), non ridimensionando gli oggetti: il modello sul disco resta in unità di lavoro e puoi esportare a taglie diverse senza toccarlo. Verifica comunque la scala nella finestra di dialogo di Pepakura.
- **Niente triangolazione** (`export_triangulated_mesh=False`): triangolare moltiplicherebbe le linee di piega. Le facce quadrangolari e n-gon sono per costruzione planari, quindi Pepakura le apre come un unico pannello.
- **Assi**: esportati con la convenzione OBJ standard (Up = Y, Forward = -Z), cioè la Z di Blender diventa Y. Se Pepakura mostra il modello coricato, ruotalo lì o riesporta con `up_axis='Z'` — è l'unico parametro di cui non ho conferma diretta sul comportamento di Pepakura.
- **Niente materiali/UV** finché non ci sono texture, per non generare un `.mtl` vuoto.

---

## 6. In Pepakura

- Se l'unfold produce **schegge strette e allungate**, torna nel modello e allarga la faccia in quel punto (in `build_tower.py`, non a mano sulla mesh)
- Se una faccia grande viene spezzata in troppi pezzi, valuta di unire facce adiacenti prima di ri-esportare
- Controlla dove Pepakura mette le linguette attorno ai **fori** (finestre, feritoie, apertura del muro) e al **profilo delle merlature**: non deve generarne, sono tagli e non pieghe

---

## 7. Assemblaggio — note che nascono dal modello

- **Finestre**: dietro va incollato un foglietto di **carta velina colorata** (ambra o blu) come vetro. Un pezzo piatto per finestra. Se prevedi un LED interno, la velina fa l'effetto vetrata illuminata.
- **Interno scuro**: perché le finestre leggano scure come nella reference, la faccia interna del foglio va stampata scura, altrimenti si vede il retro bianco della carta attraverso i fori.
- **Grammatura della carta**: **170-200 g/m²**. Sotto i 160 il fusto è un tubo troppo flessibile per reggere il corpo principale e il parapetto, e i dadi che cadono lo ammaccano. Sopra i 220 i pezzi piccoli diventano il problema opposto: le feritoie da 2,8 mm si sfrangiano al taglio, i merli da ~1 cm non piegano netti e le linguette non si appiattiscono. Se vuoi ottimizzare, i pezzi grandi e strutturali (fusto, corpo principale, plinto) stanno bene a 200 e quelli di dettaglio (parapetto con merlature, muro, rampa) a 160 — ma per un prodotto da vendere conviene una grammatura sola.
- **Incidere le pieghe prima di piegare**, con una stecca o il dorso di una lama. A 200 g/m² una piega non incisa si spacca o si arrotonda, e sul plinto le pieghe sono ravvicinate.
- **Rampa**: è un sotto-assemblaggio a sé (cuneo chiuso di 5 facce, pendenza ~17°). Va incollata dentro il guscio **prima** di chiudere la torre, con il bordo basso a filo del varco.
- **Muro di cinta**: la striscia orizzontale lungo il suo bordo inferiore è la linguetta di incollaggio, non un errore dell'unfold. Va piegata verso l'interno e incollata al piano d'appoggio: senza quella il pannello non sta in piedi.
- **Merlature**: il profilo a zigzag in cima ai pannelli del parapetto e del muro è una linea di **taglio**. La striscia si piega ai soli spigoli verticali della torre.
