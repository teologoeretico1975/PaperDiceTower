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

**Deflettori interni, aggiunti il 2026-08-06:** quattro strisce corrugate che attraversano il fusto da parete a parete (oggetto `Deflettori`). Servivano perche' senza il dado fa 263 mm di caduta libera in un tubo largo 63 mm e arriva giu' con la faccia con cui e' entrato. Il dimensionamento non si ricava a ragionamento: ci ho provato e ho sbagliato due volte di seguito. Vanno misurati **due criteri opposti** — l'insieme non deve lasciare un canale verticale libero (o il dado cade senza toccare), ogni striscia da sola deve lasciar passare il dado piu' grande (o si intasa). Vedi [[reference-vincoli-papercraft]].

**Il modello si rigenera dallo script, non si modifica a mano.** `build_tower.py` in radice del repo è la fonte di verità: contiene i parametri in cima, le funzioni di costruzione e i controlli di validità. Da dentro Blender: `exec(open(r"E:\repos\PaperDiceTower\build_tower.py").read())`. È idempotente (cancella e ricrea gli oggetti che genera).

**Perché uno script:** modellando a incrementi via MCP, ogni ritocco di proporzioni obbligava a rifare tutto a mano, e il `.blend` è un binario opaco in git. Con lo script le modifiche sono leggibili in diff e un collega può ricostruire il modello dal repo.

**Stato al 2026-08-07:** geometria completa e validata, unfold verificato in Pepakura (2 pagine A4, PDF vettoriale, nessuna sovrapposizione), OBJ e PDF in `export/`. Quattro oggetti = quattro sotto-assemblaggi: `Torre` (guscio), `Rampa` (cuneo interno), `Muro` (cinta decorativa), `Deflettori` (quattro strisce corrugate). Contiene: plinto roccioso, fusto slanciato (~3,5:1) con feritoie, silhouette a stadi, finestre ad arco passanti, varco + vaschetta a livello suolo, rampa di uscita, cima aperta con merlature, muro di cinta merlato con apertura ad arco.

**Il capitolo materiali e texture e' stato azzerato il 2026-08-07** su richiesta dell'utente: "i test fatti fino adesso danno in output risultati mediocri, compreso l'applicazione delle skin procedurali e quelle scaricate con licenza a pagamento. direi di annullare tutto, ripartire da zero, dall'idea, dal concept". Rimossi dal repo `make_textures.py`, la cartella `textures/`, le varianti di export e i materiali nello script; l'esportatore e' tornato a `export_uv=False, export_materials=False`. **Nessuno dei fallimenti era tecnico** — il problema era estetico, ed e' cosi' che va affrontato al prossimo giro. Le strade gia' battute e il vincolo di fondo sono in [[reference-texture-tentativi]], da leggere prima di ritentare. Il codice resta recuperabile dalla storia git (commit `2d6a87d` in avanti).

**Prossimo passo, non ancora fatto:** stampare e assemblare. I controlli automatici garantiscono che la mesh sia valida e Pepakura che l'unfold sia pulito; nessuno dei due dice se i pezzi sono comodi da montare. I parametri piu' a rischio sono elencati nel README (feritoie a 3,9 mm, soglia dell'apertura del muro a 3,3 mm, pieghe del plinto, varco a 41,5 mm contro un d20 da 20 mm).

**Correzioni chieste dall'utente, da non reintrodurre:**
- La prima versione completa era "brutta e non vendibile su Etsy". La rastremazione continua dava una silhouette da proiettile: servono tratti cilindrici (tamburi) tra un restringimento e l'altro. Anche il rapporto conta — a 2,3:1 sembrava un macinapepe, a 3,5:1 legge come torre.
- I merli come cubi con orientamento fisso nello spazio mondo sembravano detriti casuali: gli oggetti ripetuti attorno a un asse vanno ruotati tangenzialmente alla curvatura. Vanno inoltre appoggiati su un parapetto dedicato, non attaccati direttamente al cono, e con sagoma a tronco di piramide invece che parallelepipedo.
- La vaschetta deve stare a livello del suolo (z=0): sospesa sopra un gradino i dadi restano dentro. E il pavimento interno va inclinato verso l'uscita, altrimenti un dado si ferma sul piatto.
- Le forme puramente a scatola (vaschetta rettangolare) leggono come prototipo tecnico: meglio svasature e settori radiali — che per di più risolvono la planarità delle facce.

Vedi [[reference-vincoli-papercraft]] per i vincoli di validità della mesh, [[reference-bmesh-lessons]] per le insidie dell'API, [[reference-memoria-su-disco]] per la policy di memoria.
