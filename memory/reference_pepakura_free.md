---
name: reference-pepakura-free
description: La versione gratuita di Pepakura non salva il .pdo — ogni reimport dell'OBJ azzera impostazioni e impaginazione
metadata:
  type: reference
---

Su questa postazione Pepakura Designer 6 e' in versione gratuita/non licenziata: `Save` e `Save As...` sono disattivati nel menu `File`, quindi **il `.pdo` non e' salvabile**. L'export in PDF funziona.

Conseguenza: ogni volta che si chiude il file e si reimporta `export/PaperDiceTower.obj`, vanno rifatte a mano tutte le impostazioni (formato A4 e margini, stampa vettoriale, Edge ID e altre opzioni di visualizzazione) **e tutta l'impaginazione**, che per ~13 pezzi su 2 pagine costa circa 15 minuti. La ricetta completa dei passaggi e' la sezione 6 di `checklist_export_pepakura.md`.

**Perche' conta per il modo di lavorare:** rigenerare il modello da `build_tower.py` ed esportare l'OBJ costa due minuti, quindi l'istinto e' di iterare a piccoli passi. Ma ogni iterazione che arriva fino alla stampa impone di rifare l'impaginazione da zero. Conviene quindi **accumulare piu' correzioni e applicarle in un colpo solo**, invece di una alla volta.

**Come applicarla:** dopo una sessione di lavoro in Pepakura, conservare il PDF esportato e uno screenshot del layout finale: ricostruire a occhio la posizione dei pezzi da un PDF e' piu' lento che copiarla da un'immagine. Se il progetto va in vendita, la licenza si ripaga subito, perche' ogni variante futura (taglie diverse, versioni a tema) ripaga da sola il costo in tempo.

Vedi [[project-panoramica]] e [[reference-vincoli-papercraft]].
