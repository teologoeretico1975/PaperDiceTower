"""Genera le texture del modello, ripetibili senza cuciture visibili.

Eseguire con il Python di sistema (serve PIL), non con quello di Blender:

    python make_textures.py

Scrive in textures/ due serie, che diventano due varianti stampabili del kit:

  stone.png / stone_moss.png            muratura completa
  flat_stone.png / flat_moss.png        tinte piatte, da colorare a mano

La variante a tinte piatte non e' una riduzione di qualita' ma una scelta di
prodotto: la muratura completa copre di inchiostro circa il 45% di 1.051 cm2, che
per chi stampa a casa e' un costo reale, e il medio grigio fa concorrenza alle
linee di taglio e piega di Pepakura. Le tinte piatte costano una frazione,
lasciano le linee perfettamente leggibili e accettano bene matita e pennarello.
La scelta resta all'acquirente.

Perche' ripetibili e non una texture unica: una tile piccola applicata con UV
scalate resta nitida a qualunque scala di stampa e pesa pochi kB, mentre una
texture unica per stampare 30 cm a 300 DPI vorrebbe 4096x4096. Il limite e' che
una tile non puo' avere variazioni posizionali (piu' muschio in basso), e per
questo se ne generano due varianti da assegnare a fasce di altezza diverse.

Tutto e' ripetibile per costruzione:
  - il rumore nasce da una griglia interpolata con indici modulari, quindi il
    bordo destro combacia col sinistro e il basso con l'alto;
  - i corsi di mattoni hanno un periodo che divide esattamente il lato della tile.
"""

import os

import numpy as np
from PIL import Image

SIZE = 512
COURSES = 8              # corsi per tile
BRICKS_PER_COURSE = (3, 5)   # blocchi per corso, estremi inclusi
MORTAR = 4               # spessore della fuga in pixel
SEED = 7

COURSE_H = SIZE // COURSES


def value_noise(size, cells, seed):
    """Rumore interpolato, ripetibile: gli indici della griglia sono modulari."""
    rng = np.random.default_rng(seed)
    grid = rng.random((cells, cells))
    ys, xs = np.mgrid[0:size, 0:size].astype(np.float64)
    gx, gy = xs * cells / size, ys * cells / size
    x0, y0 = np.floor(gx).astype(int), np.floor(gy).astype(int)
    fx, fy = gx - x0, gy - y0
    # smoothstep: evita gli spigoli dell'interpolazione lineare
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    x1, y1 = (x0 + 1) % cells, (y0 + 1) % cells
    x0, y0 = x0 % cells, y0 % cells
    top = grid[y0, x0] * (1 - fx) + grid[y0, x1] * fx
    bot = grid[y1, x0] * (1 - fx) + grid[y1, x1] * fx
    return top * (1 - fy) + bot * fy


def fbm(size, cells, octaves, seed):
    out, amp, total = np.zeros((size, size)), 1.0, 0.0
    for o in range(octaves):
        out += amp * value_noise(size, cells * 2 ** o, seed + o * 101)
        total += amp
        amp *= 0.5
    return out / total


def course_widths(rng):
    """Larghezze dei blocchi di un corso, che sommano esattamente al lato della tile.

    E' questo vincolo a mantenere la ripetibilita' orizzontale pur avendo blocchi
    di dimensioni diverse: il corso si chiude sempre sul bordo.
    """
    n = int(rng.integers(BRICKS_PER_COURSE[0], BRICKS_PER_COURSE[1] + 1))
    w = rng.random(n) + 0.6                      # niente blocchi troppo sottili
    w = np.maximum((w / w.sum() * SIZE).astype(int), 40)
    w[-1] = SIZE - w[:-1].sum()                  # l'ultimo assorbe l'arrotondamento
    return w


def brick_layout():
    """Distanza dalla fuga piu' vicina e identificativo del blocco, per pixel."""
    rng = np.random.default_rng(SEED + 4242)
    d_edge = np.zeros((SIZE, SIZE), dtype=np.int32)
    brick_id = np.zeros((SIZE, SIZE), dtype=np.int32)
    next_id = 1
    for r in range(COURSES):
        y0, y1 = r * COURSE_H, (r + 1) * COURSE_H
        ys_in = np.arange(COURSE_H)[:, None]
        dy = np.minimum(ys_in, COURSE_H - 1 - ys_in)
        # ogni corso parte con uno sfalsamento proprio, non con mezzo blocco fisso
        offset = int(rng.integers(0, SIZE))
        x = 0
        for w in course_widths(rng):
            cols = (np.arange(x, x + w) + offset) % SIZE
            xs_in = np.arange(w)[None, :]
            dx = np.minimum(xs_in, w - 1 - xs_in)
            d_edge[y0:y1, cols] = np.minimum(dx, dy)
            brick_id[y0:y1, cols] = next_id
            next_id += 1
            x += w
    return d_edge, brick_id


def build():
    d_edge, brick_id = brick_layout()
    mortar = d_edge < MORTAR

    rng = np.random.default_rng(SEED)
    # tinta propria di ogni mattone: la variazione e' cio' che evita l'effetto
    # "carta da parati" nonostante la tile si ripeta
    per_brick = rng.random(brick_id.max() + 1) * 2.0 - 1.0
    tint = per_brick[brick_id] * 16.0

    grain = (fbm(SIZE, 8, 4, SEED) - 0.5) * 26.0
    stain = (fbm(SIZE, 3, 3, SEED + 55) - 0.45) * 30.0

    base = 158.0 + tint + grain + np.clip(stain, -34, 8)
    # smusso verso il bordo del blocco: da' rilievo senza cuocere ombre direzionali
    bevel = np.clip((d_edge - MORTAR) / 8.0, 0.0, 1.0)
    base = base * (0.84 + 0.16 * bevel)
    # La fuga e' PIU' SCURA della pietra: in muratura il giunto e' in ombra, ed e'
    # questo che distingue la pietra da un muro di mattoni moderno.
    base = np.where(mortar, 92.0 + grain * 0.4, base)

    stone = np.stack([base * 1.00, base * 0.985, base * 0.94], axis=-1)
    stone = np.clip(stone, 0, 255)

    # muschio: cresce nelle fughe, quindi la maschera e' polarizzata verso queste
    m = fbm(SIZE, 4, 4, SEED + 900)
    m = m + np.where(mortar, 0.16, -0.05)
    moss_mask = np.clip((m - 0.52) * 3.4, 0.0, 1.0)
    moss_col = np.stack([np.full((SIZE, SIZE), 96.0),
                         np.full((SIZE, SIZE), 118.0),
                         np.full((SIZE, SIZE), 62.0)], axis=-1)
    moss_col = moss_col * (0.75 + 0.5 * grain[..., None] / 26.0)
    mossy = stone * (1 - moss_mask[..., None]) + moss_col * moss_mask[..., None]
    mossy = np.clip(mossy, 0, 255)

    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "textures")
    os.makedirs(out_dir, exist_ok=True)
    written = {}
    for name, arr in (("stone", stone), ("stone_moss", mossy)):
        path = os.path.join(out_dir, name + ".png")
        Image.fromarray(arr.astype(np.uint8)).save(path, optimize=True)
        written[name] = path
    return written, moss_mask


# --- Muratura da fotoscansione -------------------------------------------
#
# Se in textures/src/ c'e' una mappa diffuse ripetibile, la muratura viene
# derivata da quella invece che generata proceduralmente: blocchi e grana veri
# battono qualunque procedurale. La sorgente NON e' versionata (pesa MB e non
# serve a chi usa il kit), quindi restano versionate le tile derivate e la
# procedurale fa da riserva se la sorgente manca.
#
# ATTENZIONE ALLA LICENZA: verificare che la sorgente sia utilizzabile
# commercialmente prima di vendere il kit. I pack CC0 (Poly Haven) lo sono, altri
# no, e dal solo nome del file non si distingue.
#
# Due rimappature obbligatorie, che sono la parte non ovvia:
#
# 1. Schiarire. Una texture per il 3D e' pensata per essere illuminata: questa ha
#    luminanza media 63/255 e massimo 170, cioe' non contiene nemmeno un bianco.
#    Su carta il valore stampato e' quello finale, quindi cosi' com'e' coprirebbe
#    il 75% di inchiostro. Portandola a media 185 scende al 27%.
# 2. Ridurre la crominanza. Applicare la gamma canale per canale amplifica la
#    dominante calda della fotografia e la pietra grigia diventa arenaria dorata.
#    Si rimappa quindi la sola luminanza e la crominanza si comprime.
PHOTO_SUBDIR = "src"
PHOTO_PATTERNS = ("*diff*.jpg", "*diff*.png", "*albedo*.jpg", "*albedo*.png")
PHOTO_SIZE = 1024        # una tile da 80 mm a 300 DPI vuole 945 px: oltre e' peso inutile
PHOTO_TARGET_MEAN = 185.0
PHOTO_CHROMA = 0.30
# La soglia del muschio si ricava dalla copertura desiderata, non si fissa a mano:
# dipende dall'istogramma della sorgente, e un valore assoluto scelto a occhio
# aveva prodotto l'1% di copertura invece del 12% voluto.
# `gain` governa quanto e' netto il bordo della chiazza. Un valore basso (3) dava
# una frangia che tingeva di verde il 72% della tile: la pietra risultava verde
# invece che grigia con chiazze. Alzandolo la frangia si stringe attorno alle
# chiazze vere.
PHOTO_MOSS = dict(shadow_weight=0.55, patch_weight=0.45, coverage_pct=11.0, gain=11.0)
MOSS_RGB = (104, 122, 74)


def find_photo_source(out_dir):
    import glob
    src = os.path.join(out_dir, PHOTO_SUBDIR)
    for pat in PHOTO_PATTERNS:
        hits = sorted(glob.glob(os.path.join(src, pat)))
        if hits:
            return hits[0]
    return None


def build_from_photo(path):
    """Muratura e variante col muschio derivate da una mappa diffuse."""
    img = Image.open(path).convert("RGB").resize((PHOTO_SIZE, PHOTO_SIZE), Image.LANCZOS)
    a = np.asarray(img).astype(np.float64)

    weights = np.array([0.2126, 0.7152, 0.0722])
    lum = a @ weights
    lo, hi = np.percentile(lum, [1, 99])
    x = np.clip((lum - lo) / (hi - lo), 0.0, 1.0)

    # gamma cercata per bisezione: e' l'esponente che porta la media al valore
    # voluto, e dipende dall'istogramma della sorgente
    g_lo, g_hi = 0.5, 12.0
    for _ in range(50):
        g = (g_lo + g_hi) / 2.0
        if (x ** (1.0 / g)).mean() * 255.0 < PHOTO_TARGET_MEAN:
            g_lo = g
        else:
            g_hi = g
    lum_new = (x ** (1.0 / g)) * 255.0
    chroma = (a - lum[..., None]) * PHOTO_CHROMA
    stone = np.clip(lum_new[..., None] + chroma, 0, 255)

    # Il muschio cresce dove l'acqua si ferma, cioe' nei sottosquadri: la maschera
    # combina la parte scura dell'immagine (le fughe e le cavita') con un rumore
    # ripetibile che ne rompe l'uniformita'.
    p = PHOTO_MOSS
    shadow = 1.0 - lum_new / 255.0
    patch = fbm(PHOTO_SIZE, 4, 4, SEED + 3300)
    m = p["shadow_weight"] * shadow + p["patch_weight"] * patch
    # `coverage_pct` deve significare "quanto muschio si vede", non "quanti pixel
    # ne hanno una traccia": la soglia si abbassa di mezzo passo di sfumatura,
    # cosi' i pixel oltre il percentile arrivano a mask > 0.5 e sono visibili,
    # e sotto resta una frangia morbida.
    threshold = float(np.percentile(m, 100.0 - p["coverage_pct"])) - 0.5 / p["gain"]
    mask = np.clip((m - threshold) * p["gain"], 0.0, 1.0)[..., None]
    moss_col = np.array(MOSS_RGB, dtype=np.float64) * (0.72 + 0.56 * lum_new[..., None] / 255.0)
    mossy = np.clip(stone * (1 - mask) + moss_col * mask, 0, 255)

    return stone, mossy, {
        "gamma": round(g, 2),
        "sorgente": os.path.basename(path),
        "muschio_visibile_pct": round(100.0 * float((mask > 0.5).mean())),
        "muschio_con_frangia_pct": round(100.0 * float((mask > 0.0).mean())),
    }


# Tinte piatte: chiare di proposito, cosi' l'inchiostro resta basso e la matita
# ci scrive sopra. Un colore uniforme si ripete per definizione, quindi una tile
# minuscola basta: il file pesa poche centinaia di byte.
FLAT_STONE = (214, 211, 203)
FLAT_MOSS = (196, 205, 182)
# Bianco puro: la stampa si riduce alle sole linee di taglio e piega disegnate da
# Pepakura. E' la base della scala di varianti, quella che costa meno inchiostro.
LINE_WHITE = (255, 255, 255)


def build_flat(out_dir):
    written = {}
    for name, rgb in (("flat_stone", FLAT_STONE), ("flat_moss", FLAT_MOSS),
                      ("line_white", LINE_WHITE)):
        path = os.path.join(out_dir, name + ".png")
        Image.new("RGB", (8, 8), rgb).save(path, optimize=True)
        written[name] = path
    return written


def ink_coverage(path):
    """Frazione di inchiostro stimata: 1 meno la luminosita' relativa media."""
    a = np.asarray(Image.open(path).convert("RGB")).astype(np.float64)
    return round(float((1 - a.mean(axis=2) / 255).mean()) * 100, 1)


def check_tileable(path, tol=14.0):
    """Verifica che i bordi opposti combacino: e' cio' che rende la tile invisibile."""
    a = np.asarray(Image.open(path)).astype(np.float64)
    dx = np.abs(a[:, 0] - a[:, -1]).mean()
    dy = np.abs(a[0, :] - a[-1, :]).mean()
    # confronto col salto medio tra colonne adiacenti dentro l'immagine
    inner = np.abs(a[:, 1:] - a[:, :-1]).mean()
    return {"salto_bordo_x": round(dx, 2), "salto_bordo_y": round(dy, 2),
            "salto_interno_medio": round(inner, 2),
            "ok": dx < inner + tol and dy < inner + tol}


if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "textures")
    os.makedirs(out_dir, exist_ok=True)

    photo = find_photo_source(out_dir)
    if photo:
        stone, mossy, info = build_from_photo(photo)
        for name, arr in (("stone", stone), ("stone_moss", mossy)):
            Image.fromarray(arr.astype(np.uint8)).save(
                os.path.join(out_dir, name + ".png"), optimize=True)
        print(f"muratura da fotoscansione: {info['sorgente']}  gamma {info['gamma']}  "
              f"muschio visibile {info['muschio_visibile_pct']}% "
              f"(con frangia {info['muschio_con_frangia_pct']}%)")
        files = {n: os.path.join(out_dir, n + ".png") for n in ("stone", "stone_moss")}
    else:
        print("nessuna sorgente in textures/src: uso la muratura procedurale")
        files, moss = build()
        print("copertura muschio procedurale: %.0f%%" % (100 * (moss > 0.3).mean()))

    files.update(build_flat(out_dir))
    for name, path in files.items():
        seam = check_tileable(path)
        print(f"{name:12s} inchiostro {ink_coverage(path):5.1f}%  "
              f"bordi {'ok' if seam['ok'] else 'DISCONTINUI'}  -> {path}")
