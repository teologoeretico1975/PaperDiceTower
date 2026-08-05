---
name: project-panoramica
description: Cosa è il modello PaperDiceTower, vincoli di progetto e storia delle revisioni
metadata:
  type: project
---

Torre dadi fantasy low-poly modellata in Blender (oggetto "Torre" + oggetti "Merlone_01..07" separati), pensata per essere esportata e unfoldata con Pepakura in un prodotto papercraft venduto su Etsy (ispirata a torri dadi in legno reali).

**Vincolo tecnico fondamentale:** geometria completamente faceted — niente subdivision surface, sculpting o superfici curve smooth, altrimenti l'unfold in Pepakura non funziona. Ogni fase va verificata con un controllo di manifold-ness (0 spigoli non-manifold) prima di procedere.

**Struttura del modello** (aggiornata al 2026-08-05): base cilindrica a 9 lati; rastremazione "a stadi" (tronchi di cono alternati a tamburi cilindrici, non un cono continuo); vaschetta raccogli-dadi a livello del suolo con apertura nella parete + cima della torre aperta (i dadi entrano dall'alto e cadono dritti nella vaschetta, senza deflettori interni); parapetto (fascia cilindrica) sotto 7 merli a tronco di piramide con un paio di vuoti; feritoia decorativa incassata (non passante) su una faccia della base.

**Perché:** la prima versione completa è stata giudicata "brutta e non vendibile su Etsy". Problemi identificati dall'utente: (1) la rastremazione continua dava una silhouette da proiettile invece che da torre; (2) i merli (cubi ruotati a caso, attaccati direttamente al cono) sembravano detriti casuali, non merlature; (3) la vaschetta era una scatola squadrata senza rifiniture.

**Come applicarla:** se si modifica ulteriormente la torre, mantenere questi principi già corretti: la rastremazione deve avere tratti piatti (tamburi) tra un restringimento e l'altro, non una curva continua; oggetti ripetuti attorno a un asse (come i merli) vanno ruotati tangenzialmente alla curvatura, non lasciati con orientamento fisso nello spazio mondo; elementi funzionali come la vaschetta beneficiano di svasature/rastremazioni invece di forme a scatola pura.

Vedi [[reference-memoria-su-disco]] e [[reference-bmesh-lessons]].
