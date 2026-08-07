"""Lettura e validazione del cartamodello esportato da Pepakura.

Perche' esiste. Il PDF che Pepakura stampa e' l'ultimo anello della catena e per
molto tempo e' stato l'unico non verificato: `build_tower.py` controlla la mesh,
ma nessuno controllava che l'unfold uscisse con le misure giuste. Questo modulo
legge il PDF e misura i pezzi veri, senza aprire Pepakura e senza licenza.

Sulla macchina non ci sono librerie PDF, ma non servono: il PDF di Pepakura e'
vettoriale, i suoi content stream sono FlateDecode e contengono solo operatori di
path. Si decomprime con zlib e si interpreta il minimo indispensabile.

Uso:

    python tools/pattern.py inventario export/PaperDiceTower7_300.pdf

Identifica ogni pezzo, dice su che colore di cartoncino va stampato, e controlla
tre invarianti del cartamodello. Esce con codice 1 se un controllo non passa.

Sapeva anche generare il pattern con un layer di decoro vettoriale, ma quella
parte e' stata rimossa il 2026-08-07: il decoro si fa a mano in post-produzione
(Inkscape), quindi tenere in sincrono un PDF derivato a ogni re-impaginazione era
solo manutenzione. Il codice e la sua lezione restano recuperabili dal commit
f878218 e da memory/reference_decoro_registrato.md.
"""
import re
import sys
import zlib
from collections import defaultdict

PT_MM = 25.4 / 72.0          # punti PDF -> millimetri
A4_UTILE_MM = (200.0, 287.0)  # con i margini a 5 mm impostati in Pepakura


# --------------------------------------------------------------------------
# lettura del PDF
# --------------------------------------------------------------------------

def raw_streams(data):
    """Ogni stream del file, decompresso, etichettato content oppure image.

    Sniffare il dizionario che precede lo stream non funziona: il lookback
    prende gli oggetti vicini e classifica tutto come immagine. La stampabilita'
    dei primi byte invece separa i due casi in modo netto, perche' un content
    stream e' testo di operatori e un'immagine e' binaria.
    """
    out = []
    for m in re.finditer(rb"stream\r?\n", data):
        start = m.end()
        end = data.find(b"endstream", start)
        if end < 0:
            continue
        try:
            dec = zlib.decompress(data[start:end])
        except zlib.error:
            continue
        head = dec[:400]
        printable = sum(1 for b in head if 32 <= b < 127 or b in (9, 10, 13))
        out.append(("content" if printable > len(head) * 0.95 else "image", dec))
    return out


def page_count(data):
    m = re.search(rb"/Type\s*/Pages.*?/Count\s+(\d+)", data, re.S)
    return int(m.group(1)) if m else len(re.findall(rb"/Type\s*/Page[^s]", data))


_TOKEN = re.compile(
    rb"(-?\d*\.?\d+)|(\[\s*\])|(\[[^\]]*\])|"
    rb"\b(m|l|c|v|y|re|h|S|s|f|F|B|b|n|W|q|Q|cm|d|gs|w)\b"
)


def _mat_mul(a, b):
    a0, a1, a2, a3, a4, a5 = a
    b0, b1, b2, b3, b4, b5 = b
    return (a0 * b0 + a1 * b2, a0 * b1 + a1 * b3,
            a2 * b0 + a3 * b2, a2 * b1 + a3 * b3,
            a4 * b0 + a5 * b2 + b4, a4 * b1 + a5 * b3 + b5)


def _apply(m, x, y):
    return (m[0] * x + m[2] * y + m[4], m[1] * x + m[3] * y + m[5])


def segments(stream):
    """Segmenti (p0, p1, tratteggiato) di una pagina, in punti PDF.

    Il flag del tratteggio conta: in Pepakura le pieghe sono tratteggiate e i
    tagli continui, quindi l'operatore "d" distingue le due cose. Serve sia per
    validare (un rapporto anomalo fra i due segnala pieghe mascherate da tagli)
    sia per distinguere i pezzi dai fori, che non hanno pieghe proprie.
    """
    ident = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
    ctm, stack, dash_stack, nums = ident, [], [], []
    dashed = False
    segs = []
    cur = start = None
    for m in _TOKEN.finditer(stream):
        if m.group(1) is not None:
            nums.append(float(m.group(1)))
            continue
        if m.group(2) is not None:          # [] = tratto continuo
            dashed = False
            continue
        if m.group(3) is not None:          # [a b] = tratteggio
            dashed = True
            continue
        op = m.group(4).decode()
        if op == "q":
            stack.append(ctm)
            dash_stack.append(dashed)
        elif op == "Q":
            ctm = stack.pop() if stack else ident
            dashed = dash_stack.pop() if dash_stack else False
        elif op == "cm" and len(nums) >= 6:
            ctm = _mat_mul(tuple(nums[-6:]), ctm)
        elif op == "m" and len(nums) >= 2:
            cur = start = _apply(ctm, nums[-2], nums[-1])
        elif op in ("l", "c", "v", "y") and len(nums) >= 2:
            # nessuna curva in questo pattern (geometria tutta faceted): per le
            # curve si approssima col punto finale, che qui non capita mai
            p = _apply(ctm, nums[-2], nums[-1])
            if cur:
                segs.append((cur, p, dashed))
            cur = p
        elif op == "re" and len(nums) >= 4:
            x, y, w, h = nums[-4:]
            pts = [_apply(ctm, x, y), _apply(ctm, x + w, y),
                   _apply(ctm, x + w, y + h), _apply(ctm, x, y + h)]
            for i in range(4):
                segs.append((pts[i], pts[(i + 1) % 4], dashed))
            cur = start = pts[0]
        elif op == "h" and cur and start:
            segs.append((cur, start, dashed))
            cur = start
        if op != "d":
            nums = []
    return segs


def read_pages(path):
    data = open(path, "rb").read()
    streams = raw_streams(data)
    pages = [segments(s) for k, s in streams if k == "content"]
    n_img = sum(1 for k, _ in streams if k == "image")
    return pages, page_count(data), n_img


# --------------------------------------------------------------------------
# geometria: pezzi e contorni
# --------------------------------------------------------------------------

def cluster(segs, tol=0.4):
    """Componenti connesse dei segmenti: un gruppo = un pezzo da ritagliare.

    Attenzione a come si leggono i risultati: due strisce unite da una piega
    sono un solo pezzo, ed e' corretto che il conteggio le veda come una. Il
    corpo principale, per esempio, esce attaccato alle due bande di
    rastremazione, il che vincola il colore (vedi HANDOVER, sezione blocchi).
    """
    key = lambda p: (round(p[0] / tol), round(p[1] / tol))
    parent = {}

    def find(a):
        parent.setdefault(a, a)
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for i, s in enumerate(segs):
        union(("s", i), ("n",) + key(s[0]))
        union(("s", i), ("n",) + key(s[1]))
    grid = defaultdict(list)
    for k in [k for k in list(parent) if k[0] == "n"]:
        grid[(k[1], k[2])].append(k)
    for (gx, gy), ks in list(grid.items()):
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for k2 in grid.get((gx + dx, gy + dy), []):
                    union(ks[0], k2)
    groups = defaultdict(list)
    for i in range(len(segs)):
        groups[find(("s", i))].append(i)
    return list(groups.values())


def bbox(segs, idxs):
    xs, ys = [], []
    for i in idxs:
        for p in (segs[i][0], segs[i][1]):
            xs.append(p[0])
            ys.append(p[1])
    return min(xs), min(ys), max(xs), max(ys)


def dims_mm(segs, idxs):
    x0, y0, x1, y1 = bbox(segs, idxs)
    return (x1 - x0) * PT_MM, (y1 - y0) * PT_MM


# --------------------------------------------------------------------------
# feature riconoscibili sul pattern
# --------------------------------------------------------------------------

# Firme dimensionali in mm alla scala di riferimento (torre alta 300 mm). Sono
# quelle dichiarate nel README, e ritrovarle nel PDF e' il controllo che la
# scala non si sia persa lungo la catena.
FIRME = {
    "finestra ad arco": (11.8, 42.0),
    "feritoia lunga": (3.9, 35.0),
    "feritoia corta": (3.9, 30.6),
    "apertura del muro": (11.4, 17.5),
    "deflettore": (33.8, 68.1),
}


def match_firma(w, h, tol=2.0):
    lo, hi = min(w, h), max(w, h)
    for nome, (a, b) in FIRME.items():
        if abs(lo - a) <= tol and abs(hi - b) <= tol:
            return nome
    return None


# Identificazione dei pezzi per (numero di segmenti, numero di pieghe).
#
# Perche' questa coppia e non le dimensioni: conteggi di segmenti e pieghe sono
# invarianti per rotazione e traslazione, quindi identificano un pezzo
# ovunque stia nel foglio e comunque sia ruotato. Le dimensioni no - il bounding
# box cambia appena si ruota un pezzo, e nella re-impaginazione manuale del
# 2026-08-07 la rampa e' passata da 115,1x102,3 a 103,9x113,7 senza che nulla
# fosse cambiato nella geometria.
#
# Sono legate alla geometria di build_tower.py: se il modello cambia, la tabella
# va rifatta. Il tool dice "sconosciuto" invece di indovinare.
FIRME_PEZZO = {
    (96, 32): "corpo principale con le rastremazioni",
    (82, 30): "fusto, pezzo principale",
    (39, 13): "fusto, striscia",
    (23, 6):  "fusto, striscia",
    (43, 9):  "muro di cinta",
    (80, 28): "parapetto e merlature",
    (29, 9):  "rampa",
    (64, 22): "plinto",
    (20, 4):  "pianale della base",
    (13, 3):  "deflettore",
}

# A quale gruppo di colore appartiene ogni pezzo. Scelta del committente il
# 2026-08-07: pietra su tre pagine, verde erba sulla quarta. I deflettori stanno
# dentro il fusto e non si vedono mai, quindi il loro colore e' indifferente.
BLOCCHI = {
    "corpo principale con le rastremazioni": ("torre superiore", "pietra"),
    "fusto, pezzo principale": ("torre inferiore", "pietra"),
    "fusto, striscia": ("torre inferiore", "pietra"),
    "muro di cinta": ("muro, merli e rampa", "pietra"),
    "parapetto e merlature": ("muro, merli e rampa", "pietra"),
    "rampa": ("muro, merli e rampa", "pietra"),
    "plinto": ("plinto e base", "verde erba"),
    "pianale della base": ("plinto e base", "verde erba"),
    "deflettore": ("interno, non visibile", "qualunque"),
}

# Invarianti del cartamodello a 7 lati / 300 mm. Sono gli stessi pezzi comunque
# li si impagini, quindi questi tre numeri devono tornare identici dopo ogni
# re-impaginazione: se cambiano, il layout ha perso o duplicato qualcosa, ed e'
# un errore che a occhio sul foglio non si vede.
ATTESI = {"segmenti": 636, "pezzi": 13, "fori": 15}


def classifica(segs):
    """Separa pezzi da fori e identifica ogni pezzo. Ritorna (pezzi, fori).

    Un foro e' un gruppo il cui bounding box e' contenuto in quello di un altro
    **e** che non ha pieghe proprie. La seconda condizione serve: un deflettore
    che finisce nella concavita' di un pezzo grande soddisfa la prima e verrebbe
    contato come foro.
    """
    groups = strip_frame(segs, cluster(segs))
    boxes = [bbox(segs, g) for g in groups]
    dentro_di = []
    for i, b in enumerate(boxes):
        host = [j for j, c in enumerate(boxes)
                if j != i and c[0] <= b[0] and c[1] <= b[1]
                and c[2] >= b[2] and c[3] >= b[3]]
        pieghe = any(segs[k][2] for k in groups[i])
        dentro_di.append(host[0] if (host and not pieghe) else None)

    pezzi, fori = [], []
    for i, g in enumerate(groups):
        w, h = dims_mm(segs, g)
        n_pieghe = sum(1 for k in g if segs[k][2])
        rec = {"idx": i, "w": w, "h": h, "segmenti": len(g), "pieghe": n_pieghe,
               "firma": match_firma(w, h)}
        if dentro_di[i] is not None:
            rec["host"] = dentro_di[i]
            fori.append(rec)
        else:
            rec["nome"] = FIRME_PEZZO.get((len(g), n_pieghe), "sconosciuto")
            rec["blocco"], rec["colore"] = BLOCCHI.get(rec["nome"], ("?", "?"))
            pezzi.append(rec)
    for p in pezzi:
        p["fori"] = [f["firma"] or "non identificato"
                     for f in fori if f["host"] == p["idx"]]
    return pezzi, fori


def strip_frame(segs, groups):
    """Scarta la cornice dell'area stampabile (rettangolo 200x287 da 4 lati)."""
    keep = []
    for g in groups:
        w, h = dims_mm(segs, g)
        if len(g) <= 5 and w > 195 and h > 280:
            continue
        keep.append(g)
    return keep


# --------------------------------------------------------------------------
# comandi
# --------------------------------------------------------------------------

def inventario(path):
    pages, n_dichiarate, n_img = read_pages(path)
    print(f"=== {path} ===")
    print(f"pagine: {n_dichiarate}   tessere raster di sfondo: {n_img}")

    tot = {"segmenti": 0, "pezzi": 0, "fori": 0}
    peggiore = None
    fuori_misura = []
    per_colore = defaultdict(list)

    for pi, segs in enumerate(pages):
        pezzi, fori = classifica(segs)
        n_d = sum(1 for _, _, d in segs if d)
        tot["segmenti"] += len(segs)
        tot["pezzi"] += len(pezzi)
        tot["fori"] += len(fori)
        colori = sorted({p["colore"] for p in pezzi
                         if p["colore"] not in ("qualunque", "?")})
        print(f"\n-- pagina {pi+1}: {len(segs)} segmenti ({n_d} pieghe, "
              f"{len(segs)-n_d} tagli), {len(pezzi)} pezzi, {len(fori)} fori"
              + (f"   carta: {' + '.join(colori)}" if colori else ""))
        for p in sorted(pezzi, key=lambda p: -max(p["w"], p["h"])):
            fori_txt = ", ".join(sorted(set(p["fori"]))) if p["fori"] else "-"
            print(f"     {p['w']:6.1f} x {p['h']:6.1f} mm  {p['segmenti']:3d} segm"
                  f"  {p['pieghe']:2d} pieghe   {p['nome']:38s} fori: {fori_txt}")
            per_colore[p["colore"]].append((pi + 1, p["nome"]))
            grande = max(p["w"], p["h"])
            if grande > max(A4_UTILE_MM) or min(p["w"], p["h"]) > min(A4_UTILE_MM):
                fuori_misura.append((pi + 1, p["w"], p["h"], p["nome"]))
            if peggiore is None or grande > peggiore[0]:
                peggiore = (grande, p["w"], p["h"], pi + 1)

    print("\n--- raggruppamento per colore di cartoncino ---")
    for colore in sorted(per_colore):
        pagine = sorted({pg for pg, _ in per_colore[colore]})
        print(f"  {colore:12s} pagine {pagine}: "
              f"{', '.join(n for _, n in per_colore[colore])}")

    print("\n--- invarianti ---")
    ok = True
    for k, atteso in ATTESI.items():
        buono = tot[k] == atteso
        ok &= buono
        print(f"  {k:10s} atteso {atteso:4d}   trovato {tot[k]:4d}   "
              f"{'ok' if buono else 'DIVERSO: il layout ha perso o duplicato qualcosa'}")
    if fuori_misura:
        ok = False
        for pg, w, h, nome in fuori_misura:
            print(f"  FUORI MISURA pagina {pg}: {nome} {w:.1f} x {h:.1f} mm")
    elif peggiore:
        _, w, h, pg = peggiore
        print(f"  ingombro   pezzo piu' grande {w:.1f} x {h:.1f} mm (pagina {pg}) "
              f"contro {A4_UTILE_MM[0]:.0f} x {A4_UTILE_MM[1]:.0f} stampabili   ok")
    return ok


if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] != "inventario":
        print(__doc__)
        sys.exit(1)
    sys.exit(0 if inventario(sys.argv[2]) else 1)
