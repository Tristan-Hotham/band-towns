"""Shared paths and helpers for band-towns.

Raw inputs (read where they sit, never copied into the study):
  MusicBrainz JSON dumps, 2026-11-07, data CC0 (MetaBrainz Foundation):
    /home/claude/newdata/raw_new14/music/event.tar.xz   (mbdump/event, one JSON object per line)
    /home/claude/newdata/raw_new14/music/place.tar.xz   (mbdump/place, one JSON object per line)
  Wikidata UK settlements with population (CC0): /home/claude/newdata/raw_new8/uk_settlements.tsv
  UK local authority boundaries (ONS/OSNI, Open Government Licence): /home/claude/newdata/raw/geo/lad23_bgc.geojson
"""
import json, os, math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CODE = ROOT / "code"
SCRATCH = Path("/home/claude/scratch/band-towns")
RAW = Path("/home/claude/newdata/raw_new14/music")
EVENT_TAR = RAW / "event.tar.xz"
PLACE_TAR = RAW / "place.tar.xz"
SETTLEMENTS = Path("/home/claude/newdata/raw_new8/uk_settlements.tsv")
LAD = Path("/home/claude/newdata/raw/geo/lad23_bgc.geojson")
NE_LAND = Path("/home/claude/newdata/raw/geo")

SLUG = "band-towns"
TITLE = "Does anyone play your town? Concert geography from MusicBrainz"
REPO = "https://github.com/Tristan-Hotham/band-towns"
PAGE = "https://maps.tristanhotham.com/band-towns/"
FONTS = Path("/home/claude/ref/fonts")

# broad box round the UK used only as a first filter; the real test is the LAD polygons
UK_BOX = (-8.75, 49.8, 1.9, 60.95)


def in_box(lat, lon):
    return UK_BOX[0] <= lon <= UK_BOX[2] and UK_BOX[1] <= lat <= UK_BOX[3]


def hav_km(lat1, lon1, lat2, lon2):
    r = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def load_results():
    p = DATA / "results.json"
    return json.loads(p.read_text()) if p.exists() else {}


def save_results(d):
    (DATA / "results.json").write_text(json.dumps(d, indent=1, ensure_ascii=False))


def update_results(**kw):
    r = load_results()
    r.update(kw)
    save_results(r)
    return r

import re
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")
BYLINE = "Dr Tristan Hotham · Independent researcher · 2026"
KEEP = {"DOI", "DOI_URL", "BLOG_URL"}
BAD = ("—", "–", "--", "D" "SIT", "D" "CMS", "civil" " serv", "pre-" "registered")


def get(R, path):
    v = R
    # keys may contain spaces or dots inside names; try longest match first
    parts = path.split(".")
    i = 0
    while i < len(parts):
        for j in range(len(parts), i, -1):
            k = ".".join(parts[i:j])
            if isinstance(v, list) and k.isdigit() and int(k) < len(v):
                v = v[int(k)]; i = j; break
            if isinstance(v, dict) and k in v:
                v = v[k]; i = j; break
        else:
            raise KeyError(path)
    return v


def fmt(v, f=None):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(float(v)):,}"
    if f == "pc": return f"{round(float(v))}%"
    if f == "pc1": return f"{float(v):.1f}%"
    if f in ("f0", "f1", "f2", "f3"): return f"{float(v):.{f[1]}f}"
    raise ValueError(f)


def fill(t, R):
    return re.sub(r"\{\{([^{}|]+)(\|(\w+))?\}\}",
                  lambda m: m.group(0) if m.group(1) in KEEP or m.group(1).startswith(("IMG", "TABLE")) else fmt(get(R, m.group(1)), m.group(3)), t)
