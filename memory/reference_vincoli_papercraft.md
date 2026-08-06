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

**Dettagli in rilievo: prolungare il pannello, non aggiungere blocchi.** La carta ha spessore zero, quindi una merlatura e' semplicemente il muro che continua verso l'alto con il bordo a zigzag: si ritaglia il profilo e la striscia si piega tutta insieme, zero pezzi in piu'. Come blocchi separati sarebbero scatoline da ~9x6 mm alla scala di stampa, inassemblabili. Stesso ragionamento per un muretto di cinta: pannello a spessore zero con una linguetta orizzontale alla base da incollare (senza la linguetta un pannello a spessore zero non sta in piedi), non una scatola sottile con decine di facce minuscole.

Vincolo che ne deriva: due merli adiacenti devono avere la stessa altezza. Se differiscono, al loro spigolo comune nascono due bordi liberi sovrapposti invece di una piega, cioe' due lembi di carta scollegati nello stesso punto. Con altezze uguali i vertici si condividono e i due merli si fondono in uno piu' largo.

**Pezzi interni separati.** Elementi come la rampa interna conviene tenerli come oggetti separati: nel papercraft sono sotto-assemblaggi che si incollano dentro, e non obbligano a tagliare il guscio con piani inclinati (fonte di facce non planari).

**Contare le pagine, non solo i pezzi.** Lo spreco di carta e' una dimensione di costo da misurare come le altre, e si misura sommando l'area delle facce e confrontandola con l'area stampabile di un A4 (~190x277 mm). Trappola concreta: Pepakura crea un documento per file OBJ e ogni documento occupa almeno una pagina, quindi esportare un file per sotto-assemblaggio fa stampare pagine quasi bianche per i pezzi piccoli. In questo modello a 200 mm di altezza: `Torre` 70% di un A4, `Muro` 8%, `Rampa` 6%. Un file unico li fa annidare sugli stessi fogli restando pezzi distinti e numerati.

**Verificare gli incastri contro la mesh vera, non contro i raggi.** La torre e' un ennagono: le sue facce piatte passano piu' vicine all'asse del cerchio circoscritto. Confrontare "raggio del pezzo interno" con "raggio del guscio" da' un falso via libera. Serve un ray-cast dall'asse contro la mesh reale (`check_ramp_fits` in build_tower.py).

**Come applicarla:** dopo ogni modifica geometrica eseguire i controlli in `build_tower.py` e pretendere: 0 non-manifold, 0 vertici isolati, 0 facce non planari, boundary == atteso, incastri con margine di almeno ~0.04 unita' (~1 mm alla scala di stampa).
