---
name: project-panoramica
description: Cosa è il modello PaperDiceTower, come si rigenera, e le correzioni chieste dall'utente finora
metadata:
  type: project
---

Torre dadi fantasy low-poly modellata in Blender, da esportare e unfoldare con Pepakura in un prodotto papercraft destinato alla vendita su Etsy. Reference fornite dall'utente: una torre dadi pieghevole in legno tagliato al laser, poi una torre in resina con base rocciosa, finestre ad arco e muro perimetrale.

**Il modello si rigenera dallo script, non si modifica a mano.** `build_tower.py` in radice del repo è la fonte di verità: contiene i parametri in cima, le funzioni di costruzione e i controlli di validità. Da dentro Blender: `exec(open(r"E:\repos\PaperDiceTower\build_tower.py").read())`. È idempotente (cancella e ricrea gli oggetti che genera).

**Perché uno script:** modellando a incrementi via MCP, ogni ritocco di proporzioni obbligava a rifare tutto a mano, e il `.blend` è un binario opaco in git. Con lo script le modifiche sono leggibili in diff e un collega può ricostruire il modello dal repo.

**Stato al 2026-08-05:** oggetti `Torre` (guscio) e `Rampa` (cuneo interno separato). Fatti: plinto roccioso, fusto slanciato (~3,5:1), silhouette a stadi, 9 finestre ad arco passanti sul corpo principale, varco + vaschetta a livello suolo, rampa di uscita, parapetto. Da fare: cima aperta con merlature, feritoie sul fusto basso, muro esterno decorativo.

**Correzioni chieste dall'utente, da non reintrodurre:**
- La prima versione completa era "brutta e non vendibile su Etsy". La rastremazione continua dava una silhouette da proiettile: servono tratti cilindrici (tamburi) tra un restringimento e l'altro. Anche il rapporto conta — a 2,3:1 sembrava un macinapepe, a 3,5:1 legge come torre.
- I merli come cubi con orientamento fisso nello spazio mondo sembravano detriti casuali: gli oggetti ripetuti attorno a un asse vanno ruotati tangenzialmente alla curvatura. Vanno inoltre appoggiati su un parapetto dedicato, non attaccati direttamente al cono, e con sagoma a tronco di piramide invece che parallelepipedo.
- La vaschetta deve stare a livello del suolo (z=0): sospesa sopra un gradino i dadi restano dentro. E il pavimento interno va inclinato verso l'uscita, altrimenti un dado si ferma sul piatto.
- Le forme puramente a scatola (vaschetta rettangolare) leggono come prototipo tecnico: meglio svasature e settori radiali — che per di più risolvono la planarità delle facce.

Vedi [[reference-vincoli-papercraft]] per i vincoli di validità della mesh, [[reference-bmesh-lessons]] per le insidie dell'API, [[reference-memoria-su-disco]] per la policy di memoria.
