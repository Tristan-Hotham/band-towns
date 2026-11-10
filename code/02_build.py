"""Place every UK MusicBrainz event in a local authority; build the authority table.

Outputs:
  data/events_uk.csv     one row per UK event (MusicBrainz ids, type, date, place, authority, performers)
  data/venues_uk.csv     one row per UK place with at least one event (public venue names; no addresses)
  data/authorities.csv   one row per local authority: population, centroid, arena distance (counts are added in 03)
  data/arenas.csv        the 15 arenas of 10,000+ seats (Wikipedia list, retrieved 2026)
"""
import gzip, json, re, unicodedata
import numpy as np, pandas as pd, geopandas as gpd
from shapely.geometry import Point
from shapely.strtree import STRtree
from common import *

# ---- arenas: Wikipedia, List of indoor arenas in the United Kingdom (capacity 10,000+), retrieved 2026
ARENAS = [
    ("bp pulse LIVE (NEC)", "Birmingham", 15685, 1980, 52.4531, -1.7178),
    ("Utilita Arena Birmingham", "Birmingham", 15800, 1991, 52.4795, -1.9146),
    ("Coventry Building Society Arena", "Coventry", 10000, 2005, 52.4481, -1.4956),
    ("first direct arena", "Leeds", 13781, 2013, 53.8029, -1.5431),
    ("M&S Bank Arena", "Liverpool", 11000, 2008, 53.3966, -2.9907),
    ("The O2 Arena", "London", 20000, 2007, 51.5030, 0.0032),
    ("OVO Arena Wembley", "London", 12500, 1934, 51.5581, -0.2818),
    ("AO Arena", "Manchester", 23000, 1995, 53.4881, -2.2440),
    ("Co-op Live", "Manchester", 23500, 2024, 53.4856, -2.1987),
    ("Utilita Arena Newcastle", "Newcastle upon Tyne", 11400, 1995, 54.9640, -1.6211),
    ("Motorpoint Arena Nottingham", "Nottingham", 10000, 2000, 52.9497, -1.1360),
    ("Utilita Arena Sheffield", "Sheffield", 13600, 1991, 53.4019, -1.4195),
    ("SSE Arena", "Belfast", 10800, 1999, 54.6046, -5.9152),
    ("P&J Live", "Aberdeen", 15000, 2019, 57.2045, -2.1880),
    ("OVO Hydro", "Glasgow", 14300, 2013, 55.8600, -4.2862),
]


def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


lad = gpd.read_file(LAD).to_crs(27700)
lad["geometry"] = lad.geometry.buffer(0)
pop = pd.read_csv("/home/claude/studies/religion-map/data/uk_local_authorities.csv")[["code", "nation", "census_year", "all_residents"]]
lad = lad.merge(pop, left_on="LAD23CD", right_on="code", how="left")
assert lad.all_residents.notna().all(), lad[lad.all_residents.isna()]
tree = STRtree(list(lad.geometry))
from pyproj import Transformer
T = Transformer.from_crs(4326, 27700, always_xy=True)
TI = Transformer.from_crs(27700, 4326, always_xy=True)


def which_la(lat, lon):
    x, y = T.transform(lon, lat)
    p = Point(x, y)
    hits = tree.query(p, predicate="within")
    if len(hits):
        return int(hits[0]), 0.0
    i = int(tree.nearest(p))
    d = lad.geometry.iloc[i].distance(p) / 1000
    return (i, d) if d <= 2.0 else (None, d)


# ---- settlements for area-name geocoding (largest UK settlement of that name)
st = pd.read_csv(SETTLEMENTS, sep="\t")
st.columns = ["q", "name", "coord", "pop", "type"]
st["name"] = st.name.astype(str).str.replace(r'^"|"?@en$', "", regex=True)
xy = st.coord.str.extract(r"POINT\(([-\d.]+) ([-\d.]+)\)").astype(float)
st["lon"], st["lat"] = xy[0], xy[1]
st["pop"] = pd.to_numeric(st["pop"], errors="coerce").fillna(0)
st["k"] = st.name.map(norm)
best = st.sort_values("pop", ascending=False).drop_duplicates("k").set_index("k")
area_iso = json.loads((SCRATCH / "area_iso.json").read_text())


def gb_area(a):
    if not a:
        return False
    codes = a.get("iso") or area_iso.get(a.get("id"), [])
    return any(str(c).startswith("GB") for c in codes)


def geocode_area(a):
    k = norm(a.get("name") or "")
    if k in best.index and best.loc[k, "pop"] >= 1000:
        r = best.loc[k]
        return float(r.lat), float(r.lon)
    return None


rows, venues = [], {}
dropped = {"outside_uk_polygon": 0, "area_not_geocoded": 0}
for line in gzip.open(SCRATCH / "events_all.jsonl.gz", "rt"):
    e = json.loads(line)
    cand_box = any(p["lat"] is not None and in_box(p["lat"], p["lon"]) for p in e["places"])
    cand_gb = any(gb_area(p["area"]) for p in e["places"]) or any(gb_area(a) for a in e["areas"])
    if not (cand_box or cand_gb):
        continue
    place, how, lat, lon = None, None, None, None
    for p in e["places"]:
        if p["lat"] is not None and in_box(p["lat"], p["lon"]):
            place, lat, lon, how = p, p["lat"], p["lon"], "place coordinates"
            break
    if place is None:
        for p in e["places"]:
            if gb_area(p["area"]):
                g = geocode_area(p["area"])
                if g:
                    place, (lat, lon), how = p, g, "place area name"
                    break
        if place is None:
            for a in e["areas"]:
                if gb_area(a):
                    g = geocode_area(a)
                    if g:
                        (lat, lon), how = g, "event area name"
                        break
    if lat is None:
        dropped["area_not_geocoded"] += 1
        continue
    i, d = which_la(lat, lon)
    if i is None:
        dropped["outside_uk_polygon"] += 1
        continue
    mains = [a for a in e["artists"] if a["rel"] == "main performer"]
    supp = [a for a in e["artists"] if a["rel"] == "support act"]
    rows.append({"event_id": e["id"], "type": e["type"] or "", "cancelled": bool(e["cancelled"]),
                 "date": e["begin"] or "", "year": int(e["begin"][:4]) if (e["begin"] or "")[:4].isdigit() else None,
                 "place_id": place["id"] if place else "", "place": place["name"] if place else "",
                 "place_type": (place or {}).get("type") or "", "located_by": how,
                 "lad": lad.LAD23CD.iloc[i], "la_name": lad.LAD23NM.iloc[i], "lat": round(lat, 5), "lon": round(lon, 5),
                 "main_ids": "|".join(a["id"] for a in mains), "main_names": "|".join(a["name"] for a in mains),
                 "main_types": "|".join(a["atype"] or "" for a in mains), "n_support": len(supp), "n_artists": len(e["artists"])})
    if place and place["id"] not in venues:
        venues[place["id"]] = {"place_id": place["id"], "name": place["name"], "place_type": place.get("type") or "",
                               "lat": round(lat, 5), "lon": round(lon, 5), "located_by": how,
                               "lad": lad.LAD23CD.iloc[i], "la_name": lad.LAD23NM.iloc[i]}

ev = pd.DataFrame(rows)
ev["year"] = ev.year.astype("Int64")
ev.to_csv(DATA / "events_uk.csv", index=False)
pd.DataFrame(venues.values()).to_csv(DATA / "venues_uk.csv", index=False)
print("UK events", len(ev), dropped, ev.located_by.value_counts().to_dict())

# ---- authorities
cen = lad.geometry.representative_point()
lad["px"], lad["py"] = cen.x, cen.y
ll = [TI.transform(x, y) for x, y in zip(lad.px, lad.py)]
lad["lon"] = [round(a, 5) for a, b in ll]
lad["lat"] = [round(b, 5) for a, b in ll]
ar = pd.DataFrame(ARENAS, columns=["arena", "city", "capacity", "opened", "lat", "lon"])
axy = [T.transform(lo, la) for la, lo in zip(ar.lat, ar.lon)]
ar["x"], ar["y"] = [a for a, b in axy], [b for a, b in axy]
ar["lad"] = [lad.LAD23CD.iloc[which_la(a, b)[0]] for a, b in zip(ar.lat, ar.lon)]
ar["la_name"] = ar.lad.map(dict(zip(lad.LAD23CD, lad.LAD23NM)))
ar.drop(columns=["x", "y"]).to_csv(DATA / "arenas.csv", index=False)
D = np.sqrt((lad.px.values[:, None] - ar.x.values[None, :]) ** 2 + (lad.py.values[:, None] - ar.y.values[None, :]) ** 2) / 1000
lad["arena_km"] = D.min(1).round(2)
lad["nearest_arena"] = ar.arena.values[D.argmin(1)]
lad["arena_la"] = lad.LAD23CD.isin(set(ar.lad)).astype(int)
for dec in (1970, 1980, 1990, 2000, 2010, 2020):
    m = (ar.opened < dec + 10).values  # open at some point in the decade
    lad[f"arena_km_{dec}"] = D[:, m].min(1).round(2) if m.any() else np.nan
    lad[f"arena_la_{dec}"] = lad.LAD23CD.isin(set(ar.lad[m])).astype(int)
lon_x, lon_y = T.transform(-0.1276, 51.5072)
lad["london_km"] = (np.sqrt((lad.px - lon_x) ** 2 + (lad.py - lon_y) ** 2) / 1000).round(2)
lad["london"] = lad.LAD23CD.str.startswith("E09").astype(int)
lad["area_km2"] = (lad.geometry.area / 1e6).round(2)
out = lad[["LAD23CD", "LAD23NM", "nation", "census_year", "all_residents", "lat", "lon", "area_km2", "arena_la", "arena_km",
           "nearest_arena", "london", "london_km"] + [c for c in lad.columns if c.startswith(("arena_km_", "arena_la_"))]]
out = out.rename(columns={"LAD23CD": "lad", "LAD23NM": "la_name", "all_residents": "population"})
out.to_csv(DATA / "authorities.csv", index=False)
print("authorities", len(out), "arena LAs", out.arena_la.sum())
(SCRATCH / "build_info.json").write_text(json.dumps({"dropped": dropped, "n_uk": len(ev),
                                                      "located_by": ev.located_by.value_counts().to_dict()}))
