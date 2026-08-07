# Handover — PaperDiceTower

Stato al 2026-08-07. Questo file è il punto di ingresso: orienta e rimanda ai documenti di dettaglio, senza duplicarli.

Repo: <https://github.com/teologoeretico1975/PaperDiceTower> · branch `main`. Per l'ultimo stato: `git log --oneline -5` — un hash scritto qui invecchia a ogni commit.

---

## 1. Cos'è

Torre dadi fantasy low-poly modellata in Blender, destinata a essere **unfoldata con Pepakura** e venduta come modello papercraft su Etsy. Due reference fornite dal committente: una torre dadi in legno tagliato al laser, poi una torre in resina con base rocciosa, finestre ad arco e muro perimetrale — è quest'ultima che ha guidato la forma attuale.

## 2. Dove siamo

**Geometria completa e validata. Unfold verificato in Pepakura. Manca la prova di assemblaggio da stampa.**

**Versione di riferimento: 7 lati, stampata alta 300 mm** — `PaperDiceTower7.blend`, ed è il default dello script. `PaperDiceTower.blend` a 9 lati è conservato come variante, riproducibile con `build_all(sides=9)`.

| oggetto | ruolo | facce (riferimento, 7 lati) | facce (9 lati) |
|---|---|---|---|
| `Torre` | guscio | 123 | 158 |
| `Muro` | cinta decorativa | 16 | 21 |
| `Deflettori` | 4 strisce corrugate interne | 16 | 16 |
| `Rampa` | cuneo interno | 5 | 5 |

Su entrambe: 0 non-manifold, 0 facce non planari, bordi pari agli attesi, rampa dentro le pareti.

Perché 7 lati **e** 300 mm, e non uno dei due: ridurre le facce allarga solo i pannelli (16,0 → 20,2 mm), mentre feritoie e soglie restano invariate perché sono misure assolute. Solo la scala allarga anche quelle (feritoia 2,6 → 3,9 mm). Le due leve non sono alternative. Confronto completo nel README.

Verificato in Pepakura: scala corretta, orientamento in piedi, nessun pezzo a scheggia, fori trattati come tagli e non come pieghe, nessuna sovrapposizione.

Pattern impaginato su **4 pagine A4**, PDF **vettoriale**: 636 segmenti, 13 pezzi, 15 fori, il piu' grande 180,8 x 250 mm contro 200 x 287 stampabili. Le 48 immagini raster nel PDF sono tessere di sfondo bianco: innocue. Misurato con `tools/pattern.py`, non stimato.

## 3. Come si lavora

**Il modello non si modifica a mano.** `build_tower.py` è la fonte di verità: i parametri sono in cima al file, e lo script è idempotente (cancella e ricrea ciò che genera).

Serve Blender 5.1+ con l'add-on MCP di Blender Lab attivo — vedi `memory/reference_blender_mcp_addon.md` se la connessione non risponde.

```python
# dentro Blender
exec(open(r"E:\repos\PaperDiceTower\build_tower.py").read())   # rigenera + stampa il report
export_for_pepakura()                                           # scrive export/*.obj a 300 mm
```

Il report di verifica deve dare **0** su `non_manifold_edges`, `loose_verts`, `non_planar_faces`, e `boundary_edges` pari a `expected_boundary_edges`. Perché quei controlli e non altri: `checklist_export_pepakura.md`.

Dopo l'unfold c'è un secondo controllo, sull'**output di Pepakura** invece che sulla mesh — per molto tempo era l'unico anello non verificato:

```bash
python tools/pattern.py inventario export/PaperDiceTower7_300.pdf
```

Legge il PDF (senza librerie PDF: è vettoriale, si decomprime con zlib) e misura i pezzi veri, riconoscendo le feature dalla firma dimensionale. Alla scala di riferimento deve trovare 7 finestre da 42,0 × 11,8 mm, 7 feritoie da 3,9 mm di larghezza, 4 deflettori da 33,8 × 68,1, e **nessun pezzo oltre i 200 × 287 mm stampabili**: il più grande è 180,8 × 250. Se quelle misure non tornano, la scala si è persa fra Blender e la stampa.

Identifica ogni pezzo, dice su che colore di cartoncino va stampato, e controlla tre invarianti. Esce con codice 1 se un controllo non passa, quindi si può mettere in uno script.

Perché uno script e non solo il `.blend`: il file Blender è un binario opaco in git, e modellare a incrementi rendeva ogni ritocco di proporzioni una ricostruzione manuale.

## 4. Decisioni da non ribaltare per sbaglio

Sono controintuitive e sono già costate un giro di correzioni ciascuna.

- **Finestre, feritoie e merlature sono fori e profili, non geometria in rilievo.** Una finestra incassata diventa 9 pezzi per finestra con pareti da 3 mm; i merli come blocchi separati diventano 7 scatoline da ~9×6 mm. Inassemblabili a mano. Il criterio non è il numero di facce ma **quanti pezzi separati diventa e quanto misurano davvero alla scala di stampa**.
- **La silhouette ha tratti cilindrici (tamburi) tra un restringimento e l'altro.** Senza, il profilo legge come un proiettile. Vale anche il rapporto: a 2,3:1 sembrava un macinapepe, ora è ~3,5:1.
- **Due merli adiacenti devono avere la stessa altezza.** Se differiscono, al loro spigolo comune nascono due bordi liberi sovrapposti invece di una piega.
- **La planarità va controllata, non solo la manifold-ness.** Una faccia svergolata non si piega combaciando, e il controllo di manifold-ness non la vede.
- **I deflettori rispondono a due criteri opposti, entrambi da misurare.** L'insieme non deve lasciare un canale verticale libero (o il dado cade senza toccare), ma ogni striscia da sola deve lasciar passare il dado più grande (o si intasa). Guardare solo la copertura porta a un imbuto. Le pieghe della corrugazione devono correre lungo la luce: trasversali darebbero un soffietto, cioè una molla.
- **Qualunque partizione interna del tubo rende non-manifold il guscio** (lo spigolo di attacco avrebbe 3 facce). Per questo rampa e deflettori sono oggetti separati, che nel papercraft è anche la norma.
- **La vaschetta è un settore radiale a livello del suolo.** Radiale perché così i fianchi sono complanari; a livello del suolo perché sospesa i dadi restavano dentro.
- **Si esporta un OBJ solo con tutti i sotto-assemblaggi, non uno per oggetto.** Pepakura occupa almeno una pagina per documento: `Muro` e `Rampa` riempiono l'8% e il 6% di un A4, quindi con file separati si stampano tre pagine di cui due quasi bianche. Lo spreco di carta è una dimensione di costo da misurare come le altre.
- **`export/` si versiona per intero**, `.obj` *e* PDF *e* screenshot dei layout. All'inizio i PDF erano esclusi come "rigenerabili", ma non lo sono: con Pepakura gratuito il `.pdo` non si salva, quindi il PDF piu' lo screenshot sono l'unico record di ~15 minuti di impaginazione manuale.

Il "perché" completo di ognuna è in `memory/reference_vincoli_papercraft.md` e `memory/project_panoramica.md`.

## 5. Prossimo passo

**Stampare e assemblare.** È l'unica prova che i controlli non possono dare: garantiscono una mesh valida, non un modello comodo da montare.

Da tenere d'occhio, in ordine di rischio, con il parametro da cambiare se cede:

Misure alla scala di riferimento (7 lati, 300 mm):

| # | punto | misura | parametro |
|---|---|---|---|
| 1 | feritoie, le più fragili al taglio | 3,9 mm | `SLIT_HALF_W` |
| 2 | soglia dell'apertura del muro | 3,3 mm | `WALL_GATE["v_bottom"]` |
| 3 | catena di triangoli del plinto: pieghe ravvicinate | — | `PLINTH_JAG` |
| 4 | varco di uscita, provare col d20 più grosso | 41,5 mm | `opening_top` in `add_dice_tray` |

Il varco a 41,5 mm contro un d20 da ~20 mm ha ora ampio margine, quindi il rischio si è spostato sui due dettagli più sottili.

**Conviene raccogliere più correzioni e applicarle in un colpo solo** invece di iterare una alla volta: rigenerare il modello ed esportare costa due minuti, ma rifare l'impaginazione in Pepakura ne costa ~15 perché non è salvabile (vedi sotto).

Vincolo di montaggio che nasce dalla geometria: **la rampa va incollata dentro prima di chiudere il fusto**, dopo non passa più dalla cima.

Carta **200 g/m²**, e alla scala di riferimento si può salire fino a ~250: il vincolo superiore era la fragilità dei dettagli piccoli, che a 300 mm sono cresciuti di una volta e mezza (feritoie da 3,9 mm invece di 2,6). Il vincolo inferiore invece si è irrigidito: una torre di 30 cm ha più peso da reggere, quindi sotto i 180 g/m² il fusto flette. Incidere le pieghe prima di piegare.

**Attenzione a un vincolo operativo:** con la versione gratuita di Pepakura non si può salvare il `.pdo`. Ogni reimport dell'OBJ azzera impostazioni e impaginazione, che vanno rifatte a mano (~15 minuti). Quindi: **fare tutto in una sessione sola**. Per questo in `export/` sono versionati anche i PDF e gli screenshot dei layout: sono l'unico record di quel lavoro, e da lì si ricostruisce la disposizione invece di ripartire da zero. La ricetta dei passaggi è la sezione 6 di `checklist_export_pepakura.md`. Se il progetto va in vendita la licenza si ripaga subito.

## 6. Grafica: il concept scelto

Il capitolo texture e' stato azzerato il 2026-08-07 ("risultati mediocri, comprese le skin procedurali e quelle scaricate a pagamento"). Il concept che lo sostituisce e' **il contrario di una texture**, e nasce da un'osservazione precisa.

Il vincolo che aveva ucciso le texture, registrato in `memory/reference_texture_tentativi.md`: *una tile ripetibile non sa dove si trova sul modello*, quindi non puo' disegnare l'arco attorno a **quella** finestra. Ma **il cartamodello 2D lo sa**: ogni finestra, piega e foro ha coordinate note. Quindi il decoro non e' un problema di texture, e' disegno sul pattern. Dettagli in `memory/reference_decoro_registrato.md`.

Tre decisioni operative:

- **Il colore viene dal cartoncino, non dalla stampa.** Palette chiara (sabbia, grigio perla, crema, verde salvia), scelta dal committente. Costa zero lavoro grafico, e' cio' che fanno le listing nella fascia di prezzo giusta, e sposta l'estetica sul cartoncino che sceglie l'acquirente invece che su una texture generata. Con palette chiara le linee nere restano leggibili, quindi **non** serve la stampa specchiata sul retro ne' il plotter da taglio.
- **Il decoro si disegna a mano in post-produzione**, in Inkscape sopra il PDF di Pepakura, tenendo il pattern su un layer bloccato. Un prototipo procedurale (archivolto a conci registrato sul contorno reale delle finestre) ha confermato che il principio funziona, ma la generazione automatica **e' stata rimossa il 2026-08-07**: lo stile non e' derivabile dalla geometria, e tenere in sincrono un PDF derivato a ogni re-impaginazione era solo manutenzione. Le lezioni del prototipo sono in `memory/reference_decoro_registrato.md`, il codice nel commit `f878218`.
- **La simmetria aiuta molto.** La torre e' a 7 lati con finestre e feritoie identiche, quindi i motivi davvero unici da disegnare sono cinque o sei, non tredici pezzi: il disegno unico e' circa un settimo del lavoro apparente. Resta disponibile, se serve, replicare a script un pannello disegnato a mano sugli altri sei con la rotazione corretta.

### Suddivisione in blocchi per il cartoncino colorato

**Pepakura non ha un colore per pezzo: un colore = uno o piu' fogli dedicati.** Quindi un blocco puo' avere un colore suo solo se e' un pezzo separato nel layout 2D — e in gran parte **lo e' gia**: plinto, fusto, corpo, pianali e muro escono come pezzi distinti (vedi l'inventario, sezione 3).

Dove invece Pepakura tiene insieme due blocchi, si separa **in Pepakura e non in Blender**. Motivo controintuitivo: un taglio interno alla stessa mesh e' uno spigolo tagliato, e Pepakura ci mette linguetta ed Edge ID accoppiati. Spezzare `Torre` in oggetti separati in Blender produrrebbe invece due **bordi liberi**: nessuna linguetta, perche' non c'e' niente da incollare, e nessuna numerazione che li accoppi. Servirebbe modellare un collarino telescopico a mano.

**Suddivisione adottata**, impaginata a mano dal committente il 2026-08-07: **due colori su quattro pagine**. Piu' semplice della proposta iniziale a cinque colori, e piu' economica — il conto delle pagine e' dominato dal **numero di colori, non dalla scala**, perche' ogni colore vuole almeno un foglio suo.

| pagina | carta | pezzi | come si riconosce |
|---|---|---|---|
| 1 | pietra | corpo principale con le rastremazioni + 2 deflettori | l'unico pezzo con le **7 finestre ad arco** |
| 2 | pietra | muro di cinta, parapetto e merlature, rampa | il muro e' l'unico con **l'apertura ad arco** da 11,4 x 17,5 mm |
| 3 | pietra | le **tre** strisce del fusto | portano in tutto le 7 feritoie, distribuite 5 + 1 + 1 |
| 4 | verde erba | plinto, pianale della base, 2 deflettori | la catena di triangoli e il poligono grande |

Due cose da non sbagliare:

- **Il fusto esce in tre pezzi, non uno.** Le feritoie sono 5 + 1 + 1: se sulla pagina 3 mancasse una striscia il tubo non si chiude. E' la verifica piu' facile a occhio.
- **I deflettori possono stare su qualunque pagina.** Sono dentro il fusto e non si vedono mai, quindi due sul verde vanno bene. Sono i primi da spostare se serve spazio.

**La rampa resta sul grigio**, deciso il 2026-08-07. Era stata segnalata come dubbio perche' e' in piena vista attraverso il varco ed e' la superficie su cui il dado rotola fuori, quindi col verde si leggerebbe come suolo. Sta sulla pietra: la lettura e' pietra costruita contro l'erba. Non e' una questione aperta.

Il corpo principale esce **attaccato alle due bande di rastremazione** tramite pieghe, quindi condividono il colore per forza: separarle richiederebbe un taglio esplicito in Pepakura.

**La verifica dopo ogni re-impaginazione** e' `python tools/pattern.py inventario`, che controlla tre invarianti — **636 segmenti, 13 pezzi, 15 fori** — e identifica ogni pezzo con il suo blocco e colore. Sono gli stessi pezzi comunque li si disponga, quindi quei numeri devono tornare identici: se cambiano, il layout ha perso o duplicato qualcosa, ed e' un errore che guardando il foglio non si vede. Verificato sul layout a due colori: tutti e tre tornano.

### Posizionamento, che condiziona tutto il resto

Prezzi rilevati su Etsy (vedi `memory/reference_etsy_posizionamento.md`): i PDF di casette da colorare stanno a **2-5 €**, i template low-poly su cartoncino colorato a **13-24 €**, i kit fisici pretagliati a **55 €**. Sono scaffali diversi. La torre e' alta 30 cm, ha 13 pezzi e **fa una cosa** — tira i dadi: il suo posto e' il secondo. Vendere il template bianco da colorare resta valido come *variante*, non come prodotto principale, o si finisce sullo scaffale da 3 €.

### Stato di Pepakura e licenza

Verificato aprendo i menu: `File → Print to PDF` **funziona** in versione gratuita, ed e' da lì che viene il pattern. Sono invece **bloccati dalla licenza** l'export SVG/DXF/EPS e `3D Model & Image for Texture Editing`.

Conseguenza pratica: **la licenza non serve per la prova di stampa**, che e' il prossimo passo. Servirebbe per l'export vettoriale verso i plotter da taglio (che con la palette chiara non e' necessario) e per salvare il `.pdo`. Nota su quella voce bloccata: il suo dialogo avvisa che *azzererebbe tutte le UV*, quindi cancellerebbe quelle provenienti da Blender. Le due strade sono alternative, e quella bloccata e' anche quella che toglierebbe il controllo.

Il codice texture rimosso resta recuperabile dalla storia git (commit `2d6a87d` in avanti). L'esportatore OBJ resta a `export_uv=False, export_materials=False`.

## 7. Trappole di ambiente

- Il **viewport di Blender non si ridisegna** dopo modifiche via script: senza `tag_redraw()` + `view_layer.update()` gli screenshot mostrano lo stato precedente. Ci sono cascato due volte. La funzione `refresh_viewport()` lo fa.
- Il **`.gitignore` viene dal template Visual Studio** e ignora `*.obj` (là sono file oggetto compilati): gli export sparivano dai commit senza alcun errore. Dopo aver committato artefatti, verificare con `git ls-files export`. Dettagli: `memory/reference_gitignore_obj.md`.
- Insidie di `bmesh.ops` incontrate (extrude che lascia facce fantasma, wire edge orfani, liste con entità duplicate, normali nulle sulle facce appena create): `memory/reference_bmesh_lessons.md`.

## 8. Mappa dei file

| file | contenuto |
|---|---|
| `build_tower.py` | generatore parametrico della mesh — **fonte di verità del modello** |
| `tools/pattern.py` | legge, valida e decora il cartamodello uscito da Pepakura |
| `PaperDiceTower7.blend` | scena Blender, versione di riferimento a 7 lati |
| `PaperDiceTower.blend` | variante a 9 lati, conservata per il confronto |
| `export/*.obj` | input per Pepakura |
| `export/*.pdf` | pattern: quello di Pepakura più le due varianti rigenerate |
| `README.md` | descrizione del modello e dello stato |
| `ISTRUZIONI.md` | documento per l'**acquirente** |
| `checklist_export_pepakura.md` | verifiche prima dell'unfold, scala, note di assemblaggio |
| `memory/MEMORY.md` | indice delle note di collaborazione |
| `screenshots/` | 31 catture, una per iterazione: utili per ricostruire il perché di una forma |

Nota: `checklist_export_pepakura.md` era arrivato da un altro progetto e conteneva indicazioni in conflitto (un limite di 30-60 facce, e il consiglio di rimuovere le facce interne — mentre qui il guscio **deve** restare cavo, è lo scivolo dei dadi). È stato riscritto per questo progetto.
