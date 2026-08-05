---
name: reference-memoria-su-disco
description: Le memorie di questo progetto devono essere salvate come file .md in questa cartella (memory/), non nella memoria locale di Claude su questa macchina
metadata:
  type: reference
---

Per questo progetto, tutte le memorie persistenti (decisioni, preferenze, contesto) vanno scritte come file .md in `memory/` dentro a questa working folder (E:\repos\PaperDiceTower), non nella memoria locale di Claude (`~/.claude/projects/.../memory/`).

**Perché:** direttiva organizzativa — quando si usa Claude Cowork con cartelle di lavoro su disco locale, le memorie devono stare su disco e finire nel repository git, così i colleghi che aprono la stessa cartella (o clonano il repo) hanno accesso allo stesso contesto. La memoria locale di Claude resta legata alla macchina di un singolo utente e non è condivisibile.

**Come applicarla:** qualunque sessione Claude futura che lavori in questa cartella dovrebbe leggere e aggiornare i file in `memory/` invece di (o oltre a) usare il proprio sistema di memoria automatica. Il file `MEMORY.md` in questa cartella funge da indice, con lo stesso formato (frontmatter name/description/metadata.type) del sistema di memoria automatica di Claude Code.
