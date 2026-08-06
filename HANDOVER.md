# Handover — PaperDiceTower

Stato al 2026-08-06. Questo file è il punto di ingresso: orienta e rimanda ai documenti di dettaglio, senza duplicarli.

Repo: <https://github.com/teologoeretico1975/PaperDiceTower> · branch `main` · ultimo commit `6a74f56`

---

## 1. Cos'è

Torre dadi fantasy low-poly modellata in Blender, destinata a essere **unfoldata con Pepakura** e venduta come modello papercraft su Etsy. Due reference fornite dal committente: una torre dadi in legno tagliato al laser, poi una torre in resina con base rocciosa, finestre ad arco e muro perimetrale — è quest'ultima che ha guidato la forma attuale.

## 2. Dove siamo

**Geometria completa e validata. Unfold verificato in Pepakura. Manca la prova di assemblaggio da stampa.**

| oggetto | ruolo | facce | controlli |
|---|---|---|---|
| `Torre` | guscio | 158 | 0 non-manifold, 0 non planari, 135 bordi = attesi |
| `Muro` | cinta decorativa | 21 | 0 non-manifold, 0 non planari, 34 bordi = attesi |
| `Rampa` | cuneo interno | 5 | guscio chiuso, 0 bordi |

Verificato in Pepakura: scala 200 mm corretta, orientamento in piedi, pattern su **1 pagina A4**, nessun pezzo a scheggia, fori trattati come tagli e non come pieghe.

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
- **La vaschetta è un settore radiale a livello del suolo.** Radiale perché così i fianchi sono complanari; a livello del suolo perché sospesa i dadi restavano dentro.
- **`export/`**: gli `.obj` si versionano, ciò che Pepakura produce (`.pdo`, `.pdf`) è ignorato.

Il "perché" completo di ognuna è in `memory/reference_vincoli_papercraft.md` e `memory/project_panoramica.md`.

## 5. Prossimo passo

**Stampare e assemblare.** È l'unica prova che i controlli non possono dare: garantiscono una mesh valida, non un modello comodo da montare.

Da tenere d'occhio, in ordine di rischio, con il parametro da cambiare se cede:

| # | punto | misura | parametro |
|---|---|---|---|
| 1 | feritoie, le più fragili al taglio | 2,8 mm | `SLIT_HALF_W` |
| 2 | catena di triangoli del plinto: molte pieghe ravvicinate | — | `PLINTH_JAG` |
| 3 | varco di uscita, provare col d20 più grosso | 29 mm | `opening_top` in `add_dice_tray` |
| 4 | soglia dell'apertura del muro | 2,3 mm | `WALL_GATE["v_bottom"]` |

Vincolo di montaggio che nasce dalla geometria: **la rampa va incollata dentro prima di chiudere il fusto**, dopo non passa più dalla cima. Carta da almeno 160-200 g/m², altrimenti il fusto si imbarca.

## 6. Poi: materiali e texture

Non ancora iniziati, ed è ciò che separa il modello attuale (grigio da viewport) dall'aspetto della reference. Il committente ha giudicato la forma senza colore, che è stato uno svantaggio in tutte le revisioni.

Un problema già identificato e da risolvere lì: il pianale della vaschetta è **superficie interna** (l'interno della vaschetta è un unico spazio continuo con l'interno della torre, attraverso il varco), quindi con una skin la texture finirebbe sul lato che guarda il tavolo. Tre soluzioni con costi e controindicazioni: `checklist_export_pepakura.md`, sezione 3-bis.

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
