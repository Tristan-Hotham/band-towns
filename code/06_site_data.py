"""Data for the interactive page: data/site.json (authorities with decade counts, top venues and performers),
data/venues.geojson (documented venues, names only), data/la_outlines.geojson (simplified authority outlines)."""
import json
import numpy as np, pandas as pd, geopandas as gpd
from common import *

R = load_results()
A = pd.read_csv(DATA / "la_counts.csv")
E = pd.read_csv(DATA / "events_uk.csv", dtype={"main_ids": str, "main_names": str})
# privacy: publish performer names only for acts with 5+ documented UK events (touring, public acts);
# other performers keep their MusicBrainz id only (they may be private individuals)
E["main_ids"] = E.main_ids.fillna(""); E["main_names"] = E.main_names.fillna("")
ids = E.main_ids.str.split("|").explode(); ids = ids[ids != ""]
keep = set(ids.value_counts()[lambda v: v >= 5].index)
def mask(row):
    if not row.main_ids:
        return ""
    return "|".join(n if i in keep else "" for i, n in zip(row.main_ids.split("|"), row.main_names.split("|")))
E["main_names"] = [mask(r) for r in E[["main_ids", "main_names"]].itertuples()]
E.to_csv(DATA / "events_uk.csv", index=False)
print("performer names kept for", len(keep), "acts with 5+ UK events")
C = E[E.year.between(1960, 2025) & ~E.cancelled & (E.type == "Concert")].copy()
C["main_names"] = C.main_names.fillna("")
ARN = pd.read_csv(DATA / "arenas.csv")
tours = pd.read_csv(DATA / "tours.csv")
tk = set(zip(tours.artist_mbid, tours.year.astype(int)))
DEC = list(range(1960, 2030, 10))

# expected per decade: the authority's share of the M2 fit times the decade's UK total
share = A.fitted / A.fitted.sum()
las = []
for r, sh in zip(A.itertuples(), share):
    sub = C[C.lad == r.lad]
    tv = sub.place.value_counts().head(3)
    perf = sub.main_names.str.split("|").explode()
    perf = perf[(perf != "") & perf.notna()].value_counts().head(3)
    dec = [int(getattr(r, f"c{d}")) for d in DEC]
    exp = [round(float(sh * A[f"c{d}"].sum()), 2) for d in DEC]
    las.append({"c": r.lad, "n": r.la_name, "nat": r.nation, "lat": r.lat, "lon": r.lon, "pop": int(r.population),
                "k": int(r.concerts), "t": int(r.tour_dates), "e": round(float(r.fitted), 2), "ar": int(r.arena_la),
                "akm": round(float(r.arena_km)), "na": r.nearest_arena, "v": int(r.venues), "d": dec, "de": exp,
                "y0": int(sub.year.min()) if len(sub) else None, "y1": int(sub.year.max()) if len(sub) else None,
                "tv": [[k, int(v)] for k, v in tv.items()], "tp": [[k, int(v)] for k, v in perf.items()]})
site = {"las": las, "decades": DEC, "arenas": ARN[["arena", "city", "capacity", "opened", "lat", "lon", "la_name"]].to_dict("records"),
        "totals": [int(A[f"c{d}"].sum()) for d in DEC]}
(DATA / "site.json").write_text(json.dumps(site, ensure_ascii=False, separators=(",", ":")))

# venues (public venue names only, no addresses)
g = C.groupby("place_id").agg(name=("place", "first"), ptype=("place_type", "first"), lat=("lat", "first"), lon=("lon", "first"),
                               la=("la_name", "first"), n=("event_id", "size"), y0=("year", "min"), y1=("year", "max"),
                               how=("located_by", "first")).reset_index()
g = g[g.how == "place coordinates"]
feats = [{"type": "Feature", "geometry": {"type": "Point", "coordinates": [round(r.lon, 5), round(r.lat, 5)]},
          "properties": {"name": r.name, "type": r.ptype if isinstance(r.ptype, str) else "", "la": r.la, "n": int(r.n),
                         "y0": int(r.y0), "y1": int(r.y1), "mbid": r.place_id}} for r in g.itertuples()]
(DATA / "venues.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": feats}, ensure_ascii=False, separators=(",", ":")))

lad = gpd.read_file("/home/claude/newdata/raw/geo/lad23_bsc.geojson")[["LAD23CD", "LAD23NM", "geometry"]]
lad["geometry"] = lad.geometry.simplify(0.003, preserve_topology=True)
lad.to_file(DATA / "la_outlines.geojson", driver="GeoJSON", COORDINATE_PRECISION=4)
for f in ("site.json", "venues.geojson", "la_outlines.geojson"):
    print(f, (DATA / f).stat().st_size // 1024, "KB")
print("venues mapped", len(feats))
