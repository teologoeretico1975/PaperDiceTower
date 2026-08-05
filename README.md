# PaperDiceTower

Modello Blender di una torre dadi fantasy low-poly, pensato per essere esportato e "unfoldato" con Pepakura in un prodotto papercraft (ispirato a torri dadi in legno vendute su Etsy).

## Vincolo tecnico

Geometria **completamente faceted**: solo facce piatte, spigoli netti. Niente subdivision surface, sculpting o superfici curve smooth — altrimenti l'unfold in Pepakura non funziona.

## Struttura del modello

- **Base**: cilindro a 9 lati.
- **Corpo**: rastremazione "a stadi" — tronchi di cono alternati a tratti cilindrici (tamburi), non un cono continuo, per un profilo da torre invece che da proiettile.
- **Vaschetta raccogli-dadi**: apertura nella parete + vassoio svasato a livello del suolo, collegata a un'apertura sulla cima della torre — i dadi entrano dall'alto e cadono nella vaschetta (nessuna rampa/deflettore interno).
- **Parapetto e merlature**: fascia cilindrica (cammino di ronda) sotto una corona di 7 merli a tronco di piramide, altezze irregolari e un paio di vuoti, per un effetto "diroccato".
- **Feritoia**: finestra a fessura incassata (non passante) su una faccia della base, opposta alla vaschetta.

## Struttura della cartella

- `PaperDiceTower.blend` — file Blender principale
- `screenshots/` — catture del viewport per ogni fase/iterazione
- `memory/` — note di collaborazione per sessioni Claude future (vedi `memory/MEMORY.md`)

## Stato

Modello base completo (fasi 1-5) e rivisto due volte dopo feedback sulla resa visiva. Verificato ad ogni passaggio con controllo di manifold-ness (0 spigoli non-manifold) per garantire un buon unfold.
