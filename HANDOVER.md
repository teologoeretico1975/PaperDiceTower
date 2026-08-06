# Handover — PaperDiceTower

Stato al 2026-08-06. Questo file è il punto di ingresso: orienta e rimanda ai documenti di dettaglio, senza duplicarli.

Repo: <https://github.com/teologoeretico1975/PaperDiceTower> · branch `main` · ultimo commit `6a74f56`

---

## 1. Cos'è

Torre dadi fantasy low-poly modellata in Blender, destinata a essere **unfoldata con Pepakura** e venduta come modello papercraft su Etsy. Due reference fornite dal committente: una torre dadi in legno tagliato al laser, poi una torre in resina con base rocciosa, finestre ad arco e muro perimetrale — è quest'ultima che ha guidato la forma attuale.

## 2. Dove siamo

**Geometria completa e validata. Unfold verificato in Pepakura. Manca la prova di assemblaggio da stampa.**

**Versione di riferimento: 7 lati, stampata alta 300 mm** — `PaperDiceTower7.blend`, ed è il default dello script. `PaperDiceTower.blend` a 9 lati è conservato come variante, riproducibile con `build_all(sides=9)`.

| oggetto | ruolo | facce (riferimento, 7 lati) | facce (9 lati) |
|---|---|---|---|
| `Torre` | guscio | 123 | 158 |
| `Muro` | cinta decorativa | 16 | 21 |
| `Deflettori` | 4 strisce corrugate interne | 16 | 16 |
| `Rampa` | cuneo interno | 5 | 5 |

Su entrambe: 0 non-manifold, 0 facce non planari, bordi pari agli attesi, rampa dentro le pareti.

Perché 7 lati **e** 300 mm, e non uno dei due: ridurre le facce allarga solo i pannelli (16,0 → 20,2 mm), mentre feritoie e soglie restano invariate perché sono misure assolute. Solo la scala allarga anche quelle (feritoia 2,6 → 3,9 mm). Le due leve non sono alternative. Confronto completo nel README.

Verificato in Pepakura: scala 200 mm corretta, orientamento in piedi, nessun pezzo a scheggia, fori trattati come tagli e non come pieghe, nessuna sovrapposizione.

Pattern impaginato su **2 pagine A4**, PDF **vettoriale** (707 segmenti, 27 KB). Le 24 immagini raster che restano nel PDF sono le tessere di sfondo bianco del livello texture, vuoto: innocue.

## 3. Come si lavora

**Il modello non si modifica a mano.** `build_tower.py` è la fonte di verità: i parametri sono in cima al file, e lo script è idempotente (cancella e ricrea ciò che genera).

Serve Blender 5.1+ con l'add-on MCP di Blender Lab attivo — vedi `memory/reference_blender_mcp_addon.md` se la connessione non risponde.

```python
# dentro Blender
exec(open(r"E:\repos\PaperDiceTower\build_tower.py").read())   # rigenera + stampa il report
export_for_pepakura(target_height_mm=200)                       # scrive export/*.obj
```

Il report di verifica deve dare **0** su `non_manifold_edges`, `loose_verts`, `non_planar_faces`, e `boundary_edges` pari a `expected_boundary_edges`. Perché quei controlli e non altri: `checklist_export_pepakura.md`.

Perché uno script e non solo il `.blend`: il file Blender è un binario opaco in git, e modellare a incrementi rendeva ogni ritocco di proporzioni una ricostruzione manuale.

## 4. Decisioni da non ribaltare per sbaglio

Sono controintuitive e sono già costate un giro di correzioni ciascuna.

- **Finestre, feritoie e merlature sono fori e profili, non geometria in rilievo.** Una finestra incassata diventa 9 pezzi per finestra con pareti da 3 mm; i merli come blocchi separati diventano 7 scatoline da ~9×6 mm. Inassemblabili a mano. Il criterio non è il numero di facce ma **quanti pezzi separati diventa e quanto misurano davvero alla scala di stampa**.
- **La silhouette ha tratti cilindrici (tamburi) tra un restringimento e l'altro.** Senza, il profilo legge come un proiettile. Vale anche il rapporto: a 2,3:1 sembrava un macinapepe, ora è ~3,5:1.
- **Due merli adiacenti devono avere la stessa altezza.** Se differiscono, al loro spigolo comune nascono due bordi liberi sovrapposti invece di una piega.
- **La planarità va controllata, non solo la manifold-ness.** Una faccia svergolata non si piega combaciando, e il controllo di manifold-ness non la vede.
- **I deflettori rispondono a due criteri opposti, entrambi da misurare.** L'insieme non deve lasciare un canale verticale libero (o il dado cade senza toccare), ma ogni striscia da sola deve lasciar passare il dado più grande (o si intasa). Guardare solo la copertura porta a un imbuto. Le pieghe della corrugazione devono correre lungo la luce: trasversali darebbero un soffietto, cioè una molla.
- **Qualunque partizione interna del tubo rende non-manifold il guscio** (lo spigolo di attacco avrebbe 3 facce). Per questo rampa e deflettori sono oggetti separati, che nel papercraft è anche la norma.
- **La vaschetta è un settore radiale a livello del suolo.** Radiale perché così i fianchi sono complanari; a livello del suolo perché sospesa i dadi restavano dentro.
- **Si esporta un OBJ solo con tutti i sotto-assemblaggi, non uno per oggetto.** Pepakura occupa almeno una pagina per documento: `Muro` e `Rampa` riempiono l'8% e il 6% di un A4, quindi con file separati si stampano tre pagine di cui due quasi bianche. Lo spreco di carta è una dimensione di costo da misurare come le altre.
- **`export/`**: gli `.obj` si versionano, ciò che Pepakura produce (`.pdo`, `.pdf`) è ignorato.

Il "perché" completo di ognuna è in `memory/reference_vincoli_papercraft.md` e `memory/project_panoramica.md`.

## 5. Prossimo passo

**Stampare e assemblare.** È l'unica prova che i controlli non possono dare: garantiscono una mesh valida, non un modello comodo da montare.

Da tenere d'occhio, in ordine di rischio, con il parametro da cambiare se cede:

Misure alla scala di riferimento (7 lati, 300 mm):

| # | punto | misura | parametro |
|---|---|---|---|
| 1 | feritoie, le più fragili al taglio | 3,9 mm | `SLIT_HALF_W` |
| 2 | soglia dell'apertura del muro | 3,3 mm | `WALL_GATE["v_bottom"]` |
| 3 | catena di triangoli del plinto: pieghe ravvicinate | — | `PLINTH_JAG` |
| 4 | varco di uscita, provare col d20 più grosso | 41,5 mm | `opening_top` in `add_dice_tray` |

Il varco a 41,5 mm contro un d20 da ~20 mm ha ora ampio margine, quindi il rischio si è spostato sui due dettagli più sottili.

**Conviene raccogliere più correzioni e applicarle in un colpo solo** invece di iterare una alla volta: rigenerare il modello ed esportare costa due minuti, ma rifare l'impaginazione in Pepakura ne costa ~15 perché non è salvabile (vedi sotto).

Vincolo di montaggio che nasce dalla geometria: **la rampa va incollata dentro prima di chiudere il fusto**, dopo non passa più dalla cima.

Carta **200 g/m²**, e alla scala di riferimento si può salire fino a ~250: il vincolo superiore era la fragilità dei dettagli piccoli, che a 300 mm sono cresciuti di una volta e mezza (feritoie da 3,9 mm invece di 2,6). Il vincolo inferiore invece si è irrigidito: una torre di 30 cm ha più peso da reggere, quindi sotto i 180 g/m² il fusto flette. Incidere le pieghe prima di piegare.

**Attenzione a un vincolo operativo:** con la versione gratuita di Pepakura non si può salvare il `.pdo`. Ogni reimport dell'OBJ azzera impostazioni e impaginazione, che vanno rifatte a mano (~15 minuti). Quindi: **fare tutto in una sessione sola**. Per questo in `export/` sono versionati anche i PDF e gli screenshot dei layout: sono l'unico record di quel lavoro, e da lì si ricostruisce la disposizione invece di ripartire da zero. La ricetta dei passaggi è la sezione 6 di `checklist_export_pepakura.md`. Se il progetto va in vendita la licenza si ripaga subito.

## 6. Materiali e texture

**Fatti, e verificato che Pepakura li importi e li mostri sui pezzi 2D.** Due tile di muratura ripetibili generate da `make_textures.py`, applicate con UV che tengono i corsi allineati su tutta la torre. Dettagli nel README.

La grafica è volutamente **di base**: il rischio da chiudere per primo era che la versione gratuita di Pepakura scartasse la texture, e non valeva la pena investire prima di saperlo. Ora che passa, il passo che darebbe più profondità è cuocere l'occlusione ambientale nella texture (i rientri delle finestre e gli angoli più scuri).

**Pavimenti in vista: risolto.** Il pianale della vaschetta e il pavimento interno sono superfici interne (l'interno della vaschetta è un unico spazio continuo con quello della torre attraverso il varco), quindi la texture finiva sul lato che guarda il tavolo. `flip_visible_floors()` gira le facce orizzontali a quota zero, a costo di zero pezzi, e verificato in Pepakura. **Va eseguita come ultimo passo**: un `recalc_face_normals` successivo la annulla in silenzio. Vedi `checklist_export_pepakura.md`, sezione 3-bis, per il motivo per cui qualche incoerenza di avvolgimento è inevitabile su una superficie aperta.

La muratura è derivata da una **mappa diffuse fotoscansionata** in `textures/src/`, non versionata: se manca, `make_textures.py` ricade su una muratura procedurale. Va **verificata la licenza della sorgente** prima di vendere il kit. Due rimappature sono obbligatorie e non ovvie — schiarire (una texture per il 3D è pensata per essere illuminata: così com'era coprirebbe il 75% di inchiostro) e ridurre la crominanza (la gamma per canale trasformava la pietra grigia in arenaria dorata). Dettagli nel README.

**Due varianti stampabili**, non una: `muratura` (28% di inchiostro) e `tinte_piatte` (18%, da colorare a mano). Il costo di stampa era un vincolo reale — quasi metà di 4-5 fogli A4 — e invece di scegliere fra resa e costo si lascia la scelta a chi stampa. `export_all_variants()` produce entrambe: geometria e UV sono identiche, cambiano solo i materiali.

C'è quindi un documento in più, `ISTRUZIONI.md`, rivolto all'**acquirente** e non al progetto: montaggio, ordine dei pezzi e guida per colorare la versione a tinte piatte. Va tenuto distinto da README e da questo file, che parlano a chi sviluppa il modello.

## 7. Trappole di ambiente

- Il **viewport di Blender non si ridisegna** dopo modifiche via script: senza `tag_redraw()` + `view_layer.update()` gli screenshot mostrano lo stato precedente. Ci sono cascato due volte. La funzione `refresh_viewport()` lo fa.
- Il **`.gitignore` viene dal template Visual Studio** e ignora `*.obj` (là sono file oggetto compilati): gli export sparivano dai commit senza alcun errore. Dopo aver committato artefatti, verificare con `git ls-files export`. Dettagli: `memory/reference_gitignore_obj.md`.
- Insidie di `bmesh.ops` incontrate (extrude che lascia facce fantasma, wire edge orfani, liste con entità duplicate, normali nulle sulle facce appena create): `memory/reference_bmesh_lessons.md`.

## 8. Mappa dei file

| file | contenuto |
|---|---|
| `build_tower.py` | generatore parametrico — **fonte di verità** |
| `PaperDiceTower.blend` | scena Blender |
| `export/*.obj` | input per Pepakura, scalati a 200 mm |
| `README.md` | descrizione del modello e dello stato |
| `checklist_export_pepakura.md` | verifiche prima dell'unfold, scala, note di assemblaggio |
| `memory/MEMORY.md` | indice delle note di collaborazione |
| `screenshots/` | 31 catture, una per iterazione: utili per ricostruire il perché di una forma |

Nota: `checklist_export_pepakura.md` era arrivato da un altro progetto e conteneva indicazioni in conflitto (un limite di 30-60 facce, e il consiglio di rimuovere le facce interne — mentre qui il guscio **deve** restare cavo, è lo scivolo dei dadi). È stato riscritto per questo progetto.
