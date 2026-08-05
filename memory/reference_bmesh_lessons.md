---
name: reference-bmesh-lessons
description: Insidie di bmesh.ops scoperte modellando Torre — extrude che lascia facce fantasma, wire edge orfani
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

**Perché:** entrambi i bug sono stati scoperti empiricamente durante la Fase 2 e Fase 3 (rastremazione ed estrusione della mensola), verificando dopo ogni operazione il conteggio di spigoli non-manifold — non erano documentati in modo ovvio nell'API reference bundle.

**Come applicarla:** qualunque estrusione futura su questo file (o su altri modelli con lo stesso connettore) dovrebbe usare il pattern `extrude_and_move` con cancellazione esplicita della faccia originale e ripulitura dei wire edge, non il solo `extrude_face_region` + `translate`.

Vedi [[project-panoramica]].
