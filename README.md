# PaperDiceTower

Modello Blender di una torre dadi fantasy low-poly, pensato per essere esportato e "unfoldato" con Pepakura in un prodotto papercraft (ispirato a torri dadi vendute su Etsy).

## Vincolo tecnico

Geometria **completamente faceted**: solo facce piatte, spigoli netti. Niente subdivision surface, sculpting o superfici curve smooth.

Ogni faccia deve inoltre essere **planare**: una faccia svergolata nello spazio non si piega mai combaciando sulla carta, anche se la topologia è impeccabile. Non basta controllare la manifold-ness — vedi `check_mesh()`.

## Come rigenerare il modello

Il modello non si modifica a mano: si rigenera dallo script, che è la fonte di verità. Da dentro Blender (Scripting, o via connettore MCP):

```python
exec(open(r"E:\repos\PaperDiceTower\build_tower.py").read())
```

I parametri (proporzioni, finestre, vaschetta, rampa) sono in cima a [build_tower.py](build_tower.py). Lo script stampa un report di verifica ed è idempotente: cancella e ricrea gli oggetti che genera.

Perché uno script e non solo il `.blend`: il file Blender è un binario opaco in git, mentre lo script rende le modifiche leggibili in diff, le proporzioni ritoccabili in una riga, e permette a un collega di ricostruire il modello dal repo.

## Struttura del modello

Oggetto `Torre` (guscio) e oggetto `Rampa` (pezzo interno separato).

- **Plinto**: base svasata con raggi irregolari, roccia semplificata a facce piatte.
- **Fusto**: slanciato (rapporto altezza/larghezza ~3,5:1).
- **Silhouette a stadi**: tronchi di cono alternati a tratti cilindrici (tamburi). I tamburi sono quello che distingue una torre da un proiettile: senza tratti piatti tra un restringimento e l'altro il profilo legge come una curva continua.
- **Corpo principale**: tamburo più largo del fusto, con 9 **finestre ad arco a punta passanti** (contorno faceted: base rettangolare più arco in 4 segmenti). Sono fori, non tasche: dietro si incolla carta velina colorata come "vetro".
- **Varco e vaschetta**: apertura che attraversa plinto e base del fusto (il plinto da solo è troppo basso perché passi un dado), con vaschetta a settore radiale saldata a livello del suolo.
- **Rampa**: cuneo inclinato ~17° che convoglia i dadi verso il varco, altrimenti su un pavimento piatto restano dentro.
- **Parapetto**: mensola e fascia cilindrica in cima, dove poggeranno le merlature.

## Struttura della cartella

- `build_tower.py` — generatore parametrico del modello (fonte di verità)
- `PaperDiceTower.blend` — scena Blender
- `screenshots/` — catture del viewport per ogni iterazione
- `memory/` — note di collaborazione per sessioni Claude future (vedi `memory/MEMORY.md`)

## Stato

Fatti: silhouette, finestre, varco, vaschetta, rampa. Da fare: cima aperta con merlature, feritoie sul fusto basso, muro esterno decorativo.
