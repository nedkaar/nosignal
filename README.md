# NO SIGNAL · archivio

The public archive of NO SIGNAL, the radio of Barrio's.
Italian page at `/`, English page at `/en/`.

## How it works

```
AzuraCast (Hetzner)                 GitHub                              Website
───────────────────                 ──────                              ───────
Podcasts: Voci, Musica,     every   scripts/build_archive.py            index.html  (IT)
Suoni, Radio Club     ───► hour ──► reads each podcast's RSS feed  ───► en/index.html (EN)
episodes + audio                    keeps only level 3/4 + credit       read archive.json
                                    writes site/archive.json
```

- **AzuraCast stays the only place recordings are managed.** Upload, publish, unpublish there.
- **The website updates itself every hour.** Nothing on the Hetzner server changes.
- **Audio plays from AzuraCast.** The ▶ button streams the episode file directly.
- **Two locks on consent.** An episode appears only if it is *published* in AzuraCast **and** its description says `Livello: 3` or `Livello: 4` **and** it has a `Crediti:` line.
- **If AzuraCast can't be reached**, the update stops and the site keeps its last good version.

## Files

| File | What it is | Who edits it |
|---|---|---|
| `sorgenti.json` | Settings (live stream, contacts, Radio Club meeting time), the list of feeds, and the collections (*raccolte*) with their titles and waiting rows | You, now and then |
| `scripts/build_archive.py` | Reads the feeds and writes `archive.json` | Nobody |
| `site/index.html`, `site/en/index.html` | The two pages | Only for text or design changes |
| `.github/workflows/archivio.yml` | Runs the update every hour and publishes the site | Nobody |

---

## One-time setup

### 1 · In AzuraCast: make four podcasts

On the NO SIGNAL station, under **Podcasts**, add one podcast per archive drawer:

| Podcast title | Goes into the archive as |
|---|---|
| NO SIGNAL · Voci | `voci` |
| NO SIGNAL · Musica | `musica` |
| NO SIGNAL · Suoni | `suoni` |
| NO SIGNAL · Radio Club | `voci` (its episodes form their own collections) |

Make sure the station's **public pages are enabled**, otherwise the feeds aren't public.

For each podcast, copy its **public RSS feed** link. AzuraCast shows it on the podcast's page. Open the link in a browser: you should see a page of XML starting with `<rss`. Menu labels change between AzuraCast versions; if you can't find it, look for "feed" or "RSS" on the podcast's public page.

### 2 · On GitHub: create the repository

1. Create a free account at github.com if you don't have one.
2. **New repository** → name it `nosignal` → **Public** → Create.
   (GitHub Pages is free for public repositories. Only the website code is public; recordings stay on AzuraCast.)
3. **Add file → Upload files** and drag in everything from this folder *except* the `.github` folder: `README.md`, `sorgenti.json`, the `scripts` folder and the `site` folder. Commit.
4. The `.github` folder is hidden on most computers, so add the workflow by hand:
   **Add file → Create new file**, type the name `.github/workflows/archivio.yml` (typing the slashes makes the folders), paste in the contents of `archivio.yml` from this folder, and commit.

### 3 · Turn on GitHub Pages

**Settings → Pages → Build and deployment → Source: GitHub Actions.**

### 4 · Point it at your feeds

Open `sorgenti.json` on GitHub, click the pencil, and paste each feed link into the matching `"url"`:

```json
"feed": [
  {"categoria": "voci",   "url": "https://radio.barrios.it/…/feed", "tipo_predefinito": "Trasmissione dal vivo"},
  {"categoria": "musica", "url": "https://radio.barrios.it/…/feed", "tipo_predefinito": "Trasmissione dal vivo"},
  {"categoria": "suoni",  "url": "https://radio.barrios.it/…/feed", "tipo_predefinito": "Banca sonora"},
  {"categoria": "voci",   "url": "https://radio.barrios.it/…/feed", "tipo_predefinito": "Puntata"}
]
```

A feed with an empty `"url"` is skipped, so you can start with one.

In the same file, fill in `impostazioni` when you have them:

- `diretta.stream`: the live stream URL (AzuraCast → station → Broadcasting / mount points, e.g. `…/listen/<station>/radio.mp3`). This shows the **Ascolta in diretta** button.
- `diretta.pagina`: the station's AzuraCast public page.
- `podcast.pagina`, `podcast.feed`: the Radio Club podcast's public page and feed (buttons under the Radio Club).
- `contatto`: who to contact to withdraw a recording.
- `partecipa.contatto`: how to get involved (step 1 of *Partecipa*).
- `partecipa.club_incontro`: when the Radio Club meets (on the membership card).

Commit. Saving the file starts an update straight away.

### 5 · Check it

Open the **Actions** tab. "Aggiorna archivio" should go green in a minute or two. Click the run, then **build → Build archive.json from AzuraCast** to see which episodes were added and which were skipped and why.

The site is at `https://<your-username>.github.io/nosignal/`, and the English page at `…/nosignal/en/`.

To update by hand at any time: **Actions → Aggiorna archivio → Run workflow**.

### 6 · Optional: your own address

To use e.g. `nosignal.barrios.it`:

1. **Settings → Pages → Custom domain**: type `nosignal.barrios.it`, Save.
2. At whoever manages the `barrios.it` DNS (the same place you added `radio.barrios.it`), add a **CNAME** record: name `nosignal`, value `<your-username>.github.io`.
3. When GitHub shows the domain as verified, tick **Enforce HTTPS**.

---

## Publishing a recording (for the crew)

*Per la redazione: come si pubblica una registrazione.*

1. Listen back. The people speaking choose the level. Only **3** or **4** go online.
2. In AzuraCast, open the right podcast (Voci, Musica, Suoni or Radio Club) and **add an episode**: upload the edited file and give it a title.
3. Start the **description** with these lines, exactly like this, one per line:

```
Raccolta: 00
N: 5
Spazio: Murales
Piano: Esterno · piano terra
Livello: 3
Crediti: Fatima, Anonimo
```

| Line | Meaning | Required |
|---|---|---|
| `Raccolta:` | Which broadcast or episode it belongs to, by number (`00` = the first broadcast). Must match a collection in `sorgenti.json`, otherwise a basic one is made | Yes |
| `N:` | Its place in the running order (`1A`, `2`, `5`…) | Yes |
| `Spazio:` | The room or place | Recommended |
| `Piano:` | Starts with `Primo piano`, `Piano terra`, `Seminterrato` or `Esterno`. Drives the floor display (1, T, S, EST). Anything after `·` shows as detail | Recommended |
| `Livello:` | `3` or `4`. Anything else and it **won't appear** | Yes |
| `Crediti:` | Names as people chose them, separated by commas: name, nickname or `Anonimo` | Yes |
| `Fonte:` | `MADEHERE`, `LIVE`, `PD`, `CC-BY`, `CC-BY-SA` | Optional |
| `Titolo EN:`, `Spazio EN:`, `Piano EN:` | English versions for the English page | Optional |

Leave an empty line after the header. Anything below it is a normal description.

4. **Publish** the episode in AzuraCast. It appears on the site at the next hourly update, or straight away with **Run workflow**.

## Withdrawing a recording

Unpublish or delete the episode in AzuraCast, or lower its `Livello:` below 3. It disappears from the site at the next update, at most an hour later. That keeps the 7-day promise with room to spare.

## Adding a new broadcast or episode

Add a collection to `"raccolte"` in `sorgenti.json`:

```json
{
  "numero": "01",
  "tipo": "Puntata",
  "titolo": "Via De Pretis e il piano casa",
  "titolo_en": "Via De Pretis and the housing plan",
  "data": "2026-11-12",
  "luogo": "Barrio's, Barona",
  "descrizione": "…",
  "descrizione_en": "…"
}
```

`tipo` is `Trasmissione dal vivo`, `Puntata` or `Banca sonora`. Episodes join it through `Raccolta: 01`.

**Waiting rows (`segnaposto`).** A collection can list rows that are recorded but don't have consent yet. They show greyed out as "In attesa del consenso", without names. When an episode with the same `N:` is published, it takes that row's place. The first broadcast already has its 11 rows set up this way.

**Level 2 (aired once, not available).** A level 2 recording went on air once and isn't kept, so it must **not** be uploaded or left published in AzuraCast: anything in a public feed can be downloaded. To show it on the page as greyed out and unavailable for relistening, add `"livello": 2` to its row under `segnaposto`:

```json
{"n": "2", "categoria": "voci", "spazio": "Ufficio", "piano": "Primo piano",
 "titolo": "Il lavoro del Barrio's, raccontato da chi lo fa", "livello": 2}
```

The page shows the title, the space and "2 · In onda una volta", with a hatched grey background and "Non disponibile: è andata in onda una volta e non è stata conservata". Names, audio and links never appear for these rows. If a level 2 episode does turn up in an AzuraCast feed, the update leaves it out and the log says to unpublish it.

**Levels 0 and 1 never appear.** They were never broadcast, so they leave no trace on the page. If a row under `segnaposto` is set to `"livello": 0` or `"livello": 1`, it is removed from the page. If such an episode is in AzuraCast, the log says to delete it.

## Troubleshooting

- **The run is red.** Open it. "FAILED" next to a feed means AzuraCast couldn't be reached or the link is wrong. The site keeps its last version until the next good run.
- **An episode doesn't appear.** Check the run's log for `skipped (no level 3/4 or no credit)`. Usually the description header has a typo, a missing `Livello:` or `Crediti:` line, or no empty line after the header.
- **Audio doesn't play.** Check that the episode plays on AzuraCast's own public page.
- **The hourly update stopped.** GitHub pauses scheduled runs in a public repository after 60 days without any commits, and sends you an email. Re-enable it in the Actions tab, or commit any small change.

## Why not on the Hetzner server?

It's possible, but AzuraCast already uses the server's web ports (80 and 443). A second website on the same machine means changing AzuraCast's web setup, and a mistake there takes the radio offline. GitHub Pages keeps the website completely separate: if it breaks, the radio keeps playing. The Hetzner server still does the important part, holding the audio and the episodes.
