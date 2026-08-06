---
name: reference-gitignore-obj
description: Il .gitignore di questo repo viene dal template Visual Studio e ignora *.obj, che qui sono modelli e non file compilati
metadata:
  type: reference
---

Il `.gitignore` di questo repository e' il template "Visual Studio" generato da GitHub alla creazione, unito alle regole Blender/Windows locali. Alla riga ~103 contiene `*.obj`, che in un progetto C/C++ esclude l'output del compilatore.

In questo progetto `.obj` e' invece il formato Wavefront verso Pepakura, cioe' il deliverable. Senza eccezione i file esportati vengono esclusi **silenziosamente**: `git add -A` sembra funzionare, il commit va a buon fine, e i file semplicemente non ci sono. E' successo davvero il 2026-08-05.

L'eccezione `!export/*.obj` in fondo al `.gitignore` risolve, perche' le regole successive vincono su quelle precedenti.

**Come applicarla:** dopo aver committato artefatti di export, verificare che siano davvero tracciati con `git ls-files export` invece di fidarsi dell'esito del commit. Se in futuro si aggiungono altri formati (`*.stl`, texture) controllare prima con `git check-ignore -v <file>` se il template li esclude: contiene centinaia di regole pensate per un progetto .NET, non per un progetto 3D.

**Confine deciso per `export/`: si versiona tutto.** Gli `.obj` sono la fonte verso Pepakura. Gli artefatti prodotti *da* Pepakura (`.pdf` del pattern, `.pdo` di progetto, `.png` dello screenshot di layout) erano stati esclusi come "rigenerabili dagli .obj", poi reintegrati: non lo sono davvero, perche' con la versione gratuita di Pepakura il `.pdo` non e' salvabile e rifare l'impaginazione costa ~15 minuti di lavoro manuale. Un artefatto e' disponibile solo se rigenerarlo e' a costo trascurabile; qui non lo era. Vedi [[reference-pepakura-free]].

Vedi [[project-panoramica]].
