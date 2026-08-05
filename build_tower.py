"""Generatore della torre dadi papercraft.

Rigenera l'intero modello da zero in modo riproducibile. Eseguire dentro Blender:

    exec(open(r"E:\\repos\\PaperDiceTower\\build_tower.py").read())

Vincolo di progetto: geometria completamente faceted (solo facce piatte, spigoli
netti). Ogni faccia deve essere planare, altrimenti il pezzo stampato non si
piega combaciando in Pepakura. Le funzioni di controllo in fondo verificano
manifold-ness e planarita'.
"""

import bpy
import bmesh
import math
from mathutils import Vector

# --- Parametri ------------------------------------------------------------

SIDES = 9

PLINTH_R = 1.10
PLINTH_H = 0.45
# Sporgenze irregolari del plinto: base "rocciosa" semplificata a facce piatte.
PLINTH_JAG = [0.08, 0.22, 0.05, 0.18, 0.28, 0.10, 0.15, 0.24, 0.06]

SHAFT_R = 0.80
SHAFT_H = 3.2

# (altezza, raggio finale) dal fusto verso l'alto. Un raggio uguale al
# precedente produce un tratto cilindrico (tamburo) che rompe la silhouette:
# senza questi la torre sembra un proiettile invece che una torre.
RINGS = [
    (0.25, 0.72),   # strozzatura del collo
    (0.18, 0.72),   # tamburo del collo
    (0.30, 0.92),   # riapertura verso il corpo principale
    (1.50, 0.92),   # corpo principale / tamburo delle finestre
    (0.30, 0.55),   # rastremazione verso il parapetto
    (0.10, 0.63),   # mensola del parapetto
    (0.22, 0.63),   # parapetto (i merli poggiano qui)
]

# Rampa di uscita: cuneo inclinato verso il varco, perche' su un pavimento
# piatto un dado puo' fermarsi dentro la torre. E' un oggetto separato ("Rampa")
# perche' nel papercraft e' un pezzo a se' che si incolla dentro il guscio:
# tagliare il pavimento del guscio con un piano inclinato produrrebbe facce
# svergolate (non planari) sul plinto, che ha raggi irregolari.
# Coordinate locali: +Y verso il fondo della torre, -Y verso la vaschetta.
# La larghezza al fondo e' limitata dalla corda disponibile a quella profondita'
# dentro l'ennagono, non dal diametro: verificato da check_ramp_fits().
RAMP = dict(
    front_y=-1.00,      # bordo basso, a filo del varco
    front_half_w=0.45,
    back_y=0.58,        # bordo alto, contro la parete di fondo
    back_half_w=0.38,
    height=0.48,        # dislivello: pendenza ~17 gradi
)

# Le finestre sono fori passanti, non tasche incassate. Una tasca incassata
# significherebbe 9 pezzi da ritagliare e incollare per finestra (8 pareti da
# ~3 mm piu' il fondo, alla scala di stampa prevista): inassemblabile a mano.
# Col foro passante Pepakura ritaglia solo la sagoma e dietro si incolla un
# foglio di carta velina colorata come "vetro" (1 pezzo piatto per finestra).
# Il foro e' larghezza ~8 mm su stampa da 20 cm: i dadi (15-20 mm) non escono.
WINDOW = dict(
    half_w=0.135,
    v_bottom=-0.46,
    v_spring=0.00,
    v_apex=0.50,
    shoulder_frac=0.74,
    shoulder_h=0.45,
)

# --- Utilita' bmesh -------------------------------------------------------


def extrude_and_move(bm, faces, vec):
    """Estrude *faces* e sposta la nuova geometria di *vec*.

    `bmesh.ops.extrude_face_region` NON elimina la faccia di partenza: resta
    sepolta nella mesh e rende lo spigolo di confine non-manifold (3 facce).
    Va cancellata a mano, e con lei gli spigoli "wire" che possono restare
    orfani quando si estrudono piu' facce adiacenti.
    """
    ret = bmesh.ops.extrude_face_region(bm, geom=list(faces))
    new_verts = [g for g in ret["geom"] if isinstance(g, bmesh.types.BMVert)]
    new_faces = [g for g in ret["geom"] if isinstance(g, bmesh.types.BMFace)]
    bmesh.ops.translate(bm, verts=new_verts, vec=vec)
    bmesh.ops.delete(bm, geom=list(faces), context="FACES_ONLY")
    wire = [e for e in bm.edges if len(e.link_faces) == 0]
    if wire:
        bmesh.ops.delete(bm, geom=wire, context="EDGES")
    new_vert_set = set(new_verts)
    cap = next(
        (f for f in new_faces if f.is_valid and all(v in new_vert_set for v in f.verts)),
        None,
    )
    return new_verts, new_faces, cap


def face_at_z_span(bm, z_lo, z_hi, angle_deg=None, tol=1e-2):
    """Trova la faccia quadrangolare che copre esattamente lo z-span dato."""
    best = None
    for f in bm.faces:
        if len(f.verts) != 4:
            continue
        zs = sorted(v.co.z for v in f.verts)
        if abs(zs[0] - z_lo) > tol or abs(zs[-1] - z_hi) > tol:
            continue
        if angle_deg is None:
            return f
        c = f.calc_center_median()
        if abs(math.degrees(math.atan2(c.y, c.x)) - angle_deg) < 1.0:
            best = f
    return best


def planarity(face):
    n = face.normal
    c = face.calc_center_median()
    return max(abs((v.co - c).dot(n)) for v in face.verts)


def triangulate_twisted(bm, tol=1e-4):
    """Triangola le facce svergolate: un triangolo e' planare per definizione."""
    twisted = [f for f in bm.faces if len(f.verts) > 3 and planarity(f) > tol]
    if twisted:
        bmesh.ops.triangulate(bm, faces=twisted)
    return len(twisted)


# --- Elementi del modello -------------------------------------------------


def carve_gothic_window(bm, face, half_w, v_bottom, v_spring, v_apex,
                        shoulder_frac, shoulder_h):
    """Apre una finestra ad arco a punta (faceted) in una faccia quadrangolare planare.

    Il contorno ha 8 vertici: base rettangolare piu' arco a punta in 4 segmenti.
    L'anello intorno usa 4 pentagoni ancorati SOLO ai 4 angoli della faccia:
    aggiungere vertici sugli spigoli condivisi creerebbe T-junction non-manifold.

    Il risultato e' un foro passante: il contorno resta come spigoli di bordo
    (boundary), che e' esattamente cio' che serve perche' Pepakura ritagli la
    sagoma. Vedi la nota su WINDOW per il perche' non sia una tasca incassata.
    """
    verts_loop = list(face.verts)
    if len(verts_loop) != 4:
        raise ValueError("carve_gothic_window richiede una faccia quadrangolare")

    center = face.calc_center_median()
    normal = face.normal.copy().normalized()
    up = Vector((0, 0, 1))
    right = normal.cross(up).normalized()

    def corner_key(v):
        d = v.co - center
        return (d.dot(right) > 0, d.dot(up) > 0)

    corner = {corner_key(v): v for v in verts_loop}
    BL, BR = corner[(False, False)], corner[(True, False)]
    TR, TL = corner[(True, True)], corner[(False, True)]

    def P(u, v):
        return center + right * u + up * v

    v_should = v_spring + (v_apex - v_spring) * shoulder_h
    u_should = half_w * shoulder_frac
    outline = [
        (-half_w, v_bottom),
        (0.0, v_bottom),
        (half_w, v_bottom),
        (half_w, v_spring),
        (u_should, v_should),
        (0.0, v_apex),
        (-u_should, v_should),
        (-half_w, v_spring),
    ]
    W = [bm.verts.new(P(u, v)) for u, v in outline]

    bm.faces.new((BL, BR, W[2], W[1], W[0]))
    bm.faces.new((BR, TR, W[4], W[3], W[2]))
    bm.faces.new((TR, TL, W[6], W[5], W[4]))
    bm.faces.new((TL, BL, W[0], W[7], W[6]))

    bmesh.ops.delete(bm, geom=[face], context="FACES_ONLY")


def add_exit_ramp(face_angles=(-130.0, -90.0, -50.0), **overrides):
    """Crea l'oggetto 'Rampa': cuneo chiuso che inclina il pavimento verso l'uscita.

    Il piano superiore e' un trapezio i cui 4 vertici sono complanari perche' la
    quota dipende solo da y (z = a*y + b): allargando il fronte senza toccare la
    quota il piano resta planare, quindi il pezzo si piega combaciando.
    """
    p = dict(RAMP)
    p.update(overrides)

    fy, fw = p["front_y"], p["front_half_w"]
    by, bw = p["back_y"], p["back_half_w"]
    h = p["height"]

    verts_local = [
        (-fw, fy, 0.0),   # 0 L0  bordo basso
        (fw, fy, 0.0),    # 1 L1
        (bw, by, h),      # 2 H1  bordo alto
        (-bw, by, h),     # 3 H0
        (-bw, by, 0.0),   # 4 D0  sotto il bordo alto
        (bw, by, 0.0),    # 5 D1
    ]
    faces = [
        (0, 1, 2, 3),     # piano inclinato
        (3, 2, 5, 4),     # parete di fondo
        (0, 4, 5, 1),     # fondo appoggiato al pavimento
        (0, 3, 4),        # fianco sinistro
        (1, 5, 2),        # fianco destro
    ]

    mesh = bpy.data.meshes.new("Rampa_mesh")
    mesh.from_pydata([Vector(v) for v in verts_local], [], faces)
    mesh.update()
    obj = bpy.data.objects.new("Rampa", mesh)
    bpy.context.collection.objects.link(obj)

    # Le coordinate locali assumono la vaschetta verso -Y: ruota se e' altrove.
    sector_center = sum(face_angles) / len(face_angles)
    obj.rotation_euler.z = math.radians(sector_center + 90.0)

    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.normal_update()
    bm.to_mesh(mesh)
    mesh.update()
    bm.free()
    return obj


def add_dice_tray(obj, marks, face_angles=(-130.0, -90.0, -50.0),
                  depth=1.05, opening_top=0.95, tol=1e-3):
    """Apre il varco di uscita dei dadi e vi salda la vaschetta a livello del suolo.

    Il varco attraversa sia i pannelli del plinto sia la fascia bassa del fusto:
    il plinto da solo e' alto 0.45 (~1.4 cm alla scala di stampa) e un dado
    (15-20 mm) non ci passerebbe.

    Il pianale della vaschetta sta a z=0 come il pavimento interno della torre,
    cosi' i dadi rotolano fuori invece di restare dentro. Le pareti sono alte
    esattamente quanto il plinto: cosi' i fianchi risultano quadrilateri
    complanari (tutti i loro vertici stanno sullo stesso piano verticale
    radiale) e non facce svergolate.
    """
    shaft_lo, shaft_hi = marks["shaft_bottom"], marks["shaft_top"]
    wall_h = shaft_lo

    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.faces.ensure_lookup_table()
    bm.verts.ensure_lookup_table()

    def ang_of(co):
        return math.degrees(math.atan2(co.y, co.x))

    # Taglia TUTTO l'anello del fusto a opening_top: tagliare solo le facce del
    # settore lascerebbe vertici a meta' degli spigoli verticali condivisi.
    shaft_faces = [
        f for f in bm.faces
        if len(f.verts) == 4
        and abs(min(v.co.z for v in f.verts) - shaft_lo) < 1e-2
        and abs(max(v.co.z for v in f.verts) - shaft_hi) < 1e-2
    ]
    # bisect_plane rifiuta la stessa entita' due volte: spigoli e vertici sono
    # condivisi tra facce adiacenti, quindi la lista va deduplicata.
    geom = list(shaft_faces)
    geom += list({e for f in shaft_faces for e in f.edges})
    geom += list({v for f in shaft_faces for v in f.verts})
    bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, 0, opening_top), plane_no=(0, 0, 1))
    bm.faces.ensure_lookup_table()
    bm.verts.ensure_lookup_table()

    a_lo, a_hi = min(face_angles) - 20.5, max(face_angles) + 20.5
    doomed = []
    for f in bm.faces:
        a = ang_of(f.calc_center_median())
        if not (a_lo <= a <= a_hi):
            continue
        z_lo = min(v.co.z for v in f.verts)
        z_hi = max(v.co.z for v in f.verts)
        is_plinth = z_hi <= shaft_lo + tol and z_lo >= -tol
        is_low_shaft = abs(z_lo - shaft_lo) < 1e-2 and abs(z_hi - opening_top) < 1e-2
        if is_plinth or is_low_shaft:
            doomed.append(f)
    bmesh.ops.delete(bm, geom=doomed, context="FACES")
    wire = [e for e in bm.edges if len(e.link_faces) == 0]
    if wire:
        bmesh.ops.delete(bm, geom=wire, context="EDGES")
    bm.verts.ensure_lookup_table()

    rim_angles = [a - 20.0 for a in face_angles] + [face_angles[-1] + 20.0]

    def vert_at(z, angle, radius=None):
        best, best_err = None, 1e9
        for v in bm.verts:
            if abs(v.co.z - z) > 1e-2:
                continue
            if radius is not None and abs(math.hypot(v.co.x, v.co.y) - radius) > 1e-2:
                continue
            err = abs((ang_of(v.co) - angle + 180) % 360 - 180)
            if err < best_err:
                best, best_err = v, err
        if best is None or best_err > 1.0:
            raise RuntimeError(f"vertice non trovato: z={z} angolo={angle}")
        return best

    B = [vert_at(0.0, a) for a in rim_angles]
    P = [vert_at(shaft_lo, rim_angles[0], radius=SHAFT_R),
         vert_at(shaft_lo, rim_angles[-1], radius=SHAFT_R)]

    O, T = [], []
    for v in B:
        radial = Vector((v.co.x, v.co.y, 0.0)).normalized()
        o = bm.verts.new(v.co + radial * depth)
        O.append(o)
        T.append(bm.verts.new(o.co + Vector((0, 0, wall_h))))

    for i in range(len(B) - 1):
        bm.faces.new((B[i], B[i + 1], O[i + 1], O[i]))          # pianale
        bm.faces.new((O[i], O[i + 1], T[i + 1], T[i]))          # parete esterna
    bm.faces.new((B[0], O[0], T[0], P[0]))                       # fianco sinistro
    bm.faces.new((B[-1], P[1], T[-1], O[-1]))                    # fianco destro

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.normal_update()
    bm.to_mesh(mesh)
    mesh.update()
    bm.free()
    return {"tray_sectors": len(B) - 1, "opening_top": opening_top, "tray_depth": depth}


def build_tower():
    """Costruisce l'oggetto 'Torre' e restituisce le quote chiave."""
    # Va rimosso tutto cio' che lo script rigenera, altrimenti rieseguirlo
    # accumula duplicati (Rampa.001, Rampa.002, ...).
    for name in list(bpy.data.objects.keys()):
        if name in ("Torre", "Rampa") or name.startswith(("Merlone_", "Muro_", "Rampa.")):
            bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)
    for m in list(bpy.data.meshes):
        if m.users == 0:
            bpy.data.meshes.remove(m)

    bpy.ops.mesh.primitive_cylinder_add(
        vertices=SIDES, radius=SHAFT_R, depth=SHAFT_H,
        location=(0, 0, SHAFT_H / 2), end_fill_type="NGON",
    )
    obj = bpy.context.active_object
    obj.name = "Torre"
    obj.data.name = "Torre_mesh"
    bpy.context.scene.cursor.location = (0.0, 0.0, 0.0)
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR", center="MEDIAN")

    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.faces.ensure_lookup_table()
    bm.verts.ensure_lookup_table()

    # Plinto: svasatura verso il basso con raggi irregolari.
    min_z = min(v.co.z for v in bm.verts)
    bottom = next(f for f in bm.faces if all(abs(v.co.z - min_z) < 1e-6 for v in f.verts))
    _, _, plinth_cap = extrude_and_move(bm, [bottom], Vector((0, 0, -PLINTH_H)))
    cap_verts = sorted(plinth_cap.verts, key=lambda v: math.atan2(v.co.y, v.co.x))
    for v, extra in zip(cap_verts, PLINTH_JAG):
        ang = math.atan2(v.co.y, v.co.x)
        r = PLINTH_R + extra
        v.co.x, v.co.y = r * math.cos(ang), r * math.sin(ang)

    bmesh.ops.translate(bm, verts=list(bm.verts), vec=Vector((0, 0, PLINTH_H)))

    # Corpo: sequenza di rastremazioni e tamburi.
    max_z = max(v.co.z for v in bm.verts)
    cur_face = next(f for f in bm.faces if all(abs(v.co.z - max_z) < 1e-6 for v in f.verts))
    cur_r = SHAFT_R
    z = max_z
    marks = {"shaft_bottom": PLINTH_H, "shaft_top": max_z}
    for i, (h, r) in enumerate(RINGS):
        _, _, cap = extrude_and_move(bm, [cur_face], Vector((0, 0, h)))
        ratio = r / cur_r
        if abs(ratio - 1.0) > 1e-9:
            bmesh.ops.scale(bm, verts=list(cap.verts), vec=Vector((ratio, ratio, 1.0)))
        cur_face, cur_r = cap, r
        z += h
        marks[f"ring{i}_top"] = round(z, 4)

    marks["keep_bottom"] = marks["ring2_top"]
    marks["keep_top"] = marks["ring3_top"]
    marks["parapet_top"] = marks["ring6_top"]
    marks["keep_radius"] = RINGS[3][1]
    marks["parapet_radius"] = RINGS[6][1]

    triangulated = triangulate_twisted(bm)

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.normal_update()
    bm.to_mesh(mesh)
    mesh.update()
    bm.free()

    marks["triangulated_twisted_faces"] = triangulated
    return obj, marks


def add_keep_windows(obj, marks, angles=None, **overrides):
    """Incassa finestre ad arco sulle facce del corpo principale."""
    params = dict(WINDOW)
    params.update(overrides)

    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.faces.ensure_lookup_table()

    if angles is None:
        angles = []
        for f in bm.faces:
            if len(f.verts) != 4:
                continue
            zs = sorted(v.co.z for v in f.verts)
            if abs(zs[0] - marks["keep_bottom"]) < 1e-2 and abs(zs[-1] - marks["keep_top"]) < 1e-2:
                c = f.calc_center_median()
                angles.append(round(math.degrees(math.atan2(c.y, c.x)), 1))

    carved = 0
    for ang in angles:
        face = face_at_z_span(bm, marks["keep_bottom"], marks["keep_top"], angle_deg=ang)
        if face is None:
            continue
        carve_gothic_window(bm, face, **params)
        carved += 1
        bm.faces.ensure_lookup_table()

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.normal_update()
    bm.to_mesh(mesh)
    mesh.update()
    bm.free()
    return carved


# --- Verifica -------------------------------------------------------------


def check_mesh(obj):
    """Controlli che devono passare perche' l'unfold in Pepakura funzioni.

    `non_manifold_edges`, `loose_verts` e `non_planar_faces` devono essere 0.
    `boundary_edges` invece NON deve essere zero: conta i bordi delle aperture
    volute (fori delle finestre, cima aperta, varco della vaschetta). Va
    confrontato con `expected_boundary_edges` per accorgersi di buchi non voluti.
    """
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    report = {
        "verts": len(bm.verts),
        "edges": len(bm.edges),
        "faces": len(bm.faces),
        "non_manifold_edges": len([e for e in bm.edges if not e.is_manifold and not e.is_boundary]),
        "boundary_edges": len([e for e in bm.edges if e.is_boundary]),
        "loose_verts": len([v for v in bm.verts if len(v.link_faces) == 0]),
        "non_planar_faces": len([f for f in bm.faces if len(f.verts) > 3 and planarity(f) > 1e-4]),
    }
    bm.free()
    return report


def check_ramp_fits(ramp_obj, shell_obj, min_margin=0.04):
    """Verifica che la rampa non sbuchi dalle pareti del guscio.

    Non basta confrontare il raggio col raggio del guscio: la torre e' un
    ennagono, quindi le sue facce piatte passano piu' vicine all'asse del
    cerchio circoscritto (e il plinto ha pure raggi irregolari). Qui si spara
    un raggio dall'asse verso ciascun vertice della rampa e si misura dove
    incontra davvero la parete.
    """
    mw = ramp_obj.matrix_world
    rows, worst = [], None
    for v in ramp_obj.data.vertices:
        co = mw @ v.co
        radial = Vector((co.x, co.y, 0.0))
        r = radial.length
        if r < 1e-6:
            continue
        # Lo scostamento in z evita di rasare il pavimento a z=0.
        origin = Vector((0.0, 0.0, max(co.z, 1e-3)))
        hit, loc, _, _ = shell_obj.ray_cast(origin, radial.normalized())
        if not hit:
            rows.append({"co": [round(c, 3) for c in co], "wall": None, "margin": None})
            continue
        wall_r = (loc - origin).length
        margin = wall_r - r
        rows.append({
            "co": [round(c, 3) for c in co],
            "radius": round(r, 3),
            "wall": round(wall_r, 3),
            "margin": round(margin, 3),
        })
        if worst is None or margin < worst:
            worst = margin
    return {
        "verts": rows,
        "worst_margin": None if worst is None else round(worst, 3),
        "ok": worst is not None and worst >= min_margin,
        "min_margin_required": min_margin,
    }


def refresh_viewport():
    """Il viewport non si aggiorna da solo dopo modifiche via script."""
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            area.tag_redraw()
    bpy.context.view_layer.update()


if __name__ == "__main__":
    torre, MARKS = build_tower()
    N_WINDOWS = add_keep_windows(torre, MARKS)
    TRAY = add_dice_tray(torre, MARKS)
    RAMPA = add_exit_ramp()
    RAMP_REPORT = check_mesh(RAMPA)
    RAMP_FIT = check_ramp_fits(RAMPA, torre)
    REPORT = check_mesh(torre)
    # Bordi attesi, derivati dalla topologia delle aperture volute:
    #   8 per ogni finestra passante (il suo contorno);
    #   per la vaschetta con n settori: n bordi del suo lato aperto in alto,
    #   2 spigoli in cima ai fianchi, piu' il contorno del varco (2 verticali
    #   piu' n in alto) = 2n + 4.
    _n = TRAY["tray_sectors"]
    REPORT["expected_boundary_edges"] = N_WINDOWS * 8 + 2 * _n + 4
    refresh_viewport()
    print("marks:", MARKS)
    print("windows:", N_WINDOWS)
    print("tray:", TRAY)
    print("check torre:", REPORT)
    print("check rampa:", RAMP_REPORT)
    print("fit rampa:", RAMP_FIT["ok"], "margine minimo:", RAMP_FIT["worst_margin"])
