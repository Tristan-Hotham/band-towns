"""Assemble data/results.json: coverage numbers, descriptive counts and the model estimates (from 03).
Every number quoted anywhere in the study comes from this file."""
import gzip, json
import numpy as np, pandas as pd
from common import *

M = json.load(open(DATA / "results_models.json"))
A = pd.read_csv(DATA / "la_counts.csv")
E = pd.read_csv(DATA / "events_uk.csv", dtype={"main_ids": str})
T = pd.read_csv(DATA / "tours.csv")
B = json.loads((SCRATCH / "build_info.json").read_text())
P = json.loads((SCRATCH / "place_total.json").read_text())

# ---- worldwide coverage by year (from the full event dump)
world = {}
types = {}
n_world = n_place = n_coords = 0
for line in gzip.open(SCRATCH / "events_all.jsonl.gz", "rt"):
    e = json.loads(line)
    n_world += 1
    n_place += bool(e["places"])
    n_coords += any(p["lat"] is not None for p in e["places"])
    types[e["type"] or "untyped"] = types.get(e["type"] or "untyped", 0) + 1
    y = (e["begin"] or "")[:4]
    if y.isdigit():
        world[int(y)] = world.get(int(y), 0) + 1
ukc = E[(E.type == "Concert") & ~E.cancelled & E.year.notna()].groupby("year").size()
uka = E[E.year.notna()].groupby("year").size()
years = list(range(1960, 2026))
by_year = [{"year": y, "world_events": world.get(y, 0), "uk_events": int(uka.get(y, 0)), "uk_concerts": int(ukc.get(y, 0))} for y in years]
pd.DataFrame(by_year).to_csv(DATA / "coverage_by_year.csv", index=False)
yr = pd.DataFrame(by_year).set_index("year")
win = E[E.year.between(1960, 2025) & ~E.cancelled & (E.type == "Concert")]

R = {}
R["coverage"] = {
    "world_events": n_world, "world_with_place": n_place, "world_with_coords": n_coords,
    "world_concerts": types.get("Concert", 0), "world_festivals": types.get("Festival", 0),
    "places_total": P["places_total"],
    "uk_events": len(E), "uk_concerts_all_years": int(((E.type == "Concert") & ~E.cancelled).sum()),
    "uk_festivals": int((E.type == "Festival").sum()), "uk_untyped": int(E.type.isna().sum()),
    "uk_cancelled": int(E.cancelled.sum()),
    "uk_by_coords": B["located_by"].get("place coordinates", 0),
    "uk_by_area": B["located_by"].get("place area name", 0) + B["located_by"].get("event area name", 0),
    "uk_by_area_pc": 100 * (B["located_by"].get("place area name", 0) + B["located_by"].get("event area name", 0)) / len(E),
    "dropped_outside": B["dropped"]["outside_uk_polygon"], "dropped_not_geocoded": B["dropped"]["area_not_geocoded"],
    "concerts_window": len(win), "uk_share_world_pc": 100 * len(E) / n_world,
    "median_per_year_1980_2023": float(yr.loc[1980:2023, "uk_concerts"].median()),
    "min_per_year_1980_2023": int(yr.loc[1980:2023, "uk_concerts"].min()),
    "max_year": int(yr.uk_concerts.idxmax()), "max_year_n": int(yr.uk_concerts.max()),
    "y2025": int(yr.loc[2025, "uk_concerts"]), "y2024": int(yr.loc[2024, "uk_concerts"]),
    "y2019": int(yr.loc[2019, "uk_concerts"]), "y1998": int(yr.loc[1998, "uk_concerts"]),
    "venues": int(win.place_id.nunique()),
    "venues_mapped": int(win[win.located_by == "place coordinates"].place_id.nunique()),
}
top_perf_ids = None
perf = win.assign(a=win.main_names.fillna("").str.split("|")).explode("a")
perf = perf[perf.a != ""]
tp = perf.groupby("a").size().sort_values(ascending=False)
R["coverage"]["top10_perf_share_pc"] = 100 * win[win.main_names.fillna("").str.split("|").map(lambda l: bool(set(l) & set(tp.head(10).index)))].shape[0] / len(win)
R["coverage"]["no_main_performer"] = int((win.main_names.fillna("") == "").sum())
tv = win.groupby(["place", "la_name"]).size().sort_values(ascending=False)
R["top_venues"] = [{"venue": v, "la": l, "n": int(n)} for (v, l), n in tv.head(12).items()]
R["top_performers"] = [{"name": a, "n": int(n)} for a, n in tp.head(12).items()]
R["coverage"]["top_venue_share_pc"] = 100 * tv.head(10).sum() / len(win)

# ---- authorities
n = len(A)
R["la"] = {
    "n": n, "with_any": int((A.concerts > 0).sum()), "with_none": int((A.concerts == 0).sum()),
    "with_tour": int((A.tour_dates > 0).sum()),
    "concerts": int(A.concerts.sum()), "tour_dates": int(A.tour_dates.sum()), "other": int(A.other_concerts.sum()),
    "big_n": int((A.population >= 150000).sum()), "big_no_tour": int(((A.population >= 150000) & (A.tour_dates == 0)).sum()),
    "big_none": int(((A.population >= 150000) & (A.concerts == 0)).sum()),
    "pop_none_m": float(A.loc[A.concerts == 0, "population"].sum() / 1e6),
    "pop_no_tour_m": float(A.loc[A.tour_dates == 0, "population"].sum() / 1e6),
    "pop_total_m": float(A.population.sum() / 1e6),
}
R["la"]["pop_no_tour_pc"] = 100 * R["la"]["pop_no_tour_m"] / R["la"]["pop_total_m"]
R["la"]["pop_none_pc"] = 100 * R["la"]["pop_none_m"] / R["la"]["pop_total_m"]
st = A.sort_values("tour_dates", ascending=False)
R["la"]["tour_top10_share_pc"] = 100 * st.tour_dates.head(10).sum() / st.tour_dates.sum()
so = A.sort_values("other_concerts", ascending=False)
R["la"]["other_top10_share_pc"] = 100 * so.other_concerts.head(10).sum() / so.other_concerts.sum()
sc = A.sort_values("concerts", ascending=False)
R["la"]["all_top10_share_pc"] = 100 * sc.concerts.head(10).sum() / sc.concerts.sum()
R["la"]["arena_las"] = int(A.arena_la.sum())
R["la"]["arena_pop_pc"] = 100 * A.loc[A.arena_la == 1, "population"].sum() / A.population.sum()
R["la"]["arena_concerts_pc"] = 100 * A.loc[A.arena_la == 1, "concerts"].sum() / A.concerts.sum()
R["la"]["arena_tour_pc"] = 100 * A.loc[A.arena_la == 1, "tour_dates"].sum() / A.tour_dates.sum()
R["la"]["arena_other_pc"] = 100 * A.loc[A.arena_la == 1, "other_concerts"].sum() / A.other_concerts.sum()
A["per10k"] = A.concerts / A.population * 1e4
R["top_la"] = [{"la": r.la_name, "n": int(r.concerts), "tour": int(r.tour_dates), "pop": int(r.population), "fitted": float(r.fitted),
                "ratio": float(r.ratio)} for r in sc.head(15).itertuples()]
R["top_tour_la"] = [{"la": r.la_name, "n": int(r.tour_dates)} for r in st.head(12).itertuples()]
big = A[(A.population >= 150000)]
R["skipped"] = [{"la": r.la_name, "pop": int(r.population), "concerts": int(r.concerts)} for r in big[big.tour_dates == 0].sort_values("population", ascending=False).head(12).itertuples()]
R["silent_big"] = [{"la": r.la_name, "pop": int(r.population)} for r in big[big.concerts == 0].sort_values("population", ascending=False).head(12).itertuples()]
f5 = A[A.fitted >= 5]
R["over"] = [{"la": r.la_name, "n": int(r.concerts), "fitted": float(r.fitted), "ratio": float(r.ratio)} for r in f5.sort_values("ratio", ascending=False).head(10).itertuples()]
R["under"] = [{"la": r.la_name, "n": int(r.concerts), "fitted": float(r.fitted), "ratio": float(r.ratio)} for r in f5.assign(nf=-f5.fitted).sort_values(["ratio", "nf"]).head(10).itertuples()]
R["la"]["sig_over"] = int((A.p_high < 0.01).sum())
R["la"]["sig_under"] = int((A.p_low < 0.01).sum())
L = {r.la_name: r for r in A.itertuples()}
for k in ("Westminster", "Manchester", "Glasgow City", "North Norfolk", "Cambridge", "Birmingham", "Leeds", "Liverpool",
          "Hammersmith and Fulham", "City of Edinburgh", "Wiltshire", "Fife", "Cardiff", "Barnet", "Ribble Valley", "Brent",
          "Newcastle upon Tyne", "Gateshead", "Oxford"):
    r = L[k]
    R.setdefault("named", {})[k] = {"n": int(r.concerts), "tour": int(r.tour_dates), "pop": int(r.population), "fitted": float(r.fitted),
                                   "ratio": float(r.ratio), "venues": int(r.venues)}
nn = win[win.la_name == "North Norfolk"].place.value_counts()
R["named"]["North Norfolk"]["top_venue"] = nn.index[0]
R["named"]["North Norfolk"]["top_venue_n"] = int(nn.iloc[0])
wn = win[win.la_name == "North Norfolk"]
R["named"]["North Norfolk"]["y0"] = int(wn.year.min()); R["named"]["North Norfolk"]["y1"] = int(wn.year.max())
R["named"]["North Norfolk"]["pre1990_pc"] = 100 * (wn.year < 1990).mean()
# tours
T["year"] = T.year.astype(int)
R["tours"] = {"n": len(T), "artists": int(T.artist_mbid.nunique()), "dates": int(T.uk_dates.sum()),
              "median_dates": float(T.uk_dates.median()), "median_las": float(T.authorities.median()),
              "biggest": [{"artist": r.artist, "year": int(r.year), "dates": int(r.uk_dates), "las": int(r.authorities)} for r in T.head(8).itertuples()]}
# models
R["M1"] = M["M1"]; R["M2"] = M["M2"]; R["M3"] = M["M3"]; R["tour_only"] = M["tour_only"]; R["other_only"] = M["other_only"]
R["decades"] = M["decades"]; R["robust"] = M["robust"]; R["studios"] = M["studios"]; R["placebo"] = M["placebo"]
R["tables"] = M["tables"]
# convenience
R["x"] = {
    "elast": M["M1"]["b"], "elast_lo": M["M1"]["lo"], "elast_hi": M["M1"]["hi"],
    "double_pc": 100 * (2 ** M["M1"]["b"] - 1),
    "arena_rr": M["M2"]["arena_la"]["rr"], "arena_lo": M["M2"]["arena_la"]["rr_lo"], "arena_hi": M["M2"]["arena_la"]["rr_hi"],
    "dist_b": M["M2"]["logdist"]["b"], "dist_lo": M["M2"]["logdist"]["lo"], "dist_hi": M["M2"]["logdist"]["hi"], "dist_p": M["M2"]["logdist"]["p"],
    "dist_nolondon_b": float(np.log(M["robust"]["nolondon"]["logdist"]["rr"])),
    "dist_nolondon_lo": float(np.log(M["robust"]["nolondon"]["logdist"]["rr_lo"])),
    "dist_nolondon_hi": float(np.log(M["robust"]["nolondon"]["logdist"]["rr_hi"])),
    "dist_ldn_b": float(np.log(M["robust"]["london_dist"]["logdist"]["rr"])),
    "dist_ldn_lo": float(np.log(M["robust"]["london_dist"]["logdist"]["rr_lo"])),
    "dist_ldn_hi": float(np.log(M["robust"]["london_dist"]["logdist"]["rr_hi"])),
    "tour_arena_rr": M["M3"]["arena_la_x_tour"]["rr"], "tour_arena_lo": M["M3"]["arena_la_x_tour"]["rr_lo"], "tour_arena_hi": M["M3"]["arena_la_x_tour"]["rr_hi"],
    "tour_pop_b": M["M3"]["logpop_x_tour"]["b"], "tour_pop_lo": M["M3"]["logpop_x_tour"]["lo"], "tour_pop_hi": M["M3"]["logpop_x_tour"]["hi"], "tour_pop_p": M["M3"]["logpop_x_tour"]["p"],
    "elast_tour": M["M3"]["elast_tour"], "elast_other": M["M3"]["elast_other"],
    "arena_only_tour_rr": M["tour_only"]["arena_la"]["rr"], "arena_only_other_rr": M["other_only"]["arena_la"]["rr"],
    "placebo_share_pc": 100 * M["placebo"]["share_arena_ge_real"], "placebo_dist_share_pc": 100 * M["placebo"]["share_ge_real"],
    "e1970": M["decades"]["1970"]["elast"]["b"], "e2020": M["decades"]["2020"]["elast"]["b"], "e2000": M["decades"]["2000"]["elast"]["b"],
    "pseudo_r2": M["M2"]["pseudo_r2"],
}
# 2017 UK Live Music Census (Webster et al. 2018): at least N spaces where live music is played, March 2017
R["census_compare"] = {"glasgow_spaces_2017": 241, "newcastle_gateshead_spaces_2017": 137, "oxford_spaces_2017": 110,
                       "glasgow_mb": R["named"]["Glasgow City"]["venues"],
                       "ng_mb": R["named"]["Newcastle upon Tyne"]["venues"] + R["named"]["Gateshead"]["venues"],
                       "oxford_mb": R["named"]["Oxford"]["venues"]}
R["arenas_n"] = len(pd.read_csv(DATA / "arenas.csv"))
R["robust_n_noEn"] = int((A.nation != "England").sum())
R["placebo_dist_below_pc"] = 100 * (1 - M["placebo"]["share_ge_real"])
R["arena_ci_incl1"] = sorted(k for k, v in M["robust"].items() if v["arena_la"]["rr_lo"] <= 1)
cc = R["census_compare"]
R["census_ratio"] = {"glasgow": cc["glasgow_spaces_2017"] / cc["glasgow_mb"], "ng": cc["newcastle_gateshead_spaces_2017"] / cc["ng_mb"],
                     "oxford": cc["oxford_spaces_2017"] / cc["oxford_mb"]}
# sanity asserts
assert R["la"]["concerts"] == R["coverage"]["concerts_window"], (R["la"]["concerts"], R["coverage"]["concerts_window"])
assert R["la"]["tour_dates"] + R["la"]["other"] == R["la"]["concerts"]
assert R["x"]["arena_lo"] > 1 and R["x"]["elast_lo"] > 1
save_results(json.loads(json.dumps(R, default=float)))
print(json.dumps({k: R[k] for k in ("coverage", "la", "x", "tours")}, indent=1, default=float))
print(R["over"][:5], R["under"][:5], R["skipped"][:6], R["top_venues"][:6])
