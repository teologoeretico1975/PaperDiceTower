---
name: reference-vincoli-papercraft
description: Vincoli di validita' di una mesh destinata all'unfold in Pepakura — planarita', fori vs tasche, costo di assemblaggio
metadata:
  type: reference
---

Controllare la manifold-ness non basta per un modello papercraft. Vincoli imparati lavorando su [[project-panoramica]]:

**Planarita'.** Ogni faccia con piu' di 3 vertici deve essere planare. Una faccia svergolata nello spazio non si piega mai combaciando sulla carta, anche con topologia perfetta. Il caso tipico: un quad tra due anelli di cui uno ha raggi irregolari e l'altro regolari — il quad risulta torto. Rimedio: triangolare quelle facce (un triangolo e' planare per definizione) oppure progettare le forme perche' i vertici cadano sullo stesso piano. Nel modello i fianchi della vaschetta sono complanari proprio perche' la vaschetta e' un settore radiale: tutti i vertici di un fianco stanno sullo stesso piano verticale radiale. Con una vaschetta rettangolare sarebbero stati svergolati.

**Spigoli di bordo attesi.** In un modello con aperture volute i boundary edge non devono essere zero: vanno confrontati con un valore atteso derivato dalla topologia delle aperture, altrimenti un buco involontario si nasconde nel conteggio.

**Fori passanti invece di tasche incassate.** Una finestra incassata sembra piu' ricca nel viewport ma nell'unfold diventa 9 pezzi per finestra (8 pareti sottili piu' il fondo). Alla scala di stampa prevista quelle pareti sono ~3 mm: inassemblabili a mano. Il foro passante costa 0 pezzi (Pepakura ritaglia solo la sagoma) e si puo' chiudere con un foglietto di carta velina colorata dietro, che fa da vetro. Regola generale: prima di modellare un dettaglio in rilievo, contare quanti pezzi diventa nell'unfold e quanto misurano davvero alla scala di stampa.

**Pezzi interni separati.** Elementi come la rampa interna conviene tenerli come oggetti separati: nel papercraft sono sotto-assemblaggi che si incollano dentro, e non obbligano a tagliare il guscio con piani inclinati (fonte di facce non planari).

**Verificare gli incastri contro la mesh vera, non contro i raggi.** La torre e' un ennagono: le sue facce piatte passano piu' vicine all'asse del cerchio circoscritto. Confrontare "raggio del pezzo interno" con "raggio del guscio" da' un falso via libera. Serve un ray-cast dall'asse contro la mesh reale (`check_ramp_fits` in build_tower.py).

**Come applicarla:** dopo ogni modifica geometrica eseguire i controlli in `build_tower.py` e pretendere: 0 non-manifold, 0 vertici isolati, 0 facce non planari, boundary == atteso, incastri con margine di almeno ~0.04 unita' (~1 mm alla scala di stampa).
