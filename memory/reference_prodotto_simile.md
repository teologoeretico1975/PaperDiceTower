---
name: reference-prodotto-simile
description: Analisi strutturale dei due PDF in reference/ (papercraft di casette, versione blank e colorata) — cosa copiare e perché il loro modo di dipingere non si trasferisce alla torre
metadata:
  type: reference
---

In `reference/` ci sono due PDF di un prodotto commerciale simile (un gruppo di casette), nelle due versioni **blank** e **colorata** — la stessa struttura a due varianti pensata per PaperDiceTower. Materiale di studio di terzi: **non va ridistribuito**, e il repo va tenuto privato.

## Cosa sono, misurato

| | `cottages_blank` | `cottages_color` | PaperDiceTower |
|---|---|---|---|
| peso | 5,8 KB | 6,2 MB | 55 KB |
| pagine | 3 x A4 orizzontale | 3, formati **misti**: 1 US Letter + 2 A4 | 4 x A4 verticale |
| segmenti vettoriali | 249 | **116** | 636 |
| pezzi | **1 per pagina** | — | 13 |
| fori da ritagliare | **0** | 0 | 15 |
| immagini | 1 | 3 RGB a **300 dpi esatti** + 3 maschere alpha | 48 tessere bianche |

## Quattro conclusioni

**1. Le due versioni sono due produzioni separate, non un file con un layer da accendere.** Nella colorata restano 116 segmenti vettoriali contro 249 nella blank: le linee di taglio e piega sono **cotte dentro il raster**. Chi la fa disegna, appiattisce e consegna un bitmap. Fare entrambe le versioni significa impegnarsi a due produzioni e due manutenzioni.

**2. Il trucco da copiare: la `SMask`.** Ogni immagine porta un canale di trasparenza in DeviceGray, quindi il fondo resta bianco e **l'inchiostro va solo sui pezzi**. E' la risposta al problema di copertura: si puo' avere una skin dipinta a colori pieni senza allagare di inchiostro l'A4, che su 200 g/m2 imbarcherebbe il foglio.

**3. Non ritagliano le finestre, le disegnano.** Zero fori in tutto il cartamodello. Per questo il loro rischio sul taglio fine e' nullo, mentre il nostro e' una feritoia da 3,9 mm. La nostra scelta (fori passanti con velina dietro) resta valida, ma e' una scelta e ha un prezzo.

**4. Da non copiare: i formati di pagina misti.** Una pagina US Letter e due A4 nello stesso PDF costringono l'acquirente a cambiare impostazioni a meta' documento, ed e' il modo piu' facile di far stampare una pagina in scala sbagliata. Vedi il controllo di scala in `ISTRUZIONI.md`.

## Il punto importante, che corregge una conclusione precedente

Il loro cartamodello e' **una striscia di prospetti in piedi**, con l'erba in basso e i tetti in alto: il foglio *e'* un'immagine dell'oggetto montato. Per questo un illustratore, o un modello di immagini, puo' dipingerci sopra — ogni pezzo ha lo stesso "alto", allineato alla pagina.

Sul nostro cartamodello la verticale della torre punta a **0 gradi** sul corpo principale, **90** sul pezzo grande del fusto, **0** sulle due strisce (misurato con la PCA dei fori sul layout del 2026-08-07). Avevo concluso che questo rendesse impossibile dipingere sul foglio srotolato. **La conclusione era troppo forte: quelle rotazioni sono un artefatto dell'IMPAGINAZIONE, non della geometria** — sono state introdotte per far entrare i pezzi nelle pagine.

Quindi esiste una terza strada: **reimpaginare imponendo a tutti i pezzi lo stesso orientamento.** Con la verticale della torre concorde su ogni pezzo, il foglio ridiventa un'immagine dell'oggetto e dipingerci sopra funziona come funziona per loro. Il prezzo e' in **pagine**, non tecnico: le rotazioni servivano a impacchettare, e la striscia del corpo (180,8 x 250 mm) da sola riempie una pagina. Quanto costi si vede solo provando a disporli.

Resta valido tutto il resto di [[reference-decoro-registrato]], compreso che dipingere in 3D e lasciare che Pepakura srotoli la pittura evita il problema a monte.

**Come applicarla:** se si valuta una versione colorata, decidere prima *dove* si dipinge. Sul foglio 2D serve prima un layout a orientamento uniforme, e va messo in conto l'aumento di pagine. In 3D non serve, ma servono UV e materiali riattivati nell'esportatore.

Vedi [[project-panoramica]] e [[reference-etsy-posizionamento]].
