---
name: reference-decoro-registrato
description: Il decoro va disegnato sul cartamodello 2D, non sul modello 3D — e questo aggira il vincolo che ha ucciso il capitolo texture
metadata:
  type: reference
---

Il capitolo texture era finito contro un muro registrato in [[reference-texture-tentativi]]: **una tile ripetibile non sa dove si trova sul modello**, quindi non puo' disegnare l'archivolto attorno a *quella* finestra ne' il corso di pietre che si allinea attraverso *quella* piega. Lo stile hand-painted le era strutturalmente precluso.

**Il cartamodello 2D invece lo sa.** Ogni finestra, feritoia, merlo e piega ha coordinate precise sul foglio. Quindi il decoro non e' un problema di generazione di texture: e' disegno tecnico sul pattern. E' il riquadro che sblocca la questione, ed e' implementato in `tools/pattern.py`.

**La proprieta' che rende la cosa praticabile:** il decoro derivato *dalla feature* sta dentro il pezzo per costruzione, quindi **non ha bisogno di essere ritagliato sul contorno**. L'archivolto nasce dal contorno della finestra dilatato, quindi non puo' sbordare. Il decoro derivato dalla *superficie* (corsi di pietra su tutto il pannello) invece va ritagliato, e con linguette e merlature il ritaglio e' fragile.

**Cosa e' derivabile e cosa no.** Lo script sa generare cio' che la geometria conosce: conci, chiavi d'arco, soglie, cantonali sulle pieghe, marcapiani alle rastremazioni. Non sa inventare uno stile. La divisione del lavoro concordata: il committente disegna **un** pannello in Inkscape sopra `export/PaperDiceTower7_300_vettoriale.pdf`, lo script lo replica sugli altri sei con la rotazione giusta. La torre e' a simmetria 7, quindi il disegno unico e' un settimo del lavoro apparente.

**Quattro errori commessi implementandolo, tutti istruttivi:**

1. **Gli assi.** I corsi di pietra seguivano gli assi della *pagina*, ma nel layout la striscia e' ruotata di 90 gradi. Il decoro va registrato sugli assi del **modello**.
2. **Le pieghe non bastano a ricavarli.** In una striscia le pieghe fra pannello e pannello e quelle delle linguette hanno lunghezza totale quasi identica (489 contro 459 mm misurati sul foglio 1), quindi la direzione dominante e' ambigua. Funziona invece la **finestra**: 42 x 11,8 mm, fortemente anisotropa, la sua componente principale e' la verticale della torre qualunque rotazione abbia il pezzo.
3. **Il segno della PCA e' arbitrario**, quindi da solo non dice da che parte sta l'arco: soglia e chiave sono finite invertite. Il verso si ricava dalla forma — l'estremita' ad arco e' a punta, quella della base e' larga.
4. **La mitra esplode sugli spigoli acuti.** L'apice dell'arco a punta produceva una lisca lunga d/cos(mezzo angolo). Va smussata sotto una soglia di angolo.

**Vincolo dimensionale:** il decoro aggiunge ~4,5 mm per lato, quindi la finestra decorata occupa ~21 mm su un pannello di ~35 mm. Non ci sta un secondo livello di ornamento.

**Se si disegna a mano in post-produzione** (Inkscape sul `_vettoriale.pdf`, che e' una base migliore del PDF di Pepakura perche' non ha le 48 immagini raster dentro): il disegno e' **congelato su quel layout**, quindi geometria e impaginazione vanno congelate prima. Dove il decoro attraversa una piega deve continuare; l'unico punto delicato e' la cucitura che chiude il tubo, dove primo e ultimo pannello sono agli estremi opposti del foglio. Non disegnare sulle linguette (l'inchiostro indebolisce la presa della colla) e fermarsi ~0,3 mm prima dei tagli.

Vedi [[project-panoramica]] e [[reference-pepakura-free]].
