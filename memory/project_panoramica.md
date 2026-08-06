---
name: project-panoramica
description: Cosa è il modello PaperDiceTower, come si rigenera, e le correzioni chieste dall'utente finora
metadata:
  type: project
---

Torre dadi fantasy low-poly modellata in Blender, da esportare e unfoldare con Pepakura in un prodotto papercraft destinato alla vendita su Etsy. Reference fornite dall'utente: una torre dadi pieghevole in legno tagliato al laser, poi una torre in resina con base rocciosa, finestre ad arco e muro perimetrale.

**Versione di riferimento scelta dall'utente il 2026-08-06: 7 lati, stampata alta 300 mm** (`PaperDiceTower7.blend`, default dello script). `PaperDiceTower.blend` a 9 lati resta come variante, riproducibile identica con `build_all(sides=9)` (verificato: 222 vertici, 398 spigoli, 158 facce).

**Perché servivano entrambe le leve, e questo va capito prima di "semplificare" ancora:** ridurre le facce allarga solo i pannelli (fusto 16,0 → 20,2 mm) perche' sono frazioni del perimetro. Feritoie, soglie e altri dettagli piccoli sono **misure assolute** e non cambiano affatto: restano a 2,6 e 2,2 mm. Solo l'aumento di scala li allarga (feritoia 2,6 → 3,9 mm). Chi in futuro riducesse ancora le facce non otterrebbe nulla sui dettagli fragili, che sono il vero limite del ritaglio a mano.

Costo della scelta: 4 pagine A4 invece di 2 (3 impaginando a mano), e area della carta che cresce col quadrato della scala.

**Il modello si rigenera dallo script, non si modifica a mano.** `build_tower.py` in radice del repo è la fonte di verità: contiene i parametri in cima, le funzioni di costruzione e i controlli di validità. Da dentro Blender: `exec(open(r"E:\repos\PaperDiceTower\build_tower.py").read())`. È idempotente (cancella e ricrea gli oggetti che genera).

**Perché uno script:** modellando a incrementi via MCP, ogni ritocco di proporzioni obbligava a rifare tutto a mano, e il `.blend` è un binario opaco in git. Con lo script le modifiche sono leggibili in diff e un collega può ricostruire il modello dal repo.

**Stato al 2026-08-05:** geometria completa e OBJ esportati in `export/` (torre alta 200 mm). Tre oggetti = tre sotto-assemblaggi: `Torre` (guscio), `Rampa` (cuneo interno), `Muro` (cinta decorativa). Contiene: plinto roccioso, fusto slanciato (~3,5:1) con 9 feritoie, silhouette a stadi, 9 finestre ad arco passanti, varco + vaschetta a livello suolo, rampa di uscita, cima aperta con merlature, muro di cinta merlato con apertura ad arco.

**Prossimo passo, non ancora fatto:** l'utente deve aprire gli OBJ in Pepakura, fare l'unfold e assemblare una stampa di prova. I controlli automatici garantiscono che la mesh sia valida, non che l'unfold dia pezzi comodi: quella prova va fatta prima di investire tempo in materiali e texture. I parametri piu' a rischio di dover cambiare sono elencati nel README (feritoie a 2,8 mm, varco a 29 mm contro un d20 da 20 mm, soglia dell'apertura del muro a 2,3 mm).

**Correzioni chieste dall'utente, da non reintrodurre:**
- La prima versione completa era "brutta e non vendibile su Etsy". La rastremazione continua dava una silhouette da proiettile: servono tratti cilindrici (tamburi) tra un restringimento e l'altro. Anche il rapporto conta — a 2,3:1 sembrava un macinapepe, a 3,5:1 legge come torre.
- I merli come cubi con orientamento fisso nello spazio mondo sembravano detriti casuali: gli oggetti ripetuti attorno a un asse vanno ruotati tangenzialmente alla curvatura. Vanno inoltre appoggiati su un parapetto dedicato, non attaccati direttamente al cono, e con sagoma a tronco di piramide invece che parallelepipedo.
- La vaschetta deve stare a livello del suolo (z=0): sospesa sopra un gradino i dadi restano dentro. E il pavimento interno va inclinato verso l'uscita, altrimenti un dado si ferma sul piatto.
- Le forme puramente a scatola (vaschetta rettangolare) leggono come prototipo tecnico: meglio svasature e settori radiali — che per di più risolvono la planarità delle facce.

Vedi [[reference-vincoli-papercraft]] per i vincoli di validità della mesh, [[reference-bmesh-lessons]] per le insidie dell'API, [[reference-memoria-su-disco]] per la policy di memoria.
