#!/usr/bin/env python3
"""
Build archive.json for the NO SIGNAL archive page from AzuraCast podcast feeds.

    python scripts/build_archive.py sorgenti.json site/archive.json

Reads the settings, the list of feeds and the collections ("raccolte") from
sorgenti.json, downloads every feed, and keeps only episodes that are
published in AzuraCast AND carry consent level 3 or 4 AND a credit line.
Everything else is left out of the public page.

If any feed can't be downloaded, the script stops with an error, so the
website keeps its last good version instead of publishing a half-empty one.

Only the Python standard library is used.
"""
import datetime as dt
import email.utils
import html
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET

ITUNES = "{http://www.itunes.com/dtds/podcast-1.0.dtd}"
CONTENT = "{http://purl.org/rss/1.0/modules/content/}"

# Header lines the crew writes at the top of each episode description.
# Keys are matched without case or accents; values are free text.
KEYS = {
    "raccolta": "raccolta",
    "n": "n",
    "numero": "n",
    "spazio": "spazio",
    "spazio en": "spazio_en",
    "piano": "piano",
    "piano en": "piano_en",
    "livello": "livello",
    "crediti": "crediti",
    "credito": "crediti",
    "fonte": "fonte",
    "titolo en": "titolo_en",
    "title en": "titolo_en",
}
HEADER_RE = re.compile(r"^\s*([A-Za-zÀ-ÿ ]{1,20}?)\s*:\s*(.*?)\s*$")

FLOORS = [  # first match wins, compared against the start of the "Piano" line
    ("esterno", "EST"),
    ("seminterrato", "S"),
    ("piano terra", "T"),
    ("terra", "T"),
    ("primo piano", "1"),
    ("secondo piano", "2"),
]


def log(msg):
    print(msg, file=sys.stderr)


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "nosignal-archive/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def text_of(node, tag):
    el = node.find(tag)
    return (el.text or "").strip() if el is not None and el.text else ""


def plain(desc):
    """Turn an HTML-ish description into plain lines."""
    desc = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</li>", "\n", desc)
    desc = re.sub(r"<[^>]+>", "", desc)
    return html.unescape(desc).replace("\r", "")


def parse_header(desc):
    """Read 'Key: value' lines from the top of the description.
    Stops at the first line that isn't a known key; the rest is the note."""
    fields, note, in_header = {}, [], True
    for line in plain(desc).split("\n"):
        if in_header:
            if not line.strip():
                if fields:
                    in_header = False
                continue
            m = HEADER_RE.match(line)
            key = m and KEYS.get(m.group(1).strip().lower())
            if key:
                fields[key] = m.group(2)
                continue
            in_header = False
        note.append(line)
    fields["nota"] = "\n".join(note).strip()
    return fields


def duration(raw):
    """itunes:duration may be seconds or H:MM:SS / MM:SS. Return m:ss or h:mm:ss."""
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        parts = [int(float(p)) for p in raw.split(":")]
    except ValueError:
        return None
    secs = 0
    for p in parts:
        secs = secs * 60 + p
    if secs <= 0:
        return None
    h, rem = divmod(secs, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def floor_code(piano):
    p = (piano or "").strip().lower()
    for prefix, code in FLOORS:
        if p.startswith(prefix):
            return code
    return None


def natural(n):
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", str(n))]


def iso_date(pub):
    try:
        return email.utils.parsedate_to_datetime(pub).date().isoformat()
    except Exception:
        return None


def read_feed(feed):
    raw = fetch(feed["url"])
    root = ET.fromstring(raw)
    channel = root.find("channel")
    if channel is None:
        raise ValueError("not an RSS feed")
    out = []
    for item in channel.findall("item"):
        title = text_of(item, "title")
        desc = (text_of(item, CONTENT + "encoded") or text_of(item, "description")
                or text_of(item, ITUNES + "summary"))
        f = parse_header(desc)
        try:
            level = int(re.sub(r"\D", "", f.get("livello", "")) or 0)
        except ValueError:
            level = 0
        credits = [c.strip() for c in re.split(r"[,;]", f.get("crediti", "")) if c.strip()]
        problems = []
        if "livello" not in f:
            problems.append("no 'Livello:' line")
        elif level == 2:
            problems.append(
                "'Livello: 2' must not be published in AzuraCast: its audio is public in the feed. "
                "Unpublish or delete it there, and list it in sorgenti.json under 'segnaposto' with "
                "\"livello\": 2 so it shows greyed out")
        elif level in (0, 1) and "livello" in f and re.sub(r"\D", "", f["livello"]):
            problems.append(
                f"'Livello: {level}' recordings are never kept or shown. Delete it from AzuraCast")
        elif level not in (3, 4):
            problems.append(f"'Livello: {f['livello']}' is not 3 or 4")
        if not credits:
            problems.append("no 'Crediti:' line" if "crediti" not in f else "'Crediti:' is empty")
        if "raccolta" not in f:
            problems.append("no 'Raccolta:' line (it would go under 'Altre registrazioni')")
        if level not in (3, 4) or not credits:
            log(f"  skipped {title!r}: " + "; ".join(problems))
            continue
        if problems:
            log(f"  note {title!r}: " + "; ".join(problems))
        enc = item.find("enclosure")
        rec = {
            "n": f.get("n") or "",
            "categoria": feed["categoria"],
            "spazio": f.get("spazio") or "",
            "piano": f.get("piano") or "",
            "piano_codice": floor_code(f.get("piano")),
            "titolo": title,
            "crediti": credits,
            "livello": level,
            "durata": duration(text_of(item, ITUNES + "duration")),
            "audio": enc.get("url") if enc is not None else None,
            "link": text_of(item, "link") or None,
            "fonte": (f.get("fonte") or "").upper() or None,
            "data": iso_date(text_of(item, "pubDate")),
        }
        for k in ("titolo_en", "spazio_en", "piano_en"):
            if f.get(k):
                rec[k] = f[k]
        if f.get("nota"):
            rec["nota"] = f["nota"]
        out.append((f.get("raccolta", "").strip(), rec))
    return out


def main(src_path, out_path):
    with open(src_path, encoding="utf-8") as fh:
        src = json.load(fh)

    groups = {}
    for g in src.get("raccolte", []):
        g = dict(g)
        g["registrazioni"] = []
        groups[str(g["numero"])] = g

    failed = []
    for feed in src.get("feed", []):
        if not feed.get("url"):
            continue
        log(f"Reading {feed['categoria']}: {feed['url']}")
        try:
            items = read_feed(feed)
        except Exception as e:  # network or XML problem
            log(f"  FAILED: {e}")
            failed.append(feed["url"])
            continue
        for num, rec in items:
            key = num or feed.get("raccolta_predefinita") or "XX"
            if key not in groups:
                groups[key] = {
                    "numero": key,
                    "tipo": feed.get("tipo_predefinito", "Puntata"),
                    "titolo": "Altre registrazioni" if key == "XX" else f"Raccolta {key}",
                    "data": rec.get("data") or dt.date.today().isoformat(),
                    "luogo": "Barrio's, Barona",
                    "registrazioni": [],
                }
            groups[key]["registrazioni"].append(rec)
            log(f"  + {key} {rec['n']} {rec['titolo']!r}")

    if failed:
        log("Stopping: some feeds could not be read, so the site keeps its last version.")
        sys.exit(1)

    raccolte = []
    for key, g in groups.items():
        published = g["registrazioni"]
        have = {str(r["n"]) for r in published if r["n"]}
        waiting = []
        for p in g.pop("segnaposto", []) or []:
            if str(p.get("n")) in have:
                continue
            # Level 2 shows greyed out as "not available"; levels 0 and 1 don't show at all;
            # anything else waits for consent. Never names, audio or links: those are only for 3 and 4.
            lv = p.get("livello")
            if lv in (0, 1):
                continue
            p = dict(p, crediti=[], livello=2 if lv == 2 else None,
                     durata=None, audio=None, link=None)
            p.setdefault("piano_codice", floor_code(p.get("piano")))
            waiting.append(p)
        rows = published + waiting
        rows.sort(key=lambda r: natural(r.get("n") or "zz"))
        if not rows:
            continue
        g["registrazioni"] = rows
        raccolte.append(g)

    out = {
        "aggiornato": dt.datetime.now(dt.timezone.utc).isoformat(timespec="minutes"),
        "impostazioni": src.get("impostazioni", {}),
        "raccolte": raccolte,
    }
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    total = sum(len(g["registrazioni"]) for g in raccolte)
    log(f"Wrote {out_path}: {len(raccolte)} collections, {total} rows.")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: build_archive.py sorgenti.json site/archive.json")
    main(sys.argv[1], sys.argv[2])
