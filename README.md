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

Per generare gli OBJ da aprire in Pepakura, dopo lo script:

```python
export_for_pepakura(target_height_mm=200)
```

Scrive `export/PaperDiceTower.obj` con tutti i sotto-assemblaggi in un file solo e la scala già applicata (i numeri nell'OBJ sono millimetri). Un file solo perché Pepakura occupa almeno una pagina per documento: tre file separati significherebbero tre pagine di cui due quasi bianche. Vedi [checklist_export_pepakura.md](checklist_export_pepakura.md).

Perché uno script e non solo il `.blend`: il file Blender è un binario opaco in git, mentre lo script rende le modifiche leggibili in diff, le proporzioni ritoccabili in una riga, e permette a un collega di ricostruire il modello dal repo.

## Struttura del modello

Tre oggetti, cioè tre sotto-assemblaggi distinti: `Torre` (guscio), `Rampa` (cuneo interno), `Muro` (cinta decorativa).

- **Plinto**: base svasata con raggi irregolari, roccia semplificata a facce piatte.
- **Fusto**: slanciato (rapporto altezza/larghezza ~3,5:1), con 9 **feritoie** verticali passanti ad altezze alternate — alternarle evita di rimuovere carta lungo un unico anello del tubo, che è la parte portante.
- **Silhouette a stadi**: tronchi di cono alternati a tratti cilindrici (tamburi). I tamburi sono quello che distingue una torre da un proiettile: senza tratti piatti tra un restringimento e l'altro il profilo legge come una curva continua.
- **Corpo principale**: tamburo più largo del fusto, con 9 **finestre ad arco a punta passanti** (contorno faceted: base rettangolare più arco in 4 segmenti). Sono fori, non tasche: dietro si incolla carta velina colorata come "vetro".
- **Varco e vaschetta**: apertura che attraversa plinto e base del fusto (il plinto da solo è troppo basso perché passi un dado), con vaschetta a settore radiale saldata a livello del suolo.
- **Rampa**: cuneo inclinato ~17° che convoglia i dadi verso il varco, altrimenti su un pavimento piatto restano dentro.
- **Parapetto e merlature**: mensola e fascia cilindrica in cima, con la merlatura ottenuta prolungando i pannelli del parapetto. Cima aperta: è da lì che entrano i dadi.
- **Muro di cinta**: arco sfaccettato davanti alla torre, merlato, con apertura ad arco decorativa e linguetta di incollaggio alla base.

### Vincolo sulle merlature

Due merli adiacenti devono avere la **stessa altezza**. Se differiscono, al loro spigolo comune nascono due bordi liberi sovrapposti invece di una piega: due lembi di carta scollegati nello stesso punto. Con altezze uguali i vertici si condividono e i merli si fondono in uno più largo.

## Struttura della cartella

- `build_tower.py` — generatore parametrico del modello (fonte di verità)
- `PaperDiceTower.blend` — scena Blender
- `export/` — OBJ per Pepakura, un file per sotto-assemblaggio (rigenerabili)
- `checklist_export_pepakura.md` — verifiche prima dell'unfold e note di assemblaggio
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

Da fare dopo l'unfold: materiali e texture, che sono ciò che separa il modello attuale (grigio da viewport) dall'aspetto della reference.
