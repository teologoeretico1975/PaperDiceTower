---
name: reference-texture-tentativi
description: Le strade di texture provate su PaperDiceTower e perché sono state tutte scartate — da leggere prima di ritentare
metadata:
  type: reference
---

Il 2026-08-07 l'utente ha fatto rimuovere l'intero capitolo texture: "i test fatti fino adesso danno in output risultati mediocri, compreso l'applicazione delle skin procedurali e quelle scaricate con licenza a pagamento". Si riparte da concept. Questa nota serve a non ripercorrere le stesse strade.

**Cosa funzionava tecnicamente.** Nessuno dei fallimenti era tecnico: le tile erano ripetibili senza cuciture (salto ai bordi 0,03 contro 1,0 interno), Pepakura importava le texture e le mostrava sui pezzi 2D, l'export scriveva `.obj` + `.mtl` + PNG in modo autosufficiente, e il doppio layer UV per le skin dipinte era verificato end-to-end. Il problema era **estetico**, e va affrontato come tale.

**Tile procedurale in pietra grigia.** Blocchi irregolari generati, fughe scure, muschio nelle fughe. Copertura d'inchiostro 45%, contrasto blocchi/fughe 78. Giudizio: mediocre.

**Tile da fotoscansione (Poly Haven, diffuse 4k).** Migliore della procedurale su tutti i numeri — inchiostro 28%, contrasto 88 — e inizialmente apprezzata. Due rimappature obbligatorie scoperte allora e ancora valide: una texture per il 3D e' pensata per essere *illuminata* (media 63/255, massimo 170, nessun bianco: cosi' com'e' coprirebbe il 75% di inchiostro), e la gamma applicata canale per canale amplifica la dominante calda trasformando la pietra grigia in arenaria dorata, quindi va rimappata la sola luminanza. Giudizio finale: comunque mediocre.

**Tile procedurale dipinta.** Tentativo di imitare l'hand-painted low-poly stile Warcraft. Giudizio dell'utente: "molto cheap e grafica 3d anni 90".

**La ragione di fondo, e il vincolo da cui ripartire.** L'hand-painted da videogioco dipinge l'illuminazione **seguendo la forma**: luce sugli spigoli, ombra nei sottosquadri, la cima trattata diversamente dalla base. Una tile ripetibile non sa dove si trova sul modello, quindi quello stile le è strutturalmente precluso — non è una questione di quanto bene si disegni la tile. Lo stesso limite si era già manifestato due volte: il muschio non poteva stare "più in basso", e l'ombreggiatura del riferimento pittorico si è rivelata essere a livello di oggetto e non di texture.

Ne segue che le due sole strade coerenti sono:
1. **texture unica per oggetto, dipinta a mano** (UV non sovrapposte), che è artigianato e non generazione;
2. **nessuna texture**, e il colore lo mette l'acquirente sulla carta.

**Come applicarla:** prima di ritentare la generazione di una texture, chiarire quale delle due strade si sta imboccando. Se la risposta è "una tile che sembri hand-painted", la risposta è no: è il tentativo già fallito. L'occlusione ambientale su questo modello, tra l'altro, dà pochissimo, perché il guscio ha spessore zero e le pareti esterne sono convesse quindi non occluse.

Vedi [[project-panoramica]] e [[reference-vincoli-papercraft]].
