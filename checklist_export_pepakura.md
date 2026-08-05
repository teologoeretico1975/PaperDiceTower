# Checklist pre-export Blender → Pepakura
## Necromancer Dice Tower — verifica finale prima dell'unfold

Da eseguire in Blender **dopo** aver completato tutte e 5 le fasi di modellazione
(base, rastremazione, sporgenza, merlature, feritoia), prima di esportare in OBJ.

---

### 1. Geometria non-manifold

- [ ] Vai in **Edit Mode** (Tab)
- [ ] `Select → All by Trait → Non Manifold`
- [ ] Se qualcosa viene selezionato: usa `Mesh → Clean Up → Merge by Distance`
      per unire vertici duplicati (causa più comune di non-manifold)
- [ ] Ripeti la selezione non-manifold finché il risultato è vuoto

**Perché conta:** Pepakura si basa su facce chiuse e collegate correttamente.
Vertici duplicati o buchi nella mesh producono un unfold rotto o pezzi mancanti.

---

### 2. Nessuna geometria curva/smooth residua

- [ ] Controlla che **nessun modifier Subdivision Surface** sia attivo
      (Modifier Properties, icona a chiave inglese)
- [ ] Se presente, applicalo (Apply) solo se lo shape finale ti convince,
      altrimenti rimuovilo — non lasciarlo "in sospeso"
- [ ] Verifica che non ci siano operazioni di sculpting residue
      (controlla in Sculpt Mode se la mesh ha dettagli ad alta densità
      non intenzionali)

**Perché conta:** superfici smooth generano centinaia di facce triangolari
minuscole — impossibili da tagliare/piegare a mano su carta.

---

### 3. Normali coerenti (facing outward)

- [ ] In Edit Mode: `Select All` (A) poi `Mesh → Normals → Recalculate Outside`
- [ ] Attiva temporaneamente **Face Orientation overlay** (Viewport Overlays)
      per controllo visivo: blu = normale corretta verso l'esterno,
      rosso = normale invertita

**Perché conta:** normali invertite causano facce "al contrario" nel pattern
di unfold, con texture/decorazioni specchiate o mancanti.

---

### 4. Conteggio pezzi/facce ragionevole

- [ ] Controlla il numero totale di facce (Statistics overlay o
      `Mesh Analysis`)
- [ ] Target indicativo per un dice tower papercraft: **30-60 facce totali**
      (oltre le 100 diventa difficile da assemblare per un teenager)
- [ ] Se il conteggio è molto più alto del previsto, probabilmente c'è
      ancora geometria non necessaria (es. facce interne nascoste, doppioni)

**Perché conta:** troppi pezzi piccoli rendono l'assemblaggio frustrante
invece che divertente — vanifica l'obiettivo "piacere della costruzione".

---

### 5. Facce interne nascoste da rimuovere

- [ ] Controlla che non ci siano facce doppie sovrapposte (es. interno
      cavo del cilindro base, se non necessario strutturalmente)
- [ ] `Select → All by Trait → Interior Faces` per individuarle
- [ ] Elimina quelle non necessarie al risultato finale piegato

**Perché conta:** Pepakura proverebbe a spacchettare anche facce che
l'utente finale non vedrà mai, sprecando spazio sul foglio A4 di stampa.

---

### 6. Scala reale dell'oggetto

- [ ] Verifica le dimensioni reali in Blender (N-panel → Item → Dimensions)
- [ ] Target indicativo: torre alta **15-20 cm** da assemblata
      (compatibile con un dice tower da tavolo funzionale)
- [ ] Se la scala è sballata, correggi PRIMA dell'export
      (`Object → Apply → Scale` dopo aver ridimensionato)

**Perché conta:** Pepakura scala in base alle unità del file — se sbagli
qui, tutti i pezzi stampati escono a una taglia diversa da quella voluta.

---

### 7. Export OBJ

- [ ] `File → Export → Wavefront (.obj)`
- [ ] Opzioni: **Forward = -Y**, **Up = Z** (orientamento standard per Pepakura)
- [ ] Includi **Normals** e **UV coordinates** se hai già applicato texture
- [ ] Nome file chiaro (es. `necromancer_tower_v1.obj`)

---

### 8. Prima apertura in Pepakura

- [ ] Importa l'OBJ in Pepakura Designer
- [ ] Se l'unfold produce **pezzi con forma molto allungata/sottile**
      (schegge strette), torna in Blender e correggi la geometria in
      quel punto specifico (probabilmente una faccia troppo stretta)
- [ ] Se l'unfold produce **troppi pezzi separati per una singola faccia
      grande**, valuta se unire alcune facce adiacenti in Blender prima
      di ri-esportare

---

## Nota generale

Questa checklist va eseguita **ogni volta** che modifichi il modello,
non solo alla primissima esportazione — è facile reintrodurre geometria
non-manifold con una singola estrusione mal fatta durante iterazioni
successive (es. quando aggiungerai varianti a tema Ashan).
