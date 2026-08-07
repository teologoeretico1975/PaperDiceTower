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


## Struttura della cartella

- `build_tower.py` — generatore parametrico del modello (fonte di verità)
- `tools/pattern.py` — legge il PDF di Pepakura, ne valida i pezzi e ne rigenera il pattern con il layer di decoro
- `PaperDiceTower.blend` — scena Blender, variante a **9 lati**
- `PaperDiceTower7.blend` — variante semplificata a **7 lati** (vedi sotto)
- `export/` — OBJ per Pepakura più i PDF del pattern e gli screenshot del layout. Tutto versionato: con la versione gratuita di Pepakura il progetto `.pdo` non è salvabile, quindi il PDF e lo screenshot sono l'unico record dell'impaginazione manuale
- `checklist_export_pepakura.md` — verifiche prima dell'unfold e note di assemblaggio
- `ISTRUZIONI.md` — documento per l'**acquirente**: montaggio e risoluzione dei problemi
- `screenshots/` — catture del viewport per ogni iterazione
- `memory/` — note di collaborazione per sessioni Claude future (vedi `memory/MEMORY.md`)

## Stato

**Geometria completa e validata, unfold verificato in Pepakura, prova di stampa ancora da fare.** Silhouette, finestre, feritoie, varco, vaschetta, rampa, deflettori, merlature, muro di cinta. Tutti i controlli passano su tutti e quattro gli oggetti, alla versione di riferimento (7 lati):

| oggetto | facce | non-manifold | non planari | bordi |
|---|---|---|---|---|
| `Torre` | 123 | 0 | 0 | = attesi |
| `Muro` | 16 | 0 | 0 | = attesi |
| `Deflettori` | 16 | 0 | 0 | = attesi |
| `Rampa` | 5 | 0 | 0 | 0 (guscio chiuso) |

Il pattern è impaginato su **2 pagine A4** (4 alla scala di 300 mm), PDF vettoriale. OBJ, PDF e screenshot dei layout sono in `export/`.

### Prossimo passo: prova di stampa e assemblaggio

I controlli garantiscono che la mesh sia *valida* e Pepakura che l'unfold sia pulito; nessuno dei due dice se i pezzi sono comodi da montare. Quella è la prova che manca.

Punti dove è più probabile dover tornare sui parametri, in ordine di rischio (misure a 300 mm):

1. **Feritoie larghe 3,9 mm** (`SLIT_HALF_W`) — il dettaglio più fragile al taglio. Se si strappano, allargarle.
2. **Soglia dell'apertura del muro**, ~3,3 mm (`WALL_GATE["v_bottom"]`) — se si strappa, alzare il bordo inferiore.
3. **Catena di triangoli del plinto** (`PLINTH_JAG`) — pieghe ravvicinate, scomode da cordonare.
4. **Varco di uscita alto 41,5 mm** contro un d20 da ~20 mm — ampio margine, ma va provato col set di dadi vero (`opening_top` in `add_dice_tray`).

### Validazione del cartamodello

Oltre ai controlli sulla mesh c'è un controllo sull'**output di Pepakura**, che per molto tempo era l'unico anello non verificato della catena:

```bash
python tools/pattern.py inventario export/PaperDiceTower7_300.pdf
```

Non servono librerie PDF: il file è vettoriale e si decomprime con zlib. Il tool misura i pezzi veri e riconosce le feature dalla firma dimensionale. Risultato alla scala di riferimento:

| | |
|---|---|
| pagine | 4 × A4, area utile 200 × 287 mm |
| segmenti vettoriali | 636, più 48 tessere raster di sfondo (innocue) |
| finestre ad arco | 7 × 42,0 × 11,8 mm |
| feritoie | 4 × 3,9 × 35,0 + 3 × 3,9 × 30,6 mm |
| deflettori | 4 × 33,8 × 68,1 mm |
| pezzo più grande | 180,8 × 250,0 mm — **entra in A4, niente da spezzare** |

Il punto fragile confermato è uno solo: le feritoie, larghe **3,9 mm**, che sono la dimensione minima di tutto il cartamodello.

### Grafica

**Il colore viene dal cartoncino colorato, non dalla stampa**, su una palette chiara. Il decoro è **vettoriale e registrato sulle feature**: `tools/pattern.py pdf` lo genera dal contorno reale delle finestre (archivolto a conci, chiave d'arco, soglia) e produce due varianti del pattern, `_vettoriale.pdf` e `_decoro.pdf`, nelle coordinate di pagina originali.

Perché questa strada e non una texture: una tile ripetibile non sa dove si trova sul modello, quindi non può disegnare l'arco attorno a *quella* finestra — è il vincolo che ha fatto abbandonare il capitolo texture. Il cartamodello 2D invece lo sa. Vedi `memory/reference_decoro_registrato.md` e `memory/reference_texture_tentativi.md`.
