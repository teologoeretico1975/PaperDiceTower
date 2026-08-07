"""Lettura, validazione e decorazione del cartamodello esportato da Pepakura.

Perche' esiste. Il PDF che Pepakura stampa e' l'ultimo anello della catena e per
molto tempo e' stato l'unico non verificato: `build_tower.py` controlla la mesh,
ma nessuno controllava che l'unfold uscisse con le misure giuste. Questo modulo
legge il PDF e misura i pezzi veri, senza aprire Pepakura e senza licenza.

Sulla macchina non ci sono librerie PDF, ma non servono: il PDF di Pepakura e'
vettoriale, i suoi content stream sono FlateDecode e contengono solo operatori di
path. Si decomprime con zlib e si interpreta il minimo indispensabile.

Due usi:

    python tools/pattern.py inventario export/PaperDiceTower7_300.pdf
    python tools/pattern.py pdf export/PaperDiceTower7_300.pdf

Il secondo riscrive il pattern in due varianti - solo linee e linee + decoro -
nelle coordinate di pagina originali. Ricopia i segmenti strutturali senza
ricalcolarli (scarto verificato: 0,000000 mm) e non ricopia le 48 tessere raster
di sfondo bianco, quindi l'uscita e' vettoriale pura e pesa 7 KB invece di 55.
"""
import math
import os
import re
import sys
import zlib
from collections import defaultdict

PT_MM = 25.4 / 72.0          # punti PDF -> millimetri
MM = 1.0 / PT_MM             # millimetri -> punti PDF
A4_PT = (595.27557, 841.88977)
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
    sia per ridisegnare il pattern con gli stessi stili.
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


def contours(segs, idxs):
    """Catene chiuse di un gruppo. Con le linguette la ricostruzione e'
    ambigua ai nodi di diramazione, quindi il risultato serve per le feature
    isolate (una finestra e' un anello semplice) e non per il contorno del
    pezzo, dove sbagliava."""
    adj = defaultdict(list)
    key = lambda p: (round(p[0], 2), round(p[1], 2))
    for i in idxs:
        adj[key(segs[i][0])].append((key(segs[i][1]), i))
        adj[key(segs[i][1])].append((key(segs[i][0]), i))
    seen, loops = set(), []
    for i in idxs:
        if i in seen:
            continue
        chain = [key(segs[i][0]), key(segs[i][1])]
        seen.add(i)
        while True:
            nxt = [(n, j) for n, j in adj[chain[-1]] if j not in seen]
            if not nxt:
                break
            n, j = nxt[0]
            seen.add(j)
            chain.append(n)
            if n == chain[0]:
                break
        if len(chain) >= 4:
            loops.append(chain)
    return loops


def poly_area(pts):
    a = 0.0
    for i in range(len(pts)):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % len(pts)]
        a += x0 * y1 - x1 * y0
    return a / 2.0


def _norm(v):
    n = math.hypot(*v) or 1.0
    return (v[0] / n, v[1] / n)


def offset_poly(pts, d):
    """Dilata un poligono di d, con giunto a mitra smussato sugli spigoli acuti.

    Lo smusso non e' un dettaglio: l'apice dell'arco a punta e' molto acuto, e
    la mitra pura produceva una scheggia lunga d/cos(mezzo angolo) che sull'apice
    diventava una lisca di parecchi millimetri.
    """
    pts = list(pts)
    if pts and pts[0] == pts[-1]:
        pts.pop()
    if poly_area(pts) < 0:
        pts.reverse()
    out = []
    for i in range(len(pts)):
        p0, p1, p2 = pts[i - 1], pts[i], pts[(i + 1) % len(pts)]
        e1 = _norm((p1[0] - p0[0], p1[1] - p0[1]))
        e2 = _norm((p2[0] - p1[0], p2[1] - p1[1]))
        n1, n2 = (e1[1], -e1[0]), (e2[1], -e2[0])      # normali uscenti (CCW)
        bis = _norm((n1[0] + n2[0], n1[1] + n2[1]))
        cos_half = bis[0] * n1[0] + bis[1] * n1[1]
        if cos_half < 0.55:
            out.append((p1[0] + n1[0] * d, p1[1] + n1[1] * d))
            out.append((p1[0] + n2[0] * d, p1[1] + n2[1] * d))
        else:
            out.append((p1[0] + bis[0] * d / cos_half,
                        p1[1] + bis[1] * d / cos_half))
    return out


def axis_from_windows(polys):
    """Verticale della torre, ricavata dalle finestre.

    Le pieghe non bastano: in una striscia quelle fra pannello e pannello e
    quelle delle linguette hanno lunghezza totale quasi identica (489 contro 459
    mm misurati sul foglio 1), quindi la direzione dominante e' ambigua. La
    finestra invece e' 42 x 11,8 mm, fortemente anisotropa, e la componente
    principale dei suoi vertici punta lungo la verticale della torre qualunque
    rotazione abbia il pezzo nel foglio.
    """
    acc = [0.0, 0.0]
    for poly in polys:
        n = len(poly)
        cx = sum(p[0] for p in poly) / n
        cy = sum(p[1] for p in poly) / n
        sxx = sum((p[0] - cx) ** 2 for p in poly) / n
        syy = sum((p[1] - cy) ** 2 for p in poly) / n
        sxy = sum((p[0] - cx) * (p[1] - cy) for p in poly) / n
        ang = 0.5 * math.atan2(2 * sxy, sxx - syy)
        v = (math.cos(ang), math.sin(ang))
        if acc[0] * v[0] + acc[1] * v[1] < 0:
            v = (-v[0], -v[1])
        acc[0] += v[0]
        acc[1] += v[1]
    return _norm(tuple(acc))


def _rot(p, c, s):
    return (p[0] * c - p[1] * s, p[0] * s + p[1] * c)


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
    "deflettore": (33.8, 68.1),
}


def match_firma(w, h, tol=2.0):
    lo, hi = min(w, h), max(w, h)
    for nome, (a, b) in FIRME.items():
        if abs(lo - a) <= tol and abs(hi - b) <= tol:
            return nome
    return None


def find_windows(segs, groups):
    """Contorni delle finestre ad arco, per firma dimensionale."""
    polys = []
    for g in groups:
        if match_firma(*dims_mm(segs, g)) != "finestra ad arco":
            continue
        cs = contours(segs, g)
        if not cs:
            continue
        w = list(cs[0])
        if w[0] == w[-1]:
            w.pop()
        if len(w) >= 4:
            polys.append(w)
    return polys


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
# decoro registrato sulle feature
# --------------------------------------------------------------------------

def decorate(segs):
    """Tracciati di decoro per una pagina, in punti PDF.

    Principio, ed e' la ragione per cui questa strada funziona dove il capitolo
    texture ha fallito: il decoro nasce dal contorno reale della feature, quindi
    sta dentro il pezzo per costruzione e non ha bisogno di essere ritagliato.
    Una tile ripetibile non puo' avere questa proprieta', perche' non sa dove si
    trova sul modello (vedi memory/reference_texture_tentativi.md).

    Corollario: dove non ci sono feature riconoscibili non si disegna niente.
    Oggi conosce solo la finestra ad arco, quindi decora una pagina su quattro.
    """
    groups = strip_frame(segs, cluster(segs))
    polys = find_windows(segs, groups)
    if not polys:
        return []

    ang = math.atan2(*reversed(axis_from_windows(polys)))
    ca, sa = math.cos(-ang), math.sin(-ang)
    out = []
    for wp in polys:
        # archivolto: due anelli concentrici piu' i giunti dei conci
        inner, outer = offset_poly(wp, 1.7 * MM), offset_poly(wp, 4.5 * MM)
        out.append(inner + [inner[0]])
        out.append(outer + [outer[0]])
        for i in range(min(len(inner), len(outer))):
            out.append([inner[i], outer[i]])

        c = (sum(p[0] for p in wp) / len(wp), sum(p[1] for p in wp) / len(wp))
        loc = [_rot((p[0] - c[0], p[1] - c[1]), ca, sa) for p in wp]
        lo_u, hi_u = min(p[0] for p in loc), max(p[0] for p in loc)
        span = hi_u - lo_u

        # Il segno della componente principale e' arbitrario, quindi da solo non
        # dice da che parte sta l'arco: la prima versione ha messo la soglia
        # sopra la punta e la chiave sotto la base. Il verso si ricava dalla
        # forma - l'estremita' ad arco e' a punta, quella della base e' larga.
        vext = lambda sel: max(abs(p[1]) for p in loc if sel(p[0])) * 2
        if vext(lambda u: u > hi_u - span * .25) > vext(lambda u: u < lo_u + span * .25):
            loc = [(-p[0], p[1]) for p in loc]
            lo_u, hi_u = -hi_u, -lo_u
            ang2 = ang + math.pi
        else:
            ang2 = ang
        cb, sb = math.cos(ang2), math.sin(ang2)
        back = lambda u, v: (c[0] + _rot((u, v), cb, sb)[0],
                             c[1] + _rot((u, v), cb, sb)[1])

        # soglia con aggetto oltre la luce, e chiave d'arco sull'apice
        hv = max(abs(p[1]) for p in loc) + 3.0 * MM
        out.append([back(lo_u - 1.6 * MM, -hv), back(lo_u - 4.4 * MM, -hv),
                    back(lo_u - 4.4 * MM, hv), back(lo_u - 1.6 * MM, hv),
                    back(lo_u - 1.6 * MM, -hv)])
        out.append([back(hi_u + 1.5 * MM, -1.6 * MM), back(hi_u + 4.7 * MM, -2.4 * MM),
                    back(hi_u + 4.7 * MM, 2.4 * MM), back(hi_u + 1.5 * MM, 1.6 * MM),
                    back(hi_u + 1.5 * MM, -1.6 * MM)])
    return out


# --------------------------------------------------------------------------
# scrittura del PDF
# --------------------------------------------------------------------------

def page_stream(segs, deco=None):
    """Content stream di una pagina: decoro sotto, struttura sopra."""
    L = []
    if deco:
        L.append("0.42 0.38 0.32 RG 0.55 w [] 0 d")
        for pts in deco:
            L.append(f"{pts[0][0]:.3f} {pts[0][1]:.3f} m")
            L += [f"{x:.3f} {y:.3f} l" for x, y in pts[1:]]
            L.append("S")

    def paths(items):
        for a, b in items:
            L.append(f"{a[0]:.3f} {a[1]:.3f} m {b[0]:.3f} {b[1]:.3f} l S")

    L.append("0 0 0 RG 0.65 w [] 0 d")
    paths([(a, b) for a, b, d in segs if not d])
    L.append("0.45 w [2.2 1.6] 0 d")
    paths([(a, b) for a, b, d in segs if d])
    return "\n".join(L).encode("latin1")


def build_pdf(streams, out_path):
    """PDF minimale: catalogo, albero pagine, una pagina per content stream."""
    n = len(streams)
    objs = {1: b"<< /Type /Catalog /Pages 2 0 R >>",
            2: (f"<< /Type /Pages /Kids [ "
                f"{' '.join(f'{3+i} 0 R' for i in range(n))} ] "
                f"/Count {n} >>").encode()}
    for i, body in enumerate(streams):
        objs[3 + i] = (f"<< /Type /Page /Parent 2 0 R /MediaBox "
                       f"[ 0 0 {A4_PT[0]} {A4_PT[1]} ] /Resources << >> "
                       f"/Contents {3+n+i} 0 R >>").encode()
        comp = zlib.compress(body, 9)
        objs[3 + n + i] = (b"<< /Length " + str(len(comp)).encode() +
                           b" /Filter /FlateDecode >>\nstream\n" + comp +
                           b"\nendstream")

    buf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = {}
    for num in sorted(objs):
        offsets[num] = len(buf)
        buf += f"{num} 0 obj\n".encode() + objs[num] + b"\nendobj\n"
    xref_at = len(buf)
    top = max(objs) + 1
    buf += f"xref\n0 {top}\n".encode() + b"0000000000 65535 f \n"
    for num in range(1, top):
        buf += f"{offsets.get(num, 0):010d} 00000 n \n".encode()
    buf += (f"trailer\n<< /Size {top} /Root 1 0 R >>\nstartxref\n"
            f"{xref_at}\n%%EOF\n").encode()
    open(out_path, "wb").write(buf)
    return len(buf)


# --------------------------------------------------------------------------
# comandi
# --------------------------------------------------------------------------

def inventario(path):
    pages, n_dichiarate, n_img = read_pages(path)
    print(f"=== {path} ===")
    print(f"pagine: {n_dichiarate}   tessere raster di sfondo: {n_img}")
    tot = 0
    peggiore = None
    for pi, segs in enumerate(pages):
        groups = strip_frame(segs, cluster(segs))
        n_d = sum(1 for _, _, d in segs if d)
        tot += len(segs)
        print(f"\n-- foglio {pi+1}: {len(segs)} segmenti "
              f"({n_d} pieghe, {len(segs)-n_d} tagli), {len(groups)} pezzi/fori")
        righe = []
        for g in groups:
            w, h = dims_mm(segs, g)
            righe.append((max(w, h), w, h, match_firma(w, h)))
        for _, w, h, nome in sorted(righe, reverse=True):
            entra = max(w, h) <= max(A4_UTILE_MM) and min(w, h) <= min(A4_UTILE_MM)
            tag = f"   <- {nome}" if nome else ("" if entra else "   <- NON ENTRA IN A4")
            print(f"     {w:7.1f} x {h:7.1f} mm{tag}")
            if peggiore is None or max(w, h) > peggiore[0]:
                peggiore = (max(w, h), w, h, pi + 1)
    print(f"\nsegmenti vettoriali totali: {tot}")
    if peggiore:
        _, w, h, pg = peggiore
        print(f"pezzo piu' grande: {w:.1f} x {h:.1f} mm (foglio {pg}) contro "
              f"{A4_UTILE_MM[0]:.0f} x {A4_UTILE_MM[1]:.0f} mm stampabili")


def genera_pdf(src, base=None):
    pages, _, _ = read_pages(src)
    base = base or os.path.splitext(src)[0]
    solo = build_pdf([page_stream(s) for s in pages], base + "_vettoriale.pdf")
    deco_per_pagina = [decorate(s) for s in pages]
    con = build_pdf([page_stream(s, d) for s, d in zip(pages, deco_per_pagina)],
                    base + "_decoro.pdf")
    for i, d in enumerate(deco_per_pagina):
        print(f"  pagina {i+1}: {len(pages[i])} segmenti strutturali, "
              f"{len(d)} tracciati di decoro")
    print(f"\n{base}_vettoriale.pdf   {solo/1024:.1f} KB")
    print(f"{base}_decoro.pdf        {con/1024:.1f} KB")
    verifica(src, base + "_vettoriale.pdf")


def verifica(src, gen):
    """Il controllo che conta: le coordinate non devono essere derivate, o la
    scala di stampa e' sbagliata."""
    a, _, _ = read_pages(src)
    b, _, _ = read_pages(gen)
    key = lambda S: sorted((round(p[0], 3), round(p[1], 3),
                            round(q[0], 3), round(q[1], 3), d) for p, q, d in S)
    ok = len(a) == len(b) and all(key(x) == key(y) for x, y in zip(a, b))
    print(f"verifica coordinate contro l'originale: "
          f"{'identiche' if ok else 'DIVERSE'} su {len(b)} pagine")
    return ok


if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] not in ("inventario", "pdf"):
        print(__doc__)
        sys.exit(1)
    if sys.argv[1] == "inventario":
        inventario(sys.argv[2])
    else:
        genera_pdf(sys.argv[2], *sys.argv[3:4])
