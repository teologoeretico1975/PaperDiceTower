---
name: reference-pepakura-free
description: La versione gratuita di Pepakura non salva il .pdo — ogni reimport dell'OBJ azzera impostazioni e impaginazione
metadata:
  type: reference
---

Su questa postazione Pepakura Designer 6 e' in versione gratuita/non licenziata: `Save` e `Save As...` sono disattivati nel menu `File`, quindi **il `.pdo` non e' salvabile**. L'export in PDF funziona.

**Cosa e' bloccato e cosa no, verificato aprendo i menu il 2026-08-07:**

| voce | stato |
|---|---|
| `File → Print to PDF...` (Ctrl+Shift+P) | **funziona** — e' da qui che viene il pattern |
| `File → Export → Pattern: Single File` (dxf, svg, eps, emf, png...) | bloccato dalla licenza |
| `File → Export → Pattern: Per Sheet` (dxf, svg, pdf, png...) | bloccato dalla licenza |
| `File → Export → Read-only (pdo)` | bloccato dalla licenza |
| `File → Export → 3D Model & Image for Texture Editing (obj, bmp)` | bloccato: "A license code is required to export BMP images for editing textures" |

**Quindi la licenza non serve per la prova di stampa**, che e' il passo aperto: il PDF si esporta col gratuito. Servirebbe per l'export vettoriale verso i plotter da taglio (con una palette chiara di cartoncino non e' necessario, vedi [[reference-etsy-posizionamento]]) e per salvare il `.pdo`.

**Trappola su `3D Model & Image for Texture Editing`:** il suo dialogo avvisa che *azzererebbe tutte le coordinate UV* e che l'immagine si reimporta da `Settings → Texture`. Quindi cancellerebbe le UV provenienti da Blender. Le due strade per texturizzare sono alternative, e quella bloccata dalla licenza e' anche quella che toglierebbe il controllo: l'import da `Settings → Texture` invece funziona col gratuito ed e' gia' stato verificato.

Conseguenza: ogni volta che si chiude il file e si reimporta `export/PaperDiceTower.obj`, vanno rifatte a mano tutte le impostazioni (formato A4 e margini, stampa vettoriale, Edge ID e altre opzioni di visualizzazione) **e tutta l'impaginazione**, che per ~13 pezzi su 2 pagine costa circa 15 minuti. La ricetta completa dei passaggi e' la sezione 6 di `checklist_export_pepakura.md`.

**Perche' conta per il modo di lavorare:** rigenerare il modello da `build_tower.py` ed esportare l'OBJ costa due minuti, quindi l'istinto e' di iterare a piccoli passi. Ma ogni iterazione che arriva fino alla stampa impone di rifare l'impaginazione da zero. Conviene quindi **accumulare piu' correzioni e applicarle in un colpo solo**, invece di una alla volta.

**Come applicarla:** dopo una sessione di lavoro in Pepakura, conservare il PDF esportato e uno screenshot del layout finale: ricostruire a occhio la posizione dei pezzi da un PDF e' piu' lento che copiarla da un'immagine. Se il progetto va in vendita, la licenza si ripaga subito, perche' ogni variante futura (taglie diverse, versioni a tema) ripaga da sola il costo in tempo.

Vedi [[project-panoramica]] e [[reference-vincoli-papercraft]].
