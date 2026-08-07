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

# Versione di riferimento: 7 lati, stampata alta 300 mm (vedi REFERENCE_HEIGHT_MM).
# La variante a 9 lati resta riproducibile con `build_all(sides=9)` ed e' quella
# di `PaperDiceTower.blend`. Si e' scelto 7 perche' allarga i pannelli da 16,0 a
# 20,2 mm, e i 300 mm perche' sono l'unica leva che allarga anche i dettagli
# piccoli in valore assoluto: le feritoie passano da 2,6 a 3,9 mm.
SIDES = 7
REFERENCE_HEIGHT_MM = 300.0

PLINTH_R = 1.10
PLINTH_H = 0.45
# Sporgenze irregolari del plinto: base "rocciosa" semplificata a facce piatte.
# Con un numero di lati diverso da 9 se ne prendono i primi *sides* valori
# (vedi plinth_jag): la sequenza e' fissa perche' il modello resti riproducibile.
PLINTH_JAG = [0.08, 0.22, 0.05, 0.18, 0.28, 0.10, 0.15, 0.24, 0.06]


# --- Geometria derivata dal numero di lati ---------------------------------
#
# Tutto quello che dipende da quante facce ha la torre si ricava qui, invece di
# essere scritto a mano: cambiare `sides` altrimenti spaccherebbe gli angoli
# delle feritoie, il settore della vaschetta e le liste per-faccia.


# Deflettori interni: piastre piane che intercettano il dado in caduta.
#
# Senza, il dado fa 263 mm di caduta libera in un tubo largo 63 mm alla scala di
# riferimento: non tocca nulla e arriva giu' con la faccia con cui e' entrato,
# quindi la torre non randomizza niente.
#
# Sono un oggetto separato ("Deflettori") e non lembi incernierati al guscio:
# una partizione interna di un tubo rende non-manifold lo spigolo dove si
# attacca (3 facce su un solo spigolo), e questo vale per qualunque soluzione
# integrata nella stessa mesh.
#
# Perche' piastre piane e non una scala a chiocciola: un elicoide non e' una
# superficie sviluppabile, cioe' non si appiattisce su un foglio senza stirare
# la carta, quindi andrebbe approssimato con molte faccette con relative
# linguette. E funzionalmente il dado ci scivolerebbe sopra in modo continuo,
# mentre per randomizzare serve che rimbalzi cambiando faccia.
# Ogni deflettore e' una STRISCIA CORRUGATA che va da parete a parete, non una
# piastra piana a sbalzo. Due motivi:
#
# 1. Rigidezza. Una piastra incollata su un solo lato e protesa 39 mm nel vuoto
#    flette e finisce per piegarsi sulla linea di colla, perche' la rigidezza a
#    flessione cresce col cubo dell'altezza della sezione e in un foglio piatto
#    quell'altezza e' lo spessore della carta. La corrugazione porta l'altezza
#    utile da 0,25 a ~5 mm, quindi non serve cartoncino. Andando da parete a
#    parete la striscia e' inoltre appoggiata a entrambi gli estremi.
# 2. Le creste fanno rimbalzare il dado in modo piu' caotico di una superficie
#    liscia, che e' lo scopo dell'oggetto.
#
# Vincolo che decide se funziona: le pieghe devono correre LUNGO la luce. Piegate
# in senso trasversale si otterrebbe un soffietto, cioe' una molla, piu' cedevole
# di un foglio piatto.
#
# La larghezza in pianta non puo' superare la corda di una faccia, altrimenti gli
# estremi della striscia sporgerebbero oltre gli spigoli e bucherebbero la parete.
# Servono QUATTRO strisce, e il numero viene da due criteri opposti misurati, non
# da una stima:
#  - insieme devono coprire tutta la sezione in pianta, altrimenti resta una
#    traiettoria verticale libera e il dado cade senza toccare nulla (con due
#    strisce restava un canale di 25 mm, contro i 15 mm del dado piu' piccolo);
#  - ogni striscia da sola deve invece lasciare un varco piu' largo del dado piu'
#    GRANDE, altrimenti il dado si incastra al posto di scendere (ne lascia 24 mm,
#    contro i 20 di un d20).
# Vedi check_baffle_coverage() e check_baffle_passage().
BAFFLE = dict(
    count=4,             # numero di strisce
    plan_width=0.66,     # larghezza proiettata: <= corda di una faccia (0.694)
    panels=4,            # numero di falde della corrugazione
    amplitude=0.10,      # ampiezza cresta-valle (~4,4 mm alla scala di stampa)
    tilt_deg=10.0,       # inclinazione laterale, per far rotolare via il dado
)


def norm_angle(a):
    """Riporta un angolo in gradi nell'intervallo (-180, 180]."""
    return (a + 180.0) % 360.0 - 180.0


def face_center_angles(sides):
    """Angoli dei centri delle facce laterali, in ordine crescente.

    `primitive_cylinder_add` mette i vertici a `90 + k*360/sides`, quindi i
    centri delle facce cadono a meta' strada. Verificato contro la torre a 9
    lati: i centri risultano a -170, -130, -90, ... come da formula.
    """
    return sorted(norm_angle(90.0 + (k + 0.5) * 360.0 / sides) for k in range(sides))


def vertex_angles(sides):
    """Angoli degli spigoli verticali, in ordine crescente."""
    return sorted(norm_angle(90.0 + k * 360.0 / sides) for k in range(sides))


def plinth_jag(sides):
    return [PLINTH_JAG[k % len(PLINTH_JAG)] for k in range(sides)]


def tray_face_angles(sides, sectors=None):
    """Facce contigue occupate dal varco e dalla vaschetta.

    Con `sides` dispari esiste sempre una faccia centrata a -90, quindi un
    settore simmetrico puo' avere solo un numero dispari di facce. Con 7 lati
    3 facce sarebbero il 43% del perimetro (plinto troppo indebolito) e 1 sola
    darebbe una vaschetta troppo piccola: si accetta un settore di 2 facce,
    non centrato esattamente a -90. Sposta il "davanti" del modello di mezza
    faccia, senza altre conseguenze.
    """
    if sectors is None:
        sectors = max(1, round(sides / 3))
    centers = face_center_angles(sides)
    # Si parte dalla faccia piu' vicina a -90 e si centra il settore su di essa;
    # con un numero pari di facce resta sbilanciato di mezza faccia in avanti.
    pivot = min(range(sides), key=lambda i: abs(norm_angle(centers[i] + 90.0)))
    start = pivot - (sectors - 1) // 2
    angles = [centers[(start + j) % sides] for j in range(sectors)]
    if angles != sorted(angles):
        raise NotImplementedError(
            "il settore della vaschetta attraversa +/-180 gradi: la selezione "
            "delle facce per angolo a valle assume un intervallo continuo")
    return angles


def half_face_angle(sides):
    """Mezza apertura angolare di una faccia, in gradi."""
    return 180.0 / sides


def slit_specs(sides):
    """Feritoie: una per faccia, con quota alternata tra faccia e faccia.

    Alternare le quote evita di rimuovere carta tutta alla stessa altezza, che
    indebolirebbe il tubo del fusto su un unico anello.
    """
    specs = []
    for k, angle in enumerate(face_center_angles(sides)):
        if k % 2 == 0:
            specs.append((angle, -0.55, 0.40))
        else:
            specs.append((angle, 0.35, 0.35))
    return specs


def slit_bands(sides, opening_top=0.95):
    """Per ogni faccia, l'intervallo di quote occupato dalla sua feritoia."""
    face_mid = (opening_top + PLINTH_H + SHAFT_H) / 2.0
    return {round(a, 2): (face_mid + v - h, face_mid + v + h)
            for a, v, h in slit_specs(sides)}


def baffle_specs(sides, opening_top=0.95, **overrides):
    """Coppie di facce e quote per le strisce corrugate.

    Vincoli risolti qui:
    - ogni striscia va da una faccia a quella piu' vicina all'opposto, cosi' e'
      appoggiata a entrambi gli estremi;
    - le due strisce devono avere assi il piu' possibile perpendicolari, perche'
      i varchi laterali di una siano coperti dall'altra;
    - la quota deve stare fuori dalle bande delle feritoie di **entrambe** le
      facce a cui la striscia si incolla, altrimenti la linguetta le coprirebbe.
    """
    p = dict(BAFFLE)
    p.update(overrides)

    shaft_hi = PLINTH_H + SHAFT_H
    bands = slit_bands(sides, opening_top)
    centers = [round(a, 2) for a in face_center_angles(sides)]
    r_ins = SHAFT_R * math.cos(math.pi / sides)
    half_z = 0.5 * p["plan_width"] * math.tan(math.radians(p["tilt_deg"])) \
        + 0.5 * p["amplitude"] + 0.05

    def point(a):
        return (r_ins * math.cos(math.radians(a)), r_ins * math.sin(math.radians(a)))

    coppie = []
    for a in centers:
        b = min((c for c in centers if c != a),
                key=lambda c: abs(abs(norm_angle(c - a)) - 180.0))
        if (b, a) in [(x[0], x[1]) for x in coppie]:
            continue
        pa, pb = point(a), point(b)
        axis = math.degrees(math.atan2(pb[1] - pa[1], pb[0] - pa[0]))
        # finestre di quota libere da entrambe le feritoie
        blocked = sorted([bands[a], bands[b]])
        windows, z = [], opening_top + half_z
        for lo, hi in blocked:
            if lo - half_z > z:
                windows.append((z, lo - half_z))
            z = max(z, hi + half_z)
        if shaft_hi - half_z > z:
            windows.append((z, shaft_hi - half_z))
        windows = [w for w in windows if w[1] - w[0] > 0.05]
        if windows:
            coppie.append((a, b, axis, windows))

    count = int(p.pop("count"))
    if len(coppie) < count:
        raise RuntimeError(f"servono {count} coppie di facce ma ne esistono {len(coppie)}")

    # Le coppie si ordinano per direzione dell'asse vista come RETTA (non come
    # vettore: una striscia non ha un verso), poi si alternano assegnando le quote
    # a zig-zag sull'ordine angolare, cosi' due strisce vicine in altezza non hanno
    # anche assi vicini e i loro varchi laterali non si allineano.
    coppie.sort(key=lambda c: c[2] % 180.0)
    scelte = [coppie[i] for i in range(count)]
    ordine = list(range(0, count, 2)) + list(range(1, count, 2))
    scelte = [scelte[i] for i in ordine]

    # Quote distribuite uniformemente sull'altezza utile del fusto: distanziarle
    # serve perche' il dado abbia spazio per ribaltarsi tra un urto e il successivo.
    lo = opening_top + half_z
    hi = PLINTH_H + SHAFT_H - half_z
    passo = (hi - lo) / count
    quote = [hi - passo * (i + 0.5) for i in range(count)]

    out = []
    for (a, b, axis, _), z in zip(scelte, quote):
        # Se la quota cade sulla feritoia di una delle due facce, la linguetta ne
        # copre un tratto dall'interno: effetto cosmetico su una fessura da 4 mm,
        # segnalato invece di essere evitato a costo di ammassare le strisce.
        su_feritoia = [f for f in (a, b)
                       if bands[f][0] - half_z < z < bands[f][1] + half_z]
        out.append(dict(face_a=a, face_b=b, axis_deg=round(axis, 2),
                        z=round(z, 3), over_slit=su_feritoia, **p))
    return out


def merlon_pattern(sides):
    """Altezze dei merli, una per faccia del parapetto (0 = vuoto).

    Vincolo: due merli adiacenti devono avere la stessa altezza, altrimenti al
    loro spigolo comune nascono due bordi liberi sovrapposti invece di una
    piega. Qui si alternano merlo e vuoto, e con `sides` dispari l'ultimo slot
    e' forzato a vuoto perche' altrimenti si troverebbe adiacente al primo.

    Per 9 lati si restituisce la sequenza scelta a mano nel modello originale,
    cosi' quel file resta riproducibile: contiene un merlo doppio e uno spezzato
    piu' basso, che l'alternanza automatica non produrrebbe.
    """
    if sides == len(MERLON_HEIGHTS):
        return list(MERLON_HEIGHTS)
    pool = [0.34, 0.30, 0.36, 0.20]
    pattern = [0.0] * sides
    slot = 0
    for k in range(0, sides - 1, 2):
        pattern[k] = pool[slot % len(pool)]
        slot += 1
    return pattern

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

# Merlature: una per faccia del parapetto, 0 = vuoto. Non sono blocchi separati
# ma il muro del parapetto che continua verso l'alto: la carta ha spessore zero,
# quindi un merlo e' un pannello piatto: si ritaglia il profilo a zigzag e la
# striscia si piega tutta insieme, zero pezzi da incollare. Come blocchi separati
# sarebbero 7 scatoline da ~9x6 mm alla scala di stampa: inassemblabili.
#
# Vincolo: due merli adiacenti devono avere la stessa altezza, altrimenti al
# loro spigolo comune nascono due bordi liberi sovrapposti invece di una piega.
# Altezze uguali consecutive si fondono in un merlo piu' largo.
MERLON_HEIGHTS = [0.34, 0.0, 0.30, 0.30, 0.0, 0.36, 0.0, 0.20, 0.0]

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

# Feritoie sul fusto: fessure verticali passanti, larghe ~2,8 mm alla scala di
# stampa. Piu' strette diventerebbero impossibili da ritagliare a mano.
SLIT_HALF_W = 0.045
# (angolo della faccia, centro verticale rispetto al centro faccia, semi-altezza).
# Le quote si alternano tra faccia e faccia: cosi' non si rimuove carta tutta
# alla stessa altezza, che indebolirebbe il tubo del fusto su un unico anello.
SLITS = [
    (-170.0, -0.55, 0.40),
    (-130.0, 0.35, 0.35),
    (-90.0, -0.55, 0.40),
    (-50.0, 0.35, 0.35),
    (-10.0, -0.55, 0.40),
    (30.0, 0.35, 0.35),
    (70.0, -0.55, 0.40),
    (110.0, 0.35, 0.35),
    (150.0, -0.55, 0.40),
]

# Muro di cinta decorativo davanti alla torre, oggetto separato ("Muro").
# E' un pannello a spessore zero come il resto del guscio, non un muretto pieno:
# in carta un muro pieno sarebbe una scatola sottile con decine di facce
# minuscole. La linguetta orizzontale alla base (foot_inward) e' la superficie
# da incollare, senza la quale un pannello a spessore zero non sta in piedi.
# Il raggio deve stare fuori dalla vaschetta, che a terra arriva a ~2,37.
# Ampiezza angolare a cui si mira per ogni segmento del muro. Il numero di
# segmenti si ricava dividendo il settore per questo valore, quindi non va
# scritto a mano: settore e numero di lati cambiano insieme.
WALL_SEGMENT_DEG = 20.0
WALL = dict(
    radius=2.80,
    # angle_from/angle_to e segments si ricavano dal settore della vaschetta;
    # questi valori restano solo come ripiego se si passa un settore esplicito.
    angle_from=-150.0,
    angle_to=-30.0,
    segments=7,
    base_height=0.55,
    foot_inward=0.25,
)
# La merlatura del muro alterna merlo e vuoto e viene generata in base al numero
# di segmenti: vale lo stesso vincolo della torre (merli adiacenti di altezza
# diversa creerebbero bordi liberi sovrapposti al posto di una piega).
# Apertura ad arco: e' decorativa, non un passaggio. Per arrivare a terra
# servirebbe una soglia di pochi decimi di millimetro, che si strapperebbe.
# `segment` viene sempre ricalcolato come quello centrale.
WALL_GATE = dict(
    segment=3,
    half_w=0.13,
    v_bottom=-0.20,
    v_spring=0.00,
    v_apex=0.20,
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


def quad_frame(face):
    """Assi locali e angoli di una faccia quadrangolare verticale.

    Restituisce `(P, BL, BR, TR, TL)` dove `P(u, v)` mappa coordinate locali
    (u = orizzontale sulla faccia, v = verticale) in coordinate mondo.
    """
    verts_loop = list(face.verts)
    if len(verts_loop) != 4:
        raise ValueError("serve una faccia quadrangolare")

    center = face.calc_center_median()
    normal = face.normal.copy()
    if normal.length < 1e-9:
        # Le facce appena create con bm.faces.new() hanno normale nulla finche'
        # non si chiama bm.normal_update(): senza normale gli assi locali sono
        # degeneri e la classificazione degli angoli fallisce.
        raise ValueError("normale della faccia nulla: chiamare bm.normal_update() prima")
    normal.normalize()
    up = Vector((0, 0, 1))
    right = normal.cross(up).normalized()

    def corner_key(v):
        d = v.co - center
        return (d.dot(right) > 0, d.dot(up) > 0)

    corner = {corner_key(v): v for v in verts_loop}
    if len(corner) != 4:
        raise ValueError(f"la faccia non ha 4 angoli distinti negli assi locali: {sorted(corner)}")

    def P(u, v):
        return center + right * u + up * v

    return (P, corner[(False, False)], corner[(True, False)],
            corner[(True, True)], corner[(False, True)])


def carve_outline(bm, face, outline_uv, corner_split):
    """Apre un foro passante di contorno arbitrario in una faccia quadrangolare planare.

    `outline_uv` sono i vertici del contorno in coordinate locali, in ordine
    antiorario partendo dal basso a sinistra. `corner_split` dice quanti
    spigoli del contorno competono a ciascuno dei 4 lati della faccia (la somma
    deve fare il numero di vertici del contorno).

    L'anello di riempimento e' ancorato SOLO ai 4 angoli della faccia: mettere
    vertici nuovi sugli spigoli condivisi coi vicini creerebbe T-junction
    non-manifold. Tutte le facce generate stanno nel piano della faccia
    originale, quindi sono planari.
    """
    P, BL, BR, TR, TL = quad_frame(face)
    W = [bm.verts.new(P(u, v)) for u, v in outline_uv]

    n = len(W)
    if sum(corner_split) != n:
        raise ValueError("corner_split non copre tutto il contorno")

    # Indici del contorno che coincidono con l'inizio di ciascun lato.
    starts, acc = [], 0
    for count in corner_split:
        starts.append(acc)
        acc += count

    quad_corners = [BL, BR, TR, TL]
    for side in range(4):
        a = quad_corners[side]
        b = quad_corners[(side + 1) % 4]
        i0 = starts[side]
        i1 = starts[(side + 1) % 4]
        # vertici del contorno da i1 indietro fino a i0 (senso opposto al bordo)
        span, j = [], i1
        while True:
            span.append(W[j % n])
            if j % n == i0 % n:
                break
            j -= 1
        bm.faces.new(tuple([a, b] + span))

    bmesh.ops.delete(bm, geom=[face], context="FACES_ONLY")


def carve_gothic_window(bm, face, half_w, v_bottom, v_spring, v_apex,
                        shoulder_frac, shoulder_h):
    """Apre una finestra ad arco a punta (faceted) in una faccia quadrangolare.

    Il contorno ha 8 vertici: base rettangolare piu' arco a punta in 4 segmenti.
    Il risultato e' un foro passante, cioe' il contorno resta come spigoli di
    bordo: e' esattamente cio' che serve perche' Pepakura ritagli la sagoma.
    Vedi la nota su WINDOW per il perche' non sia una tasca incassata.
    """
    v_should = v_spring + (v_apex - v_spring) * shoulder_h
    u_should = half_w * shoulder_frac
    outline = [
        (-half_w, v_bottom),      # 0 base sinistra    (angolo del lato inferiore)
        (0.0, v_bottom),          # 1 base centro
        (half_w, v_bottom),       # 2 base destra      (angolo del lato destro)
        (half_w, v_spring),       # 3 imposta destra
        (u_should, v_should),     # 4 spalla destra    (angolo del lato superiore)
        (0.0, v_apex),            # 5 vertice dell'arco
        (-u_should, v_should),    # 6 spalla sinistra  (angolo del lato sinistro)
        (-half_w, v_spring),      # 7 imposta sinistra
    ]
    carve_outline(bm, face, outline, corner_split=(2, 2, 2, 2))


def carve_slit(bm, face, half_w, v_center, half_h):
    """Apre una feritoia: fessura verticale rettangolare passante."""
    outline = [
        (-half_w, v_center - half_h),
        (half_w, v_center - half_h),
        (half_w, v_center + half_h),
        (-half_w, v_center + half_h),
    ]
    carve_outline(bm, face, outline, corner_split=(1, 1, 1, 1))


def add_shaft_slits(obj, marks, slits=None, half_w=None, opening_top=0.95):
    """Apre le feritoie sulle facce del fusto, sopra il varco della vaschetta."""
    slits = list(slit_specs(marks["sides"]) if slits is None else slits)
    half_w = SLIT_HALF_W if half_w is None else half_w

    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.faces.ensure_lookup_table()

    carved = 0
    for angle, v_center, half_h in slits:
        face = face_at_z_span(bm, opening_top, marks["shaft_top"], angle_deg=angle)
        if face is None:
            continue
        carve_slit(bm, face, half_w, v_center, half_h)
        carved += 1
        bm.faces.ensure_lookup_table()

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.normal_update()
    bm.to_mesh(mesh)
    mesh.update()
    bm.free()
    # Ogni feritoia rettangolare aggiunge 4 spigoli di bordo (il suo contorno).
    return {"slits": carved, "boundary_edges": carved * 4}


def open_top_and_crenellate(obj, marks, heights=None):
    """Apre la cima della torre e alza le merlature dal bordo del parapetto.

    La cima va aperta perche' e' da li' che entrano i dadi. I merli sono
    prolungamenti verticali dei pannelli del parapetto, complanari con essi:
    nessun pezzo aggiuntivo da assemblare.
    """
    heights = list(merlon_pattern(marks["sides"]) if heights is None else heights)
    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.faces.ensure_lookup_table()
    bm.verts.ensure_lookup_table()

    top_z = max(v.co.z for v in bm.verts)
    cap = next(
        (f for f in bm.faces
         if len(f.verts) == marks["sides"] and all(abs(v.co.z - top_z) < 1e-6 for v in f.verts)),
        None,
    )
    if cap is None:
        raise RuntimeError("tappo superiore non trovato")
    bmesh.ops.delete(bm, geom=[cap], context="FACES_ONLY")

    ring = sorted(
        (v for v in bm.verts if abs(v.co.z - top_z) < 1e-6),
        key=lambda v: math.atan2(v.co.y, v.co.x),
    )
    if len(ring) != len(heights):
        raise RuntimeError(f"il parapetto ha {len(ring)} lati ma sono date {len(heights)} altezze")

    # Vertici condivisi per (vertice del bordo, altezza): merli adiacenti di pari
    # altezza si fondono invece di duplicare lo spigolo verticale.
    shared = {}

    def top_vert(base, h):
        key = (base.index, round(h, 6))
        if key not in shared:
            shared[key] = bm.verts.new(base.co + Vector((0, 0, h)))
        return shared[key]

    raised = 0
    for i, h in enumerate(heights):
        if h <= 0:
            continue
        v0, v1 = ring[i], ring[(i + 1) % len(ring)]
        bm.faces.new((v0, v1, top_vert(v1, h), top_vert(v0, h)))
        raised += 1

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.normal_update()
    bm.to_mesh(mesh)
    mesh.update()
    bm.free()

    gaps = sum(1 for h in heights if h <= 0)
    groups = sum(
        1 for i, h in enumerate(heights)
        if h > 0 and heights[i - 1] <= 0            # inizio di una sequenza di merli
    )
    return {
        "merlon_faces": raised,
        "merlon_groups": groups,
        "gaps": gaps,
        # bordi liberi introdotti: la cima di ogni vuoto, la cima di ogni
        # pannello alzato, piu' i due fianchi verticali di ogni gruppo.
        "boundary_edges": gaps + raised + 2 * groups,
    }


def add_baffles(sides=None, specs=None):
    """Crea l'oggetto 'Deflettori': una striscia corrugata per deflettore.

    Ogni falda della corrugazione e' un quadrilatero con due lati paralleli
    all'asse della striscia, quindi planare per costruzione: nello sviluppo la
    striscia e' un rettangolo con linee di piega parallele, la forma piu' semplice
    che Pepakura possa gestire.
    """
    sides = SIDES if sides is None else sides
    specs = baffle_specs(sides) if specs is None else specs

    r_ins = SHAFT_R * math.cos(math.pi / sides)   # apotema: distanza della faccia piatta

    mesh = bpy.data.meshes.new("Deflettori_mesh")
    verts, faces = [], []
    for s in specs:
        aa, ab = math.radians(s["face_a"]), math.radians(s["face_b"])
        pa = Vector((r_ins * math.cos(aa), r_ins * math.sin(aa), s["z"]))
        pb = Vector((r_ins * math.cos(ab), r_ins * math.sin(ab), s["z"]))
        axis = (pb - pa)
        length = axis.length
        axis.normalize()
        # trasversale, inclinata di tilt_deg: percorrendola si scende
        flat = Vector((-axis.y, axis.x, 0.0)).normalized()
        phi = math.radians(s["tilt_deg"])
        across = flat * math.cos(phi) - Vector((0, 0, 1)) * math.sin(phi)
        normal = axis.cross(across).normalized()

        n_p = int(s["panels"])
        pitch = s["plan_width"] / n_p
        centre = pa + axis * (length / 2.0)
        na = Vector((math.cos(aa), math.sin(aa), 0.0))
        nb = Vector((math.cos(ab), math.sin(ab), 0.0))
        base = len(verts)
        for i in range(n_p + 1):
            off = -s["plan_width"] / 2.0 + pitch * i
            # creste e valli alternate: e' questo che da' altezza alla sezione
            ridge = normal * (s["amplitude"] / 2.0 * (1 if i % 2 == 0 else -1))
            crease = centre + across * off + ridge
            # Ogni cresta va tagliata SUI PIANI delle due facce, non a lunghezza
            # fissa: le facce non sono esattamente opposte, quindi spostandosi in
            # senso trasversale gli estremi escrescerebbero oltre la parete.
            ta = (r_ins - crease.dot(na)) / axis.dot(na)
            tb = (r_ins - crease.dot(nb)) / axis.dot(nb)
            verts.append(crease + axis * ta)
            verts.append(crease + axis * tb)
        for i in range(n_p):
            k = base + 2 * i
            faces.append((k, k + 1, k + 3, k + 2))

    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new("Deflettori", mesh)
    bpy.context.collection.objects.link(obj)

    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.normal_update()
    bm.to_mesh(mesh)
    mesh.update()
    bm.free()
    scale = REFERENCE_HEIGHT_MM / (PLINTH_H + SHAFT_H + sum(h for h, _ in RINGS))
    p0 = specs[0]
    pitch = p0["plan_width"] / p0["panels"]
    return obj, {
        "count": len(specs),
        "specs": [{"da_faccia": s["face_a"], "a_faccia": s["face_b"],
                   "asse_deg": s["axis_deg"], "z": s["z"]} for s in specs],
        "assi_a_deg": None if len(specs) < 2 else round(
            abs(norm_angle(specs[1]["axis_deg"] - specs[0]["axis_deg"])), 1),
        "mm": {
            "larghezza_in_pianta": round(p0["plan_width"] * scale, 1),
            "larghezza_sviluppata": round(
                p0["panels"] * math.hypot(pitch, p0["amplitude"]) * scale, 1),
            "passo_creste": round(pitch * scale, 1),
            "ampiezza": round(p0["amplitude"] * scale, 1),
        },
    }


def check_baffles_fit(baffle_obj, shell_obj, tol=0.01):
    """Verifica che nessun deflettore sbuchi dalle pareti del guscio.

    I vertici della cerniera stanno *sulla* parete per costruzione, quindi qui non
    si pretende un margine positivo come per la rampa: si controlla soltanto che
    nessun vertice stia fuori. Il ray-cast parte dall'asse, quindi va saltato per
    la punta, che passa oltre l'asse e non ha una direzione radiale sensata.
    """
    rows, worst = [], None
    for v in baffle_obj.data.vertices:
        co = baffle_obj.matrix_world @ v.co
        radial = Vector((co.x, co.y, 0.0))
        if radial.length < 0.05:
            continue
        hit, loc, _, _ = shell_obj.ray_cast(
            Vector((0.0, 0.0, co.z)), radial.normalized())
        if not hit:
            continue
        margin = (loc - Vector((0.0, 0.0, co.z))).length - radial.length
        rows.append({"co": [round(c, 3) for c in co], "margine": round(margin, 4)})
        if worst is None or margin < worst:
            worst = margin
    return {"verts": rows, "worst_margin": None if worst is None else round(worst, 4),
            "ok": worst is not None and worst >= -tol}


def check_baffle_coverage(baffle_obj, sides=None, target_height_mm=None,
                          smallest_die_mm=15.0, grid=90):
    """Misura se un dado puo' cadere dritto senza toccare alcun deflettore.

    Non basta contare la percentuale di sezione coperta: cio' che conta e' il
    **canale libero piu' largo**, perche' un dado passa solo se trova un varco
    piu' grande di se'. Qui si spara un raggio verticale da una griglia di punti
    della sezione del fusto e si cerca il cerchio piu' grande che sta interamente
    nella zona non coperta (limitato anche dalle pareti).

    `smallest_die_mm` e' il dado piu' piccolo di un set poliedrico (il d8, ~15 mm),
    non il d20: e' quello il caso peggiore.
    """
    sides = SIDES if sides is None else sides
    if target_height_mm is None:
        target_height_mm = REFERENCE_HEIGHT_MM
    scale = target_height_mm / (PLINTH_H + SHAFT_H + sum(h for h, _ in RINGS))
    r_ins = SHAFT_R * math.cos(math.pi / sides)
    normals = [(math.cos(math.radians(90 + (k + 0.5) * 360.0 / sides)),
                math.sin(math.radians(90 + (k + 0.5) * 360.0 / sides)))
               for k in range(sides)]

    inside = []
    for i in range(grid):
        for j in range(grid):
            x = -SHAFT_R + 2 * SHAFT_R * i / (grid - 1)
            y = -SHAFT_R + 2 * SHAFT_R * j / (grid - 1)
            if all(x * nx + y * ny <= r_ins - 1e-9 for nx, ny in normals):
                inside.append((x, y))

    z_top = PLINTH_H + SHAFT_H
    free, blocked = [], []
    for x, y in inside:
        hit, _, _, _ = baffle_obj.ray_cast(
            Vector((x, y, z_top)), Vector((0.0, 0.0, -1.0)))
        (blocked if hit else free).append((x, y))

    r_max = 0.0
    for x, y in free:
        d_wall = min(r_ins - (x * nx + y * ny) for nx, ny in normals)
        d_blk = min((math.hypot(x - bx, y - by) for bx, by in blocked), default=99.0)
        r_max = max(r_max, min(d_wall, d_blk))

    channel_mm = 2.0 * r_max * scale
    return {
        "copertura_pct": round(100.0 * len(blocked) / len(inside)),
        "canale_libero_mm": round(channel_mm, 1),
        "dado_piu_piccolo_mm": smallest_die_mm,
        "ok": channel_mm < smallest_die_mm,
    }


def check_baffle_passage(sides=None, specs=None, target_height_mm=None,
                         largest_die_mm=20.0, grid=90):
    """Verifica che il dado riesca a SCENDERE oltre ogni singolo deflettore.

    E' il criterio opposto a check_baffle_coverage: quello pretende che l'insieme
    delle strisce non lasci un canale verticale libero, questo pretende che
    ciascuna striscia da sola lasci un varco piu' largo del dado piu' GRANDE,
    altrimenti il dado si incastra al posto di scendere. Progettare guardando solo
    la copertura porta a un imbuto che si intasa.
    """
    sides = SIDES if sides is None else sides
    specs = baffle_specs(sides) if specs is None else specs
    rows, worst = [], None
    for i, s in enumerate(specs):
        obj, _ = add_baffles(sides=sides, specs=[s])
        cov = check_baffle_coverage(obj, sides=sides,
                                    target_height_mm=target_height_mm,
                                    smallest_die_mm=largest_die_mm, grid=grid)
        bpy.data.objects.remove(obj, do_unlink=True)
        gap = cov["canale_libero_mm"]
        rows.append({"striscia": i + 1, "z": s["z"], "varco_mm": gap,
                     "passa": gap >= largest_die_mm})
        worst = gap if worst is None else min(worst, gap)
    return {"per_striscia": rows, "varco_minimo_mm": worst,
            "dado_piu_grande_mm": largest_die_mm,
            "ok": worst is not None and worst >= largest_die_mm}


def add_perimeter_wall(merlons=None, gate=None, sides=None, **overrides):
    """Crea l'oggetto 'Muro': muretto di cinta merlato davanti alla torre.

    Pannello ad arco sfaccettato con linguetta di incollaggio alla base,
    merlatura in cima e un'apertura ad arco decorativa. Riusa le stesse due
    tecniche del guscio: merli come prolungamento del pannello e foro passante
    tramite `carve_outline`.
    """
    p = dict(WALL)
    p.update(overrides)

    # Il muro copre lo stesso settore della vaschetta: con un numero di lati
    # diverso da 9 quel settore cambia, quindi gli angoli vanno ricavati e non
    # letti da WALL. Il numero di segmenti si adegua per mantenere la stessa
    # risoluzione angolare (~17 gradi per segmento) e resta dispari, cosi' la
    # merlatura alternata comincia e finisce con un merlo.
    sides = SIDES if sides is None else sides
    if "angle_from" not in overrides and "angle_to" not in overrides:
        sector = tray_face_angles(sides)
        half = half_face_angle(sides)
        p["angle_from"] = sector[0] - half
        p["angle_to"] = sector[-1] + half
    if "segments" not in overrides:
        span = abs(p["angle_to"] - p["angle_from"])
        # ~20 gradi per segmento, forzato dispari perche' la merlatura alternata
        # cominci e finisca con un merlo. Da' 7 segmenti sul settore di 120 gradi
        # della torre a 9 lati e 5 su quello di 103 gradi della torre a 7 lati:
        # segmenti piu' larghi (29 mm invece di 21 alla scala di stampa) sono
        # meno faticosi da piegare su carta pesante.
        p["segments"] = max(3, int(round(span / WALL_SEGMENT_DEG)) | 1)

    n = p["segments"]
    if merlons is None:
        merlons = [0.20 if i % 2 == 0 else 0.0 for i in range(n)]
    else:
        merlons = list(merlons)
    if gate is None:
        gate = dict(WALL_GATE)
        gate["segment"] = n // 2          # segmento centrale, qualunque sia n
    elif gate:
        gate = dict(gate)
    else:
        gate = None
    if gate is not None and not 0 <= gate["segment"] < n:
        raise RuntimeError(f"segmento {gate['segment']} fuori dai {n} del muro")

    if len(merlons) != n:
        raise RuntimeError(f"{n} segmenti ma {len(merlons)} altezze di merlo")

    mesh = bpy.data.meshes.new("Muro_mesh")
    obj = bpy.data.objects.new("Muro", mesh)
    bpy.context.collection.objects.link(obj)

    bm = bmesh.new()
    r_out = p["radius"]
    r_in = r_out - p["foot_inward"]
    h = p["base_height"]
    a0, a1 = math.radians(p["angle_from"]), math.radians(p["angle_to"])

    outer, inner, top = [], [], []
    for i in range(n + 1):
        a = a0 + (a1 - a0) * i / n
        ca, sa = math.cos(a), math.sin(a)
        outer.append(bm.verts.new(Vector((r_out * ca, r_out * sa, 0.0))))
        inner.append(bm.verts.new(Vector((r_in * ca, r_in * sa, 0.0))))
        top.append(bm.verts.new(Vector((r_out * ca, r_out * sa, h))))

    panels = []
    for i in range(n):
        bm.faces.new((outer[i], outer[i + 1], inner[i + 1], inner[i]))   # linguetta
        panels.append(bm.faces.new((outer[i], outer[i + 1], top[i + 1], top[i])))

    shared = {}

    def merlon_vert(base, height):
        key = (id(base), round(height, 6))
        if key not in shared:
            shared[key] = bm.verts.new(base.co + Vector((0, 0, height)))
        return shared[key]

    raised = 0
    for i, mh in enumerate(merlons):
        if mh <= 0:
            continue
        bm.faces.new((top[i], top[i + 1], merlon_vert(top[i + 1], mh), merlon_vert(top[i], mh)))
        raised += 1

    bm.faces.ensure_lookup_table()
    # Necessario prima di carve_*: le facce appena create hanno normale nulla.
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.normal_update()

    gate_edges = 0
    if gate:
        idx = gate.pop("segment")
        carve_gothic_window(bm, panels[idx], **gate)
        gate_edges = 8

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.normal_update()
    bm.to_mesh(mesh)
    mesh.update()
    bm.free()

    gaps = sum(1 for mh in merlons if mh <= 0)
    groups = sum(
        1 for i, mh in enumerate(merlons)
        if mh > 0 and (i == 0 or merlons[i - 1] <= 0)
    )
    return obj, {
        "segments": n,
        "merlon_faces": raised,
        "merlon_groups": groups,
        "gaps": gaps,
        # linguetta interna (n) + 2 lati della linguetta + 2 lati del pannello
        # + cima dei vuoti + profilo dei merli + contorno dell'apertura
        "boundary_edges": n + 2 + 2 + gaps + raised + 2 * groups + gate_edges,
    }


def add_exit_ramp(face_angles=None, sides=None, **overrides):
    """Crea l'oggetto 'Rampa': cuneo chiuso che inclina il pavimento verso l'uscita.

    Il piano superiore e' un trapezio i cui 4 vertici sono complanari perche' la
    quota dipende solo da y (z = a*y + b): allargando il fronte senza toccare la
    quota il piano resta planare, quindi il pezzo si piega combaciando.
    """
    if face_angles is None:
        face_angles = tray_face_angles(SIDES if sides is None else sides)
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


def add_dice_tray(obj, marks, face_angles=None,
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
    if face_angles is None:
        face_angles = tray_face_angles(marks["sides"])
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

    # Mezza faccia piu' un margine: con un numero di lati diverso da 9 le facce
    # sono piu' larghe e un valore fisso mancherebbe le facce del settore.
    half = half_face_angle(marks["sides"])
    a_lo, a_hi = min(face_angles) - (half + 0.5), max(face_angles) + (half + 0.5)
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

    rim_angles = [a - half for a in face_angles] + [face_angles[-1] + half]

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


def build_tower(sides=None):
    """Costruisce l'oggetto 'Torre' e restituisce le quote chiave.

    `sides` sovrascrive SIDES: tutto cio' che dipende dal numero di facce viene
    ricavato dai generatori in cima al file, quindi lo stesso script produce sia
    la torre a 9 lati sia le varianti semplificate.
    """
    sides = SIDES if sides is None else sides
    # Va rimosso tutto cio' che lo script rigenera, altrimenti rieseguirlo
    # accumula duplicati (Rampa.001, Rampa.002, ...).
    for name in list(bpy.data.objects.keys()):
        if name in ("Torre", "Rampa", "Muro", "Deflettori") or \
                name.startswith(("Merlone_", "Muro.", "Rampa.", "Deflettori.")):
            bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)
    for m in list(bpy.data.meshes):
        if m.users == 0:
            bpy.data.meshes.remove(m)

    bpy.ops.mesh.primitive_cylinder_add(
        vertices=sides, radius=SHAFT_R, depth=SHAFT_H,
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
    for v, extra in zip(cap_verts, plinth_jag(sides)):
        ang = math.atan2(v.co.y, v.co.x)
        r = PLINTH_R + extra
        v.co.x, v.co.y = r * math.cos(ang), r * math.sin(ang)

    bmesh.ops.translate(bm, verts=list(bm.verts), vec=Vector((0, 0, PLINTH_H)))

    # Corpo: sequenza di rastremazioni e tamburi.
    max_z = max(v.co.z for v in bm.verts)
    cur_face = next(f for f in bm.faces if all(abs(v.co.z - max_z) < 1e-6 for v in f.verts))
    cur_r = SHAFT_R
    z = max_z
    marks = {"sides": sides, "shaft_bottom": PLINTH_H, "shaft_top": max_z}
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


def export_for_pepakura(target_height_mm=None, out_dir=None,
                        names=("Torre", "Rampa", "Muro", "Deflettori"), combined=True,
                        basename="PaperDiceTower"):
    """Esporta gli OBJ per Pepakura, scalati all'altezza di stampa richiesta.

    Per default scrive un file solo con tutti i sotto-assemblaggi. Con file
    separati Pepakura crea un documento per file, e ogni documento occupa almeno
    una pagina: misurando le aree, `Torre` riempie il 70% di un A4 ma `Muro`
    l'8% e `Rampa` il 6%, quindi si stampano tre pagine di cui due quasi bianche.
    Nel file unico Pepakura annida i pezzi sugli stessi fogli tenendoli
    comunque distinti e numerati, e il totale sta in ~1 pagina piu' le linguette.
    `combined=False` torna a un file per oggetto (utile per ristampare un solo
    pezzo).

    La scala si applica in fase di export (`global_scale`) invece di ridimensionare
    gli oggetti: il modello sul disco resta in unita' di lavoro e si puo' esportare
    a taglie diverse senza toccarlo. Tutti gli oggetti condividono l'origine del
    mondo, quindi una scala uniforme li lascia allineati tra loro.

    Un OBJ non porta unita' di misura: qui i numeri sono millimetri, cosi'
    l'altezza dell'assieme vale esattamente *target_height_mm*. In Pepakura va
    comunque verificata la scala nella sua finestra di dialogo.

    `export_triangulated_mesh` resta disattivato: triangolare moltiplicherebbe
    le linee di piega, e le facce quadrangolari o n-gon sono per costruzione
    planari, quindi Pepakura le apre come un unico pannello.
    """
    import os

    if target_height_mm is None:
        target_height_mm = REFERENCE_HEIGHT_MM
    if out_dir is None:
        out_dir = os.path.join(os.path.dirname(bpy.data.filepath), "export")
    os.makedirs(out_dir, exist_ok=True)

    objs = [bpy.data.objects[n] for n in names if n in bpy.data.objects]
    z_all = [(o.matrix_world @ v.co).z for o in objs for v in o.data.vertices]
    height_units = max(z_all) - min(z_all)
    scale = target_height_mm / height_units

    def write(path, selection):
        bpy.ops.object.select_all(action="DESELECT")
        for o in selection:
            o.select_set(True)
        bpy.context.view_layer.objects.active = selection[0]
        bpy.ops.wm.obj_export(
            filepath=path,
            export_selected_objects=True,
            global_scale=scale,
            apply_transform=True,
            export_triangulated_mesh=False,
            export_normals=True,
            # Nessuna UV e nessun materiale: il modello e' senza texture, e
            # scriverli genererebbe un .mtl vuoto. Vanno riattivati se e quando si
            # ripartira' col capitolo texture (vedi memory/reference_texture_tentativi.md).
            export_uv=False,
            export_materials=False,
        )
        return path

    written = {}
    if combined:
        # `basename` permette di esportare una variante senza sovrascrivere
        # l'OBJ della versione principale, che e' versionato nel repo.
        written[basename] = write(os.path.join(out_dir, f"{basename}.obj"), objs)
    else:
        for o in objs:
            written[o.name] = write(os.path.join(out_dir, f"{o.name}.obj"), [o])

    bpy.ops.object.select_all(action="DESELECT")

    # Area delle facce in mm2, per stimare quante pagine servono davvero.
    area_mm2 = {}
    for o in objs:
        bm = bmesh.new()
        bm.from_mesh(o.data)
        area_mm2[o.name] = round(sum(f.calc_area() for f in bm.faces) * scale ** 2)
        bm.free()
    a4_printable = 190 * 277

    return {
        "files": written,
        "combined": combined,
        "height_units": round(height_units, 4),
        "target_height_mm": target_height_mm,
        "global_scale": round(scale, 4),
        "up_axis": "Y",          # convenzione OBJ standard: la Z di Blender diventa Y
        "forward_axis": "-Z",
        "area_mm2": area_mm2,
        "pagine_a4_teoriche": round(sum(area_mm2.values()) / a4_printable, 2),
    }


def check_page_fit(target_height_mm=None, sides=None, page_mm=(200.0, 287.0)):
    """Stima se i pezzi srotolati entrano in una pagina, alla scala di stampa data.

    Ogni anello della torre si srotola in una striscia lunga quanto il perimetro
    del poligono e alta quanto la sua altezza (o l'apotema, per le rastremazioni).
    Un pezzo non puo' essere spezzato a cavallo di due fogli, quindi il vincolo
    che conta non e' l'area totale ma la **striscia piu' lunga**: se supera il
    lato maggiore della pagina va divisa a mano in Pepakura.

    `page_mm` e' l'area stampabile, non il formato: A4 con margini da 5 mm.
    E' una stima del rettangolo di ingombro, senza linguette, e Pepakura resta
    libero di annidare o dividere diversamente.
    """
    if target_height_mm is None:
        target_height_mm = REFERENCE_HEIGHT_MM
    sides = SIDES if sides is None else sides
    scale = target_height_mm / (PLINTH_H + SHAFT_H + sum(h for h, _ in RINGS))

    def chord(radius):
        return 2.0 * radius * math.sin(math.pi / sides) * scale

    def band_bbox(r_lo, r_hi, height):
        """Ingombro del pezzo srotolato di una banda della torre.

        Una banda cilindrica si srotola in un rettangolo esatto. Un tronco di
        cono invece si srotola in un **settore anulare**, che si incurva su se
        stesso: trattarlo come striscia rettilinea sovrastima molto il lato
        lungo (per il plinto di un fattore 2,5).
        """
        if abs(r_lo - r_hi) < 1e-9:
            return sides * chord(r_lo), height * scale
        slant = math.hypot(height, r_lo - r_hi)
        dr = abs(r_lo - r_hi)
        rho_out = slant * max(r_lo, r_hi) / dr
        rho_in = slant * min(r_lo, r_hi) / dr
        theta = 2.0 * math.pi * dr / slant          # apertura del settore
        pts = []
        for i in range(65):
            a = -theta / 2.0 + theta * i / 64.0
            for rho in (rho_in, rho_out):
                pts.append((rho * math.cos(a), rho * math.sin(a)))
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        return (max(xs) - min(xs)) * scale, (max(ys) - min(ys)) * scale

    bands = []
    r_bottom = PLINTH_R + max(plinth_jag(sides))
    bands.append(("plinto (catena)", *band_bbox(r_bottom, SHAFT_R, PLINTH_H)))
    bands.append(("fondo del plinto", 2 * r_bottom * scale, 2 * r_bottom * scale))
    bands.append(("fusto", sides * chord(SHAFT_R), (SHAFT_H - 0.95 + PLINTH_H) * scale))
    r_prev = SHAFT_R
    for i, (h, r) in enumerate(RINGS):
        bands.append((f"anello {i}", *band_bbox(r_prev, r, h)))
        r_prev = r

    wall_span = abs(tray_face_angles(sides)[-1] - tray_face_angles(sides)[0]) \
        + 2 * half_face_angle(sides)
    wall_segs = max(3, int(round(wall_span / WALL_SEGMENT_DEG)) | 1)
    wall_len = wall_segs * 2 * WALL["radius"] * math.sin(
        math.radians(wall_span / wall_segs) / 2) * scale
    bands.append(("muro", wall_len,
                  (WALL["base_height"] + 0.20 + WALL["foot_inward"]) * scale))

    page_short, page_long = sorted(page_mm)
    rows, oversize = [], []
    for name, length, height in bands:
        long_side, short_side = max(length, height), min(length, height)
        fits = long_side <= page_long and short_side <= page_short
        rows.append({"pezzo": name, "mm": [round(length), round(height)], "entra": fits})
        if not fits:
            oversize.append(name)

    return {
        "target_height_mm": target_height_mm,
        "sides": sides,
        "pagina_stampabile_mm": list(page_mm),
        "pezzi": rows,
        "fuori_misura": oversize,
        "ok": not oversize,
    }


def refresh_viewport():
    """Il viewport non si aggiorna da solo dopo modifiche via script."""
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            area.tag_redraw()
    bpy.context.view_layer.update()


def build_all(sides=None):
    """Costruisce torre, rampa e muro e restituisce tutti i report.

    `sides` sceglie il numero di facce: 9 e' il modello originale, valori piu'
    bassi lo semplificano (meno pannelli per striscia, meno pieghe, meno
    finestre e feritoie).
    """
    sides = SIDES if sides is None else sides
    torre, marks = build_tower(sides)
    n_windows = add_keep_windows(torre, marks)
    tray = add_dice_tray(torre, marks)
    slits = add_shaft_slits(torre, marks)
    crown = open_top_and_crenellate(torre, marks)
    rampa = add_exit_ramp(sides=sides)
    muro, wall_info = add_perimeter_wall(sides=sides)
    deflettori, baffle_info = add_baffles(sides=sides)

    report = check_mesh(torre)
    report["expected_boundary_edges"] = (
        n_windows * 8 + 2 * tray["tray_sectors"] + 4
        + crown["boundary_edges"] + slits["boundary_edges"]
    )
    wall_report = check_mesh(muro)
    wall_report["expected_boundary_edges"] = wall_info["boundary_edges"]

    return {
        "sides": sides,
        "marks": marks,
        "windows": n_windows,
        "tray": tray,
        "slits": slits,
        "crown": crown,
        "wall": wall_info,
        "check_torre": report,
        "check_muro": wall_report,
        "check_rampa": check_mesh(rampa),
        "fit_rampa": check_ramp_fits(rampa, torre),
        "deflettori": baffle_info,
        "check_deflettori": check_mesh(deflettori),
        "fit_deflettori": check_baffles_fit(deflettori, torre),
        "copertura_deflettori": check_baffle_coverage(deflettori, sides=sides),
        "passaggio_deflettori": check_baffle_passage(sides=sides),
    }


if __name__ == "__main__":
    torre, MARKS = build_tower()
    N_WINDOWS = add_keep_windows(torre, MARKS)
    TRAY = add_dice_tray(torre, MARKS)
    SLITS_DONE = add_shaft_slits(torre, MARKS)
    CROWN = open_top_and_crenellate(torre, MARKS)
    RAMPA = add_exit_ramp()
    RAMP_REPORT = check_mesh(RAMPA)
    RAMP_FIT = check_ramp_fits(RAMPA, torre)
    MURO, WALL_INFO = add_perimeter_wall()
    WALL_REPORT = check_mesh(MURO)
    WALL_REPORT["expected_boundary_edges"] = WALL_INFO["boundary_edges"]
    REPORT = check_mesh(torre)
    # Bordi attesi, derivati dalla topologia delle aperture volute:
    #   8 per ogni finestra passante (il suo contorno);
    #   per la vaschetta con n settori: n bordi del suo lato aperto in alto,
    #   2 spigoli in cima ai fianchi, piu' il contorno del varco (2 verticali
    #   piu' n in alto) = 2n + 4;
    #   piu' il profilo della merlatura e i contorni delle feritoie.
    _n = TRAY["tray_sectors"]
    REPORT["expected_boundary_edges"] = (
        N_WINDOWS * 8 + 2 * _n + 4
        + CROWN["boundary_edges"]
        + SLITS_DONE["boundary_edges"]
    )
    refresh_viewport()
    print("marks:", MARKS)
    print("windows:", N_WINDOWS)
    print("tray:", TRAY)
    print("slits:", SLITS_DONE)
    print("crown:", CROWN)
    print("check torre:", REPORT)
    print("check rampa:", RAMP_REPORT)
    print("fit rampa:", RAMP_FIT["ok"], "margine minimo:", RAMP_FIT["worst_margin"])
    print("muro:", WALL_INFO)
    print("check muro:", WALL_REPORT)
