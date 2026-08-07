---
name: reference-decoro-registrato
description: Il decoro va disegnato sul cartamodello 2D, non sul modello 3D — e questo aggira il vincolo che ha ucciso il capitolo texture
metadata:
  type: reference
---

Il capitolo texture era finito contro un muro registrato in [[reference-texture-tentativi]]: **una tile ripetibile non sa dove si trova sul modello**, quindi non puo' disegnare l'archivolto attorno a *quella* finestra ne' il corso di pietre che si allinea attraverso *quella* piega. Lo stile hand-painted le era strutturalmente precluso.

**Il cartamodello 2D invece lo sa.** Ogni finestra, feritoia, merlo e piega ha coordinate precise sul foglio. Quindi il decoro non e' un problema di generazione di texture: e' disegno sul pattern. E' il riquadro che sblocca la questione.

**La proprieta' che rende la cosa praticabile:** il decoro derivato *dalla feature* sta dentro il pezzo per costruzione, quindi **non ha bisogno di essere ritagliato sul contorno**. L'archivolto nasce dal contorno della finestra dilatato, quindi non puo' sbordare. Il decoro derivato dalla *superficie* (corsi di pietra su tutto il pannello) invece va ritagliato, e con linguette e merlature il ritaglio e' fragile.

**Decisione del 2026-08-07: il decoro si fa a MANO in post-produzione**, non generato. Il principio resta quello sopra — si disegna sul pattern 2D — ma l'implementazione e' Inkscape sopra il PDF di Pepakura, col pattern su un layer bloccato.

Perche' non generarlo, pur avendo un prototipo funzionante: lo stile non e' derivabile dalla geometria (lo script sa fare conci, soglie, cantonali, marcapiani, non sa inventare un carattere), e un PDF derivato va tenuto in sincrono a **ogni** re-impaginazione. Il codice di generazione e' stato rimosso da `tools/pattern.py`, che resta il validatore del cartamodello; e' recuperabile dal commit `f878218`.

**La simmetria fa la differenza:** a 7 lati con finestre e feritoie identiche, i motivi unici da disegnare sono cinque o sei, non tredici pezzi. Il disegno unico e' circa un settimo del lavoro apparente. Resta disponibile, se servisse, replicare a script un pannello disegnato a mano sugli altri sei con la rotazione corretta.

**Quattro errori commessi implementandolo, tutti istruttivi:**

1. **Gli assi.** I corsi di pietra seguivano gli assi della *pagina*, ma nel layout la striscia e' ruotata di 90 gradi. Il decoro va registrato sugli assi del **modello**.
2. **Le pieghe non bastano a ricavarli.** In una striscia le pieghe fra pannello e pannello e quelle delle linguette hanno lunghezza totale quasi identica (489 contro 459 mm misurati sul foglio 1), quindi la direzione dominante e' ambigua. Funziona invece la **finestra**: 42 x 11,8 mm, fortemente anisotropa, la sua componente principale e' la verticale della torre qualunque rotazione abbia il pezzo.
3. **Il segno della PCA e' arbitrario**, quindi da solo non dice da che parte sta l'arco: soglia e chiave sono finite invertite. Il verso si ricava dalla forma — l'estremita' ad arco e' a punta, quella della base e' larga.
4. **La mitra esplode sugli spigoli acuti.** L'apice dell'arco a punta produceva una lisca lunga d/cos(mezzo angolo). Va smussata sotto una soglia di angolo.

**Vincolo dimensionale:** il decoro aggiunge ~4,5 mm per lato, quindi la finestra decorata occupa ~21 mm su un pannello di ~35 mm. Non ci sta un secondo livello di ornamento.

**Vincoli del disegno a mano.** Nota pratica: il PDF di Pepakura contiene 48 tessere raster di sfondo bianco, che in Inkscape arrivano come 48 immagini da cancellare a mano prima di iniziare. Poi: il disegno e' **congelato su quel layout**, quindi geometria e impaginazione vanno congelate prima. Dove il decoro attraversa una piega deve continuare; l'unico punto delicato e' la cucitura che chiude il tubo, dove primo e ultimo pannello sono agli estremi opposti del foglio. Non disegnare sulle linguette (l'inchiostro indebolisce la presa della colla) e fermarsi ~0,3 mm prima dei tagli.

Vedi [[project-panoramica]] e [[reference-pepakura-free]].
