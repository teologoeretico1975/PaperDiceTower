# PaperDiceTower

Modello Blender di una torre dadi fantasy low-poly, pensato per essere esportato e "unfoldato" con Pepakura in un prodotto papercraft (ispirato a torri dadi vendute su Etsy).

> **Se stai prendendo in mano il progetto ora, parti da [HANDOVER.md](HANDOVER.md).**

## Vincolo tecnico

Geometria **completamente faceted**: solo facce piatte, spigoli netti. Niente subdivision surface, sculpting o superfici curve smooth.

Ogni faccia deve inoltre essere **planare**: una faccia svergolata nello spazio non si piega mai combaciando sulla carta, anche se la topologia è impeccabile. Non basta controllare la manifold-ness — vedi `check_mesh()`.

## Come rigenerare il modello

Il modello non si modifica a mano: si rigenera dallo script, che è la fonte di verità. Da dentro Blender (Scripting, o via connettore MCP):

```python
exec(open(r"E:\repos\PaperDiceTower\build_tower.py").read())
```

I parametri (proporzioni, finestre, vaschetta, rampa, merlature, muro) sono in cima a [build_tower.py](build_tower.py). Lo script stampa un report di verifica ed è idempotente: cancella e ricrea gli oggetti che genera.

### Versione di riferimento: 7 lati, alta 300 mm

È quella di `PaperDiceTower7.blend`, ed è il default dello script (`SIDES = 7`, `REFERENCE_HEIGHT_MM = 300`). La variante a 9 lati resta riproducibile con `build_all(sides=9)` ed è quella di `PaperDiceTower.blend`.

Ci si è arrivati per rendere il modello montabile su carta da 170-200 g/m². Le due modifiche fanno lavori **diversi e non sostituibili**:

| | 9 lati / 20 cm | 7 lati / 20 cm | **7 lati / 30 cm** |
|---|---|---|---|
| pannello del fusto | 16,0 mm | 20,2 mm | **30,4 mm** |
| pannello del parapetto | 12,6 mm | 15,9 mm | **23,9 mm** |
| larghezza feritoia | 2,6 mm | 2,6 mm | **3,9 mm** |
| soglia apertura muro | 2,2 mm | 2,2 mm | **3,3 mm** |
| pagine A4 | 2 | 2 | 4 (3 impaginando a mano) |

Ridurre le facce allarga **solo i pannelli**: feritoie e soglie non cambiano, perché sono misure assolute e non frazioni del perimetro. Solo l'aumento di scala allarga anche quelle. Chi in futuro volesse "semplificare" riducendo ancora le facce non otterrebbe nulla sui dettagli fragili.

Il modello a 9 lati è conservato perché il confronto sopra è l'unica traccia del perché queste scelte sono state fatte.

### Misure a 300 mm

| | |
|---|---|
| varco di uscita | 41,5 mm (un d20 misura ~20 mm) |
| interno del fusto | 63,0 mm |
| finestra | 11,8 × 42,0 mm |
| feritoia | 3,9 × 35,0 mm |
| vaschetta | profonda 45,9 mm, pareti 19,7 mm |
| rampa | dislivello 21,0 mm, larga 39,4 mm al varco |
| deflettore | 35,6 mm sviluppati (30,5 in pianta), creste con passo 7,6 e ampiezza 4,6 mm |

Altezza massima stampabile senza dividere pezzi: **~322 mm** (limite dato dalla striscia del corpo principale contro il lato lungo di un A4). Verificabile con `check_page_fit(target_height_mm=...)`.

Per generare gli OBJ da aprire in Pepakura, dopo lo script:

```python
export_for_pepakura()                                   # riferimento: 7 lati a 300 mm
export_for_pepakura(target_height_mm=200, basename="PaperDiceTower7")   # altra taglia
```

Scrive `export/PaperDiceTower.obj` con tutti i sotto-assemblaggi in un file solo e la scala già applicata (i numeri nell'OBJ sono millimetri). Un file solo perché Pepakura occupa almeno una pagina per documento: tre file separati significherebbero tre pagine di cui due quasi bianche. Vedi [checklist_export_pepakura.md](checklist_export_pepakura.md).

Perché uno script e non solo il `.blend`: il file Blender è un binario opaco in git, mentre lo script rende le modifiche leggibili in diff, le proporzioni ritoccabili in una riga, e permette a un collega di ricostruire il modello dal repo.

## Struttura del modello

Quattro oggetti, cioè quattro sotto-assemblaggi distinti: `Torre` (guscio), `Rampa` (cuneo interno), `Muro` (cinta decorativa), `Deflettori` (quattro strisce corrugate interne).

- **Plinto**: base svasata con raggi irregolari, roccia semplificata a facce piatte.
- **Fusto**: slanciato (rapporto altezza/larghezza ~3,5:1), con 9 **feritoie** verticali passanti ad altezze alternate — alternarle evita di rimuovere carta lungo un unico anello del tubo, che è la parte portante.
- **Silhouette a stadi**: tronchi di cono alternati a tratti cilindrici (tamburi). I tamburi sono quello che distingue una torre da un proiettile: senza tratti piatti tra un restringimento e l'altro il profilo legge come una curva continua.
- **Corpo principale**: tamburo più largo del fusto, con 9 **finestre ad arco a punta passanti** (contorno faceted: base rettangolare più arco in 4 segmenti). Sono fori, non tasche: dietro si incolla carta velina colorata come "vetro".
- **Varco e vaschetta**: apertura che attraversa plinto e base del fusto (il plinto da solo è troppo basso perché passi un dado), con vaschetta a settore radiale saldata a livello del suolo.
- **Rampa**: cuneo inclinato ~17° che convoglia i dadi verso il varco, altrimenti su un pavimento piatto restano dentro.
- **Deflettori**: quattro strisce corrugate che attraversano il fusto da parete a parete, a quote e rotazioni diverse. Senza, il dado fa 263 mm di caduta libera in un tubo largo 63 mm: non tocca nulla e arriva giù con la faccia con cui è entrato, quindi la torre non randomizza niente.
- **Parapetto e merlature**: mensola e fascia cilindrica in cima, con la merlatura ottenuta prolungando i pannelli del parapetto. Cima aperta: è da lì che entrano i dadi.
- **Muro di cinta**: arco sfaccettato davanti alla torre, merlato, con apertura ad arco decorativa e linguetta di incollaggio alla base.

### I deflettori: due criteri opposti

Il dimensionamento non si può ricavare a ragionamento, e provarci mi ha fatto sbagliare due volte. Servono **due misure che tirano in direzioni contrarie**, entrambe nello script:

- `check_baffle_coverage` — l'**insieme** delle strisce non deve lasciare un canale verticale libero più largo del dado **più piccolo** (il d8, ~15 mm, non il d20: è quello il caso peggiore). Altrimenti il dado cade dritto senza toccare niente.
- `check_baffle_passage` — **ogni striscia da sola** deve lasciare un varco più largo del dado **più grande** (d20, 20 mm). Altrimenti il dado si incastra invece di scendere.

Valori raggiunti: canale dritto **1,7 mm**, varco minimo per livello **25,3 mm**. Guardare solo la copertura porta a un imbuto che si intasa.

Da qui vengono le quattro strisce: con due il canale libero restava di 25 mm, e aggiungere ampiezza o una terza piastra non bastava.

### Perché corrugate e non piastre piane

Una piastra incollata su un solo lato e protesa nel vuoto flette e si piega sulla linea di colla, perché la rigidezza a flessione cresce col cubo dell'altezza della sezione e in un foglio piatto quell'altezza è lo spessore della carta. La corrugazione la porta da 0,25 a ~4,6 mm, quindi **non serve cartoncino**. Andando da parete a parete la striscia è inoltre appoggiata a entrambi gli estremi.

**Le pieghe devono correre lungo la luce.** Piegate in senso trasversale si ottiene un soffietto, cioè una molla, più cedevole di un foglio piatto. È l'unico modo di sbagliare questo pezzo.

Scartata la scala a chiocciola: un elicoide non è una superficie sviluppabile, quindi in carta andrebbe approssimato con molte faccette e relative linguette; e funzionalmente il dado ci scivolerebbe sopra invece di rimbalzare.

### Vincolo sulle merlature

Due merli adiacenti devono avere la **stessa altezza**. Se differiscono, al loro spigolo comune nascono due bordi liberi sovrapposti invece di una piega: due lembi di carta scollegati nello stesso punto. Con altezze uguali i vertici si condividono e i merli si fondono in uno più largo.

## Texture

Due tile di muratura **ripetibili**, generate da [make_textures.py](make_textures.py) con il Python di sistema (serve PIL):

```bash
python make_textures.py
```

Ripetibili e non una texture unica perché una tile piccola applicata con UV scalate resta nitida a qualunque scala di stampa e pesa pochi kB, mentre una texture unica per stampare 30 cm a 300 DPI vorrebbe 4096×4096. Lo script verifica da sé la continuità ai bordi confrontando il salto di colore fra bordi opposti con il salto medio interno.

### La muratura viene da una fotoscansione

Se in `textures/src/` c'è una mappa **diffuse** ripetibile, la muratura è derivata da quella; altrimenti lo script ricade su una muratura procedurale. La sorgente non è versionata (pesa MB e a chi usa il kit non serve): versionate sono le tile derivate, che sono il deliverable.

**Verificare la licenza della sorgente prima di vendere il kit.** I pack CC0 (Poly Haven) sono utilizzabili commercialmente, altri no, e dal nome del file non si distingue.

Due rimappature sono obbligatorie, e sono la parte non ovvia:

1. **Schiarire.** Una texture per il 3D è pensata per essere *illuminata*: quella usata ha luminanza media 63/255 e massimo 170, cioè non contiene nemmeno un bianco. Su carta il valore stampato è quello finale, quindi così com'è coprirebbe il **75%** di inchiostro. Portata a media 185 scende al **28%**, e conserva più contrasto fra blocchi e fughe (88) della procedurale che sostituisce (78).
2. **Ridurre la crominanza.** Applicare la gamma canale per canale amplifica la dominante calda della fotografia: la pietra grigia diventava arenaria dorata. Si rimappa la sola luminanza e la crominanza si comprime al 30%.

Il muschio si posiziona dove l'acqua si ferma, combinando le zone in ombra dell'immagine (fughe e cavità) con un rumore ripetibile. Due parametri sono definiti per ciò che si vede e non per valori arbitrari: `coverage_pct` è la frazione di muschio **visibile** (soglia ricavata per percentile, perché un valore assoluto scelto a occhio aveva prodotto l'1% invece del 12%), e `gain` la nettezza del bordo della chiazza — con un valore basso la frangia morbida tingeva di verde il 72% della tile e la pietra risultava verde invece che grigia con chiazze.

Il limite di una tile ripetibile è che **non ha un "basso"**: non può avere più muschio in fondo. La variazione posizionale si ottiene con due varianti assegnate a fasce di altezza — `stone_moss.png` sotto quota 0,96 (~42 mm dal suolo) e su tutto il muro, `stone.png` sopra. Lo stacco cade su uno spigolo orizzontale già esistente, così non taglia una faccia a metà.

Le UV si proiettano con `v` preso dalla quota z in coordinate mondo: è questo che tiene i corsi di muratura allineati tra facce e tra anelli diversi, invece di farli ripartire da zero su ogni pannello.

**Anche rampa e deflettori sono texturizzati**, benché interni: la rampa è in piena vista attraverso il varco ed è la superficie su cui i dadi atterrano, e il deflettore più alto si vede dall'apertura in cima, cioè proprio quando si guarda dentro per lanciare.

Verificato: Pepakura importa la texture e la mostra sui pezzi 2D. L'export scrive `.obj` + `.mtl` + i PNG nella stessa cartella (`path_mode="COPY"`), così è autosufficiente.

### Due varianti stampabili

Il costo di stampa è un vincolo reale, non un dettaglio: si stampano 1.051 cm² su 4-5 fogli A4. Invece di scegliere fra resa e costo si spedisce il kit in **due vesti**, lasciando la scelta a chi stampa:

| variante | inchiostro | per chi |
|---|---|---|
| `linee` | 0% | stampa solo tagli e pieghe: base bianca da colorare o dipingere |
| `tinte_piatte` | 18% | tinte chiare già stampate, da rifinire a mano |
| `muratura` | 28% | modello finito appena assemblato |

Geometria e UV sono identiche fra le varianti: cambiano solo i materiali, quindi `export_all_variants()` riassegna e riesporta senza ricostruire nulla. I nomi delle immagini differiscono per variante, così i file copiati in `export/` non si sovrascrivono.

Le tinte piatte e le linee hanno un vantaggio collaterale: sono abbastanza chiare da lasciare perfettamente leggibili le linee di taglio e piega di Pepakura, che con la muratura di medio grigio ci competono.

### Aggiungere una skin

Costa **una riga** in `TEXTURE_VARIANTS` più una coppia di tile: la geometria non si tocca. Ma il costo vero non è qui.

**Ogni skin richiede la sua impaginazione in Pepakura**, e con la versione gratuita l'impaginazione non è salvabile: sono ~15 minuti di lavoro manuale per skin, ogni volta. Con la licenza si salva un `.pdo`, si sostituisce la texture e si riesporta in pochi minuti.

Quindi un catalogo di skin è economico solo con la licenza. Da verificare, perché decide il flusso di lavoro: se Pepakura permetta di **sostituire l'immagine** in un `.pdo` già impaginato. Se sì, una sola impaginazione serve tutte le skin.

La guida per colorare la versione a tinte piatte è in [ISTRUZIONI.md](ISTRUZIONI.md), che è il documento rivolto all'acquirente — pubblico diverso da questo README.

## Struttura della cartella

- `build_tower.py` — generatore parametrico del modello (fonte di verità)
- `make_textures.py` — generatore delle tile di muratura (Python di sistema, serve PIL)
- `textures/` — le due tile ripetibili, rigenerabili
- `PaperDiceTower.blend` — scena Blender, variante a **9 lati**
- `PaperDiceTower7.blend` — variante semplificata a **7 lati** (vedi sotto)
- `export/` — OBJ per Pepakura più i PDF del pattern e gli screenshot del layout. Tutto versionato: con la versione gratuita di Pepakura il progetto `.pdo` non è salvabile, quindi il PDF e lo screenshot sono l'unico record dell'impaginazione manuale
- `checklist_export_pepakura.md` — verifiche prima dell'unfold e note di assemblaggio
- `ISTRUZIONI.md` — documento per l'**acquirente**: montaggio e guida ai colori
- `screenshots/` — catture del viewport per ogni iterazione
- `memory/` — note di collaborazione per sessioni Claude future (vedi `memory/MEMORY.md`)

## Stato

**Geometria completa e pronta per l'unfold.** Silhouette, finestre, feritoie, varco, vaschetta, rampa, merlature, muro di cinta. Tutti i controlli passano su tutti e tre gli oggetti:

| oggetto | facce | non-manifold | non planari | bordi |
|---|---|---|---|---|
| `Torre` | 158 | 0 | 0 | 135 = attesi |
| `Muro` | 21 | 0 | 0 | 34 = attesi |
| `Rampa` | 5 | 0 | 0 | 0 (guscio chiuso) |

OBJ esportati in `export/`, scalati per una torre alta 200 mm.

### Prossimo passo: prova di unfold e assemblaggio

Nessuno ha ancora aperto il modello in Pepakura. I controlli garantiscono che la mesh sia *valida*, non che l'unfold produca pezzi comodi da montare: quella è la prova che conta e va fatta prima di investire tempo in materiali e texture.

Punti dove è più probabile dover tornare sui parametri, in ordine di rischio:

1. **Pezzi a scheggia nell'unfold** — se Pepakura genera pannelli stretti e allungati, la faccia corrispondente va allargata in `build_tower.py`.
2. **Feritoie larghe 2,8 mm** (`SLIT_HALF_W`) — al limite del ritagliabile a mano. Se si strappano, allargarle.
3. **Varco di uscita alto 29 mm** contro un d20 da ~20 mm — sulla carta passa, ma va provato col set di dadi vero (`opening_top` in `add_dice_tray`).
4. **Soglia dell'apertura del muro**, ~2,3 mm (`WALL_GATE["v_bottom"]`) — se si strappa, alzare il bordo inferiore.

Materiali e texture sono fatti (vedi sopra) e verificati passare in Pepakura. La grafica è volutamente di base: serviva prima chiudere il rischio che la versione gratuita di Pepakura scartasse la texture. Ora che è verificato, si può investire — l'occlusione ambientale cotta nella texture è il passo che darebbe più profondità.
