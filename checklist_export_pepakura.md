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

| altezza torre stampata | 1 unità Blender = | larghezza finestra | altezza varco | interno del fusto | feritoia |
|---|---|---|---|---|---|
| **30 cm** (riferimento) | 4,37 cm | 11,8 mm | 41,5 mm | 63,0 mm | 3,9 mm |
| 20 cm | 2,92 cm | 7,9 mm | 27,7 mm | 42,0 mm | 2,6 mm |

**Verifica che i dadi passino** con la scala scelta: un d20 misura ~20 mm. Alla scala di riferimento il varco è 41,5 mm e l'interno 63 mm, quindi ampiamente comodi. A 20 cm il varco scende a 27,7 mm: passa, ma conviene provare col dado più grosso del set.

Le finestre restano **troppo strette perché un dado esca** a entrambe le scale, che è voluto.

**Altezza massima: ~322 mm**, oltre la quale la striscia del corpo principale supera il lato lungo stampabile di un A4 e va divisa a mano. Verificabile con `check_page_fit(target_height_mm=...)`, che elenca l'ingombro di ogni pezzo srotolato.

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

**Un file solo, non tre.** Pepakura apre un documento per file, e ogni documento parte da una pagina propria: con file separati i pezzi piccoli non possono condividere il foglio con quelli grandi. Misurando le aree a 200 mm di altezza:

| pezzo | area | % di un A4 |
|---|---|---|
| Torre | 36.858 mm² | 70,0% |
| Muro | 4.434 mm² | 8,4% |
| Rampa | 3.235 mm² | 6,1% |
| **totale** | **44.527 mm²** | **85%** |

Con tre file si stampano tre documenti separati. Nel file unico Pepakura annida i pezzi sugli stessi fogli tenendoli comunque distinti e numerati.

### Compattare il layout su meno pagine

**Il formato carta non è la leva: l'A4 è già l'impostazione di default.** Il foglio grande che si vede in Edit Mode non è un A2, è la tela di Pepakura suddivisa in pagine A4 affiancate (2×2). Se il PDF esce in 4 pagine è perché **i pezzi sono sparpagliati**, non per il formato.

Percorsi verificati in Pepakura Designer 6:

1. `Settings` → **`Page...`** — qui c'è *Paper Size* (già A4, 210×297) e i **margini, 15 mm per lato di default**. Abbassarli a ~5 mm porta l'area utile da 180×267 = 48.060 mm² a 200×287 = 57.400 mm², cioè +19%.
   Da non confondere con `Settings` → `Print...` (e `File` → `Print Settings...`), che riguardano solo spessore del tratto e stampa vettoriale/bitmap.
2. `2D Layout` → **`Re-layout Parts...`** — ridispone i pezzi compattandoli. È il comando che risolve le 4 pagine: cambiando margini o formato i pezzi non si spostano da soli.
3. `2D Layout` → **`Check Overlapping Parts`** — da lanciare dopo il ricalcolo: un pezzo sovrapposto a un altro in stampa è irrecuperabile.

Se `Save` è disattivato e in fondo al menu `File` compare `Switch to Designer Mode`, cliccarlo prima: in modalità ridotta i comandi di layout non sono disponibili.

**Risultato ottenuto: 2 pagine A4**, con i margini a 5 mm e la disposizione rifinita a mano. `Re-layout Parts` da solo si fermava a 4: il suo algoritmo evita che i pezzi escano dai bordi ma non minimizza il numero di pagine, e le strisce lunghe e sottili di questo modello sono il caso peggiore per un impacchettamento automatico. La rifinitura a mano è normale per un kit commerciale, e permette anche di raggruppare i pezzi in modo sensato: corpo della torre su una pagina, base e accessori sull'altra.

Due pagine è anche il minimo teorico: l'area dei pezzi è 44.527 mm² contro 48.060 mm² di A4 stampabile, cioè il 92,6% di una pagina, più il 15-25% di linguette, e un pezzo non può essere spezzato a cavallo di due fogli.

### Opzioni di visualizzazione che contano

Perché servono. Per la sequenza operativa vedi la ricetta nella sezione 6. Nel pannello *Display Options* di Edit Mode:

- **`Check Overlapping Parts`**: è un'opzione di visualizzazione, non un comando da lanciare. Tenerla attiva **mentre** si dispongono i pezzi: evidenzia le sovrapposizioni in tempo reale. Un pezzo annidato nel foro di un altro (es. la striscia merlata dentro l'anello) non è un errore ma buon impacchettamento, e questa opzione permette di distinguere i due casi.
- **`Hide nearly flat folding lines`** con soglia 175°: da tenere attiva. Questo modello ha facce complanari (i pannelli dei merli continuano il parapetto sottostante), e le pieghe a 180° non vanno disegnate perché lì la carta resta piatta.
- **`Edge ID`** e **`Page Number`**: irrilevanti per un prototipo costruito da chi ha fatto il modello, **necessari per la versione da vendere**. `Edge ID` numera gli spigoli accoppiati: senza, con ~13 pezzi e molte linguette, l'acquirente deve indovinare quale linguetta va con quale bordo.

Un vincolo di ingombro da conoscere: la catena di triangoli del plinto è una striscia lunga ~215 mm, più della larghezza stampabile di un A4 in verticale. Va ruotata di 90° per rientrare nell'altra dimensione. Se `Re-layout Parts` non lo fa da sé, ruotarla a mano.

Per ristampare un solo pezzo: `export_for_pepakura(combined=False)` torna a un file per oggetto.

Cosa fa e perché:

- **La scala è già dentro il file**: i numeri nell'OBJ sono millimetri, quindi la torre esce alta esattamente 200 mm. La scala si applica in export (`global_scale`), non ridimensionando gli oggetti: il modello sul disco resta in unità di lavoro e puoi esportare a taglie diverse senza toccarlo. Verifica comunque la scala nella finestra di dialogo di Pepakura.
- **Niente triangolazione** (`export_triangulated_mesh=False`): triangolare moltiplicherebbe le linee di piega. Le facce quadrangolari e n-gon sono per costruzione planari, quindi Pepakura le apre come un unico pannello.
- **Assi**: esportati con la convenzione OBJ standard (Up = Y, Forward = -Z), cioè la Z di Blender diventa Y. Se Pepakura mostra il modello coricato, ruotalo lì o riesporta con `up_axis='Z'` — è l'unico parametro di cui non ho conferma diretta sul comportamento di Pepakura.
- **Niente materiali/UV** finché non ci sono texture, per non generare un `.mtl` vuoto.

---

## 6. Versione gratuita di Pepakura: niente salvataggio

**Vincolo operativo da conoscere prima di iniziare.** Nella versione gratuita/non licenziata `Save` e `Save As...` sono disattivati: **non si può salvare il `.pdo`**. Ogni volta che si chiude il file e si reimporta l'OBJ, tutte le impostazioni e tutta l'impaginazione vanno rifatte a mano. L'export in PDF invece funziona.

Conseguenze pratiche:

- **Fare tutto il lavoro in una sessione sola.** Chiudere Pepakura equivale a buttare l'impaginazione.
- **Il PDF esportato è l'unico artefatto che sopravvive.** Va conservato: serve sia per stampare sia come riferimento visivo per ricostruire la disposizione dei pezzi la volta successiva.
- Conviene anche **tenere uno screenshot del layout finale**: ricostruire a occhio la posizione di ~13 pezzi da un PDF è più lento che copiarla da un'immagine.
- Per questo motivo **PDF e screenshot del layout sono versionati** in `export/`: non sono artefatti usa e getta, sono l'unico record del lavoro di impaginazione.
- Se il progetto va in vendita, **la licenza si ripaga da sola**: ogni ritocco al modello significa rifare da zero un'impaginazione di ~15 minuti, e ogni variante futura (dimensioni diverse, versioni a tema) la stessa cosa.

### Ricetta da riapplicare a ogni reimport

Nell'ordine, dopo aver aperto `export/PaperDiceTower.obj`:

| # | dove | cosa |
|---|---|---|
| 1 | `File` | `Switch to Designer Mode`, se presente in fondo al menu (in modalità ridotta i comandi di layout non ci sono) |
| 2 | `Settings` → `Page...` | *Paper Size* = **A4**; margini **Left & Right = 5**, **Top & Bottom = 5** (il default è 15 e costa il 19% di area utile) |
| 3 | `Settings` → `Print...` | **`Print lines clearly (Vector print)`** — il default è bitmap, che rasterizza tutto a ~140 DPI |
| 4 | *Display Options* (Edit Mode) | attivare **`Edge ID`**, **`Page Number`**, **`Check Overlapping Parts`**, **`Hide nearly flat folding lines`** (soglia 175°); `Flaps` è già attivo |
| 5 | — | verificare che la **scala** dica **200 mm** di altezza |
| 6 | `2D Layout` → `Re-layout Parts...` | prima passata automatica: si ferma a 4 pagine |
| 7 | pannello 2D | **disporre a mano** fino a 2 pagine: appaiare le due strisce grandi (corpo principale ~192×52 mm e fusto ~169×104 mm) nello stesso verso sulla prima pagina; base, muro, rampa e vaschetta sulla seconda. Ruotare di 90° la catena del plinto (~215 mm, più larga di un A4 in verticale) |
| 8 | — | controllare che `Check Overlapping Parts` non evidenzi nulla |
| 9 | `File` → `Print to PDF...` | `Ctrl+Shift+P` |

Risultato atteso: 2 pagine A4, PDF vettoriale di ~27 KB.

---

## 7. In Pepakura

- Se l'unfold produce **schegge strette e allungate**, torna nel modello e allarga la faccia in quel punto (in `build_tower.py`, non a mano sulla mesh)
- Se una faccia grande viene spezzata in troppi pezzi, valuta di unire facce adiacenti prima di ri-esportare
- Controlla dove Pepakura mette le linguette attorno ai **fori** (finestre, feritoie, apertura del muro) e al **profilo delle merlature**: non deve generarne, sono tagli e non pieghe

---

## 8. Assemblaggio — note che nascono dal modello

- **Finestre**: dietro va incollato un foglietto di **carta velina colorata** (ambra o blu) come vetro. Un pezzo piatto per finestra. Se prevedi un LED interno, la velina fa l'effetto vetrata illuminata.
- **Interno scuro**: perché le finestre leggano scure come nella reference, la faccia interna del foglio va stampata scura, altrimenti si vede il retro bianco della carta attraverso i fori.
- **Grammatura della carta**: **200 g/m²** alla scala di riferimento, con margine fino a ~250. I due limiti si sono spostati passando a 30 cm: il tetto superiore era la fragilità dei dettagli piccoli, che ora sono una volta e mezza più grandi (feritoie da 3,9 mm invece di 2,6), quindi si può salire; il limite inferiore invece si è alzato, perché una torre di 30 cm ha più peso da reggere e sotto i 180 g/m² il fusto flette. A 20 cm valeva invece 170-200 con tetto stretto.
- **Incidere le pieghe prima di piegare**, con una stecca o il dorso di una lama. A 200 g/m² una piega non incisa si spacca o si arrotonda, e sul plinto le pieghe sono ravvicinate.
- **Rampa**: è un sotto-assemblaggio a sé (cuneo chiuso di 5 facce, pendenza ~17°). Va incollata dentro il guscio **prima** di chiudere la torre, con il bordo basso a filo del varco.
- **Muro di cinta**: la striscia orizzontale lungo il suo bordo inferiore è la linguetta di incollaggio, non un errore dell'unfold. Va piegata verso l'interno e incollata al piano d'appoggio: senza quella il pannello non sta in piedi.
- **Merlature**: il profilo a zigzag in cima ai pannelli del parapetto e del muro è una linea di **taglio**. La striscia si piega ai soli spigoli verticali della torre.
