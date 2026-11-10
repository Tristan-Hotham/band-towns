"""Counts per authority and the pre-specified models (NOTES.md). Writes data/la_counts.csv, data/tours.csv,
data/results_models.json and the coverage numbers; 05_results.py assembles data/results.json."""
import gzip, json, warnings
import numpy as np, pandas as pd, statsmodels.api as sm
from common import *

warnings.filterwarnings("ignore")
Y0, Y1 = 1960, 2025
A = pd.read_csv(DATA / "authorities.csv")
E = pd.read_csv(DATA / "events_uk.csv", dtype={"main_ids": str, "main_names": str})
E["main_ids"] = E.main_ids.fillna("")
E["main_names"] = E.main_names.fillna("")
inwin = E.year.between(Y0, Y1) & ~E.cancelled
C = E[inwin & (E.type == "Concert")].copy()
print("concerts in window", len(C))

# ---- tours: artist-year with 5+ UK documented concerts as main performer
ex = C.assign(aid=C.main_ids.str.split("|"), aname=C.main_names.str.split("|")).explode(["aid", "aname"])
ex = ex[ex.aid != ""]
ay = ex.groupby(["aid", "year"]).agg(n=("event_id", "size"), name=("aname", "first"), las=("lad", "nunique")).reset_index()
tours = ay[ay.n >= 5].copy()
tour_keys = set(zip(tours.aid, tours.year))
ex["tour"] = [(a, y) in tour_keys for a, y in zip(ex.aid, ex.year)]
tour_events = set(ex.event_id[ex.tour])
C["tour"] = C.event_id.isin(tour_events)
tours = tours.sort_values(["n"], ascending=False)
tours.rename(columns={"aid": "artist_mbid", "name": "artist", "n": "uk_dates", "las": "authorities"}).to_csv(DATA / "tours.csv", index=False)
top_perf = ex.groupby(["aid", "aname"]).size().sort_values(ascending=False).head(10)


def counts(df, name):
    return df.groupby("lad").size().rename(name)


A = A.set_index("lad")
A["concerts"] = counts(C, "concerts")
A["tour_dates"] = counts(C[C.tour], "t")
A["other_concerts"] = counts(C[~C.tour], "o")
A["venues"] = C.groupby("lad").place_id.nunique()
A["performers"] = ex.groupby("lad").aid.nunique()
cap = C.assign(a1=C.main_ids.str.split("|").str[0])
cap = pd.concat([cap[cap.a1 == ""], cap[cap.a1 != ""].assign(k=lambda d: d.groupby(["lad", "a1"]).cumcount()).query("k < 3")])
A["concerts_cap3"] = counts(cap, "c")
top_ids = set(top_perf.index.get_level_values(0))
A["concerts_notop10"] = counts(C[~C.main_ids.str.split("|").map(lambda l: bool(set(l) & top_ids))], "c")
A["concerts_coords"] = counts(C[C.located_by == "place coordinates"], "c")
W = E[inwin & ((E.type.isin(["Concert", "Festival"])) | (E.type.isna() & (E.main_ids != "")))]
A["live_wide"] = counts(W, "c")
A["concerts_2000"] = counts(C[C.year >= 2000], "c")
for dec in range(1960, 2030, 10):
    A[f"c{dec}"] = counts(C[(C.year >= dec) & (C.year < dec + 10)], "c")
# studios (falsification): MusicBrainz places of type Studio with coordinates
import geopandas as gpd
pl = pd.DataFrame([json.loads(l) for l in gzip.open(SCRATCH / "places_uk.jsonl.gz", "rt")])
pl = pl[(pl.type == "Studio") & pl.lat.notna()]
lad = gpd.read_file(LAD)[["LAD23CD", "geometry"]]
g = gpd.GeoDataFrame(pl, geometry=gpd.points_from_xy(pl.lon, pl.lat), crs=4326)
j = gpd.sjoin(g, lad, predicate="within")
A["studios"] = j.groupby("LAD23CD").size()
A = A.fillna({c: 0 for c in A.columns if c not in ("nearest_arena",)})
for c in ["concerts", "tour_dates", "other_concerts", "venues", "performers", "concerts_cap3", "concerts_notop10",
          "concerts_coords", "live_wide", "concerts_2000", "studios"] + [f"c{d}" for d in range(1960, 2030, 10)]:
    A[c] = A[c].astype(int)

A["logpop"] = np.log(A.population)
A["logdist"] = np.log(A.arena_km.clip(lower=1))
A["loglondon"] = np.log(A.london_km.clip(lower=1))
for n in ("Scotland", "Wales", "Northern Ireland"):
    A["nat_" + n[:2]] = (A.nation == n).astype(int)
NAT = ["nat_Sc", "nat_Wa", "nat_No"]


def ppml(y, X, df, cluster=None):
    Xm = sm.add_constant(df[X].astype(float))
    Xm = Xm.loc[:, Xm.std() > 0].assign(const=1.0)
    m = sm.GLM(df[y].astype(float), Xm, family=sm.families.Poisson())
    r = m.fit(cov_type="cluster", cov_kwds={"groups": cluster}) if cluster is not None else m.fit(cov_type="HC1")
    return r


def coef(r, k, exp=False, n=None):
    b, s = r.params[k], r.bse[k]
    lo, hi = b - 1.96 * s, b + 1.96 * s
    d = {"b": b, "se": s, "lo": lo, "hi": hi, "p": float(r.pvalues[k]), "n": int(n if n is not None else r.nobs)}
    if exp:
        d.update(rr=np.exp(b), rr_lo=np.exp(lo), rr_hi=np.exp(hi))
    return d


RES = {}
M1 = ppml("concerts", ["logpop"] + NAT, A)
RES["M1"] = coef(M1, "logpop")
RES["M1"]["z_vs1"] = (M1.params["logpop"] - 1) / M1.bse["logpop"]
from scipy.stats import norm as N
RES["M1"]["p_vs1"] = float(2 * (1 - N.cdf(abs(RES["M1"]["z_vs1"]))))
MAIN = ["logpop", "arena_la", "logdist"] + NAT
M2 = ppml("concerts", MAIN, A)
RES["M2"] = {k: coef(M2, k, exp=True) for k in ("logpop", "arena_la", "logdist")}
RES["M2"]["pseudo_r2"] = 1 - M2.deviance / M2.null_deviance
A["fitted"] = M2.fittedvalues
A["ratio"] = A.concerts / A.fitted
from scipy.stats import poisson
A["p_high"] = poisson.sf(A.concerts - 1, A.fitted)
A["p_low"] = poisson.cdf(A.concerts, A.fitted)

# M3: stacked tour vs other
S = pd.concat([A.assign(y=A.tour_dates, tour=1), A.assign(y=A.other_concerts, tour=0)]).reset_index()
for v in ("logpop", "arena_la", "logdist"):
    S[v + "_x_tour"] = S[v] * S.tour
M3 = ppml("y", ["tour", "logpop", "arena_la", "logdist", "logpop_x_tour", "arena_la_x_tour", "logdist_x_tour"] + NAT, S, cluster=S.lad.values)
RES["M3"] = {k: coef(M3, k, exp=True, n=len(S)) for k in ("logpop", "logpop_x_tour", "arena_la", "arena_la_x_tour", "logdist", "logdist_x_tour")}
RES["M3"]["elast_tour"] = M3.params["logpop"] + M3.params["logpop_x_tour"]
RES["M3"]["elast_other"] = M3.params["logpop"]
for nm, y in (("tour_only", "tour_dates"), ("other_only", "other_concerts")):
    r = ppml(y, MAIN, A)
    RES[nm] = {k: coef(r, k, exp=True) for k in ("logpop", "arena_la", "logdist")}

# H4 by decade (exploratory): elasticity, top-10 share, arenas open by the decade
dec = {}
for d in range(1970, 2030, 10):
    col = f"c{d}"
    r = ppml(col, ["logpop"] + NAT, A)
    A2 = A.assign(arena_la=A[f"arena_la_{d}"], logdist=np.log(A[f"arena_km_{d}"].clip(lower=1)))
    r2 = ppml(col, MAIN, A2)
    srt = A[col].sort_values(ascending=False)
    dec[str(d)] = {"n": int(A[col].sum()), "elast": coef(r, "logpop"), "arena": coef(r2, "arena_la", exp=True),
                   "dist": coef(r2, "logdist", exp=True), "top10_share": float(srt.head(10).sum() / max(1, srt.sum())),
                   "las_with_any": int((A[col] > 0).sum()), "top": list(srt.head(5).index.map(A.la_name.to_dict()))}
RES["decades"] = dec

# robustness on M2
rob = {}
def add(key, label, y, X=MAIN, df=A, fam="ppml"):
    if fam == "nb":
        Xm = sm.add_constant(df[X].astype(float))
        r = sm.NegativeBinomial(df[y].astype(float), Xm).fit(disp=0, maxiter=200, cov_type="HC1")
    elif fam == "ols":
        Xm = sm.add_constant(df[X].astype(float))
        r = sm.OLS(np.log1p(df[y]), Xm).fit(cov_type="HC1")
    else:
        r = ppml(y, X, df)
    rob[key] = {"label": label, **{k: coef(r, k, exp=True) for k in ("logpop", "arena_la", "logdist")}}
add("nb", "Negative binomial", "concerts", fam="nb")
add("cap3", "Each artist capped at 3 concerts per authority", "concerts_cap3")
add("notop10", "Without the 10 most documented performers", "concerts_notop10")
add("coords", "Only events placed by venue coordinates", "concerts_coords")
add("wide", "Concerts, festivals and untyped events with a performer", "live_wide")
add("y2000", "2000 to 2025 only", "concerts_2000")
add("venues", "Outcome: distinct documented venues", "venues")
add("performers", "Outcome: distinct main performers", "performers")
for n in ("England", "Scotland", "Wales", "Northern Ireland"):
    sub = A[A.nation != n]
    add("no_" + n[:2], f"Without {n}", "concerts", MAIN[:3] + [x for x in NAT if x != "nat_" + n[:2]], sub)
add("nolondon", "Without the 33 London boroughs", "concerts", df=A[A.london == 0])
add("london_dist", "Adding log distance to central London", "concerts", MAIN + ["loglondon"])
add("ols", "OLS on log(1 + concerts)", "concerts", fam="ols")
RES["robust"] = rob

# falsification: studios
r = ppml("studios", MAIN, A)
RES["studios"] = {k: coef(r, k, exp=True) for k in ("logpop", "arena_la", "logdist")}
RES["studios"]["n_studios"] = int(A.studios.sum())

# placebo arenas: random authorities in the same population decile as each real arena authority
rng = np.random.default_rng(2026)
A["dec"] = pd.qcut(A.population, 10, labels=False)
real = A[A.arena_la == 1]
pool = {d: A[(A.arena_la == 0) & (A.dec == d)].index.values for d in range(10)}
lad_xy = A[["lat", "lon"]]
lat = np.radians(A.lat.values); lon = np.radians(A.lon.values)
def gc(i_idx):
    la2, lo2 = lat[i_idx][None, :], lon[i_idx][None, :]
    a = np.sin((lat[:, None] - la2) / 2) ** 2 + np.cos(lat[:, None]) * np.cos(la2) * np.sin((lon[:, None] - lo2) / 2) ** 2
    return (2 * 6371 * np.arcsin(np.sqrt(a))).min(1)
pos = {k: i for i, k in enumerate(A.index)}
pb = []
for it in range(500):
    pick = [rng.choice(pool[d]) for d in real.dec]
    P = A.assign(arena_la=A.index.isin(pick).astype(int), logdist=np.log(np.clip(gc(np.array([pos[k] for k in pick])), 1, None)))
    try:
        rr = ppml("concerts", MAIN, P)
        pb.append((rr.params["logdist"], rr.params["arena_la"]))
    except Exception:
        pass
pb = np.array(pb)
RES["placebo"] = {"draws": len(pb), "dist_mean": float(pb[:, 0].mean()), "dist_p05": float(np.percentile(pb[:, 0], 5)),
                  "dist_p95": float(np.percentile(pb[:, 0], 95)), "share_ge_real": float((pb[:, 0] >= M2.params["logdist"]).mean()),
                  "arena_mean_rr": float(np.exp(pb[:, 1]).mean()), "share_arena_ge_real": float((pb[:, 1] >= M2.params["arena_la"]).mean())}
np.save(SCRATCH / "placebo.npy", pb)

# full coefficient tables for the appendix
def table(r):
    return {k: {"b": float(r.params[k]), "se": float(r.bse[k]), "p": float(r.pvalues[k])} for k in r.params.index}
RES["tables"] = {"M1": table(M1), "M2": table(M2), "M3": table(M3)}
RES["n_la"] = len(A)
RES["top_perf"] = [{"name": n, "n": int(v)} for (i, n), v in top_perf.items()]
json.dump(RES, open(DATA / "results_models.json", "w"), indent=1, default=float)
keep = ["la_name", "nation", "population", "lat", "lon", "arena_la", "arena_km", "nearest_arena", "concerts", "tour_dates",
        "other_concerts", "venues", "performers", "studios", "fitted", "ratio", "p_high", "p_low"] + [f"c{d}" for d in range(1960, 2030, 10)]
A[keep].round(4).to_csv(DATA / "la_counts.csv")
print(json.dumps({k: RES[k] for k in ("M1", "M2")}, indent=1, default=float)[:3000])
print("M3", {k: (round(v["rr"], 3), round(v["rr_lo"], 3), round(v["rr_hi"], 3)) for k, v in RES["M3"].items() if isinstance(v, dict)})
print("placebo", RES["placebo"])
print("studios", {k: (round(v["rr"], 3), round(v["p"], 3)) for k, v in RES["studios"].items() if isinstance(v, dict)})
for k, v in rob.items():
    print(k, {kk: (round(vv["rr"], 2), round(vv["rr_lo"], 2), round(vv["rr_hi"], 2)) for kk, vv in v.items() if kk != "label"})
for d, v in dec.items():
    print(d, v["n"], round(v["elast"]["b"], 2), round(v["top10_share"], 2), v["las_with_any"], v["top"])
