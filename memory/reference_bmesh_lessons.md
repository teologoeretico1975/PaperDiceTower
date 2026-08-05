---
name: reference-bmesh-lessons
description: Insidie di bmesh.ops scoperte modellando Torre — extrude con facce fantasma, wire edge orfani, liste duplicate, bisect parziale
metadata:
  type: reference
---

Lavorando su questo file via `execute_blender_code` con l'API `bmesh.ops`, sono emersi due comportamenti non ovvi che hanno causato geometria non-manifold nelle prime fasi:

**1. `bmesh.ops.extrude_face_region(bm, geom=[face])` non elimina la faccia originale.** La faccia passata in input resta al suo posto come faccia "fantasma" dopo l'estrusione, mentre la nuova geometria (spostata) viene creata separatamente. Il risultato: lo spigolo di confine finisce condiviso da 3 facce invece di 2 (non-manifold). Va sempre cancellata esplicitamente dopo l'estrusione:

```python
ret = bmesh.ops.extrude_face_region(bm, geom=[face])
new_verts = [g for g in ret['geom'] if isinstance(g, bmesh.types.BMVert)]
bmesh.ops.translate(bm, verts=new_verts, vec=offset)
bmesh.ops.delete(bm, geom=[face], context='FACES_ONLY')  # <- necessario
```

**2. Cancellare più facce con `context='FACES_ONLY'` può lasciare spigoli "wire" orfani.** Se due facce cancellate insieme condividevano uno spigolo interno (usato solo da loro due), quello spigolo resta con 0 facce collegate — non è né manifold né boundary, va ripulito a parte:

```python
wire = [e for e in bm.edges if len(e.link_faces) == 0]
if wire:
    bmesh.ops.delete(bm, geom=wire, context='EDGES')
```

**3. `bmesh.ops` rifiuta liste in cui la stessa entità compare due volte.** Costruendo il `geom` da passare a `bisect_plane` partendo da più facce, spigoli e vertici condivisi finiscono duplicati e l'operatore solleva `ValueError: found the same (BMVert/BMEdge/BMFace) used multiple times`. Va deduplicato con un set:

```python
geom = list(faces)
geom += list({e for f in faces for e in f.edges})
geom += list({v for f in faces for v in f.verts})
```

**4. Tagliare solo un settore di un anello lascia T-junction.** Se si bisect solo alcune facce di un anello chiuso, gli spigoli verticali condivisi coi vicini vengono spezzati e i vicini restano con un vertice a metà spigolo (non-manifold). Conviene tagliare l'anello intero e poi cancellare solo le facce del settore che interessa.

**5. Uno script rigeneratore deve cancellare tutto ciò che crea.** Aggiungendo un oggetto nuovo (es. `Rampa`) senza inserirlo nella lista di pulizia iniziale, ogni riesecuzione ne accumula una copia (`Rampa.001`, `Rampa.002`, ...) sovrapposta e invisibile. Controllare la lista degli oggetti della scena dopo un doppio run è il modo più rapido per accorgersene.

**Perché:** entrambi i bug sono stati scoperti empiricamente durante la Fase 2 e Fase 3 (rastremazione ed estrusione della mensola), verificando dopo ogni operazione il conteggio di spigoli non-manifold — non erano documentati in modo ovvio nell'API reference bundle.

**Come applicarla:** qualunque estrusione futura su questo file (o su altri modelli con lo stesso connettore) dovrebbe usare il pattern `extrude_and_move` con cancellazione esplicita della faccia originale e ripulitura dei wire edge, non il solo `extrude_face_region` + `translate`.

Vedi [[project-panoramica]].
