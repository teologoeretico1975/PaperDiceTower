---
name: reference-blender-mcp-addon
description: Dove trovare e come installare l'add-on Blender che serve al connettore MCP per collegarsi a questa Blender locale
metadata:
  type: reference
---

Il connettore "Blender" usato in questo progetto ha due metà: il server MCP lato Claude Code (già configurato) e un add-on da installare dentro Blender stesso, che apre un socket locale su `localhost:9876`. Senza l'add-on installato e abilitato in Blender, ogni tool `mcp__Blender__*` fallisce con `Cannot connect to Blender at localhost:9876`.

L'add-on è quello ufficiale di Blender Lab, non un progetto di terze parti: https://www.blender.org/lab/mcp-server/ (richiede Blender 5.1+). Si installa trascinando lo zip dentro la finestra di Blender (drag & drop) — la prima volta aggiunge il repository "Blender Lab", la seconda installa l'add-on vero e proprio.

**Perché:** cercare "mcp" tra gli add-on di Blender non basta a trovarlo — non è preinstallato né elencato finché non lo si scarica e trascina dentro Blender almeno una volta. Verificato funzionante il 2026-08-05.

**Come applicarla:** se in futuro (anche su un'altra macchina/collega) il connettore Blender smette di rispondere con lo stesso errore di connessione, il primo controllo è: Blender è aperto e l'add-on è installato/abilitato con il server avviato? Ripartire da https://www.blender.org/lab/mcp-server/ per il download.

Vedi [[project-panoramica]].
