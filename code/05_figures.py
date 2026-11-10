"""Figures for the page (img/*.jpg), blog (release/blog/b_*.png, 1800 px wide), paper (release/paper/f_*.pdf) and header.png.
Light paper; more than expected = warm red, fewer = sea blue, grey midpoint."""
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib import font_manager as fm
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
import numpy as np, pandas as pd, geopandas as gpd
from PIL import Image
from common import *

for f in ("FrauncesVar.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf", "SourceSerif4-It.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf"):
    fm.fontManager.addfont(str(FONTS / f))
SERIF = "Source Serif 4"; DISP = fm.FontProperties(fname=str(FONTS / "FrauncesVar.ttf")).get_name(); MONO = "IBM Plex Mono"
PAPER, INK, MUT, RULE = "#F6EED8", "#2B2119", "#6E604E", "#D9C9A3"
HOT, COOL, GREY = "#B4442E", "#2F6A9E", "#9C9384"
CMAP = LinearSegmentedColormap.from_list("g", ["#1F4F7A", "#6F9CC4", "#D8D1C3", "#E3A08A", "#B4442E", "#6E1F12"])
plt.rcParams.update({"font.family": SERIF, "font.size": 12, "axes.edgecolor": MUT, "axes.labelcolor": INK, "xtick.color": MUT,
                     "ytick.color": MUT, "axes.facecolor": PAPER, "figure.facecolor": PAPER, "axes.unicode_minus": False,
                     "pdf.fonttype": 42, "axes.spines.top": False, "axes.spines.right": False})
HALO = [pe.withStroke(linewidth=3, foreground=PAPER)]
R = load_results()
REL = ROOT / "release"; BLOG = REL / "blog"; PAPD = REL / "paper"; IMG = ROOT / "img"
for d in (BLOG, PAPD, IMG, SCRATCH):
    os.makedirs(d, exist_ok=True)
SRC = ("Data: MusicBrainz event and place dumps, 2026 (CC0, MetaBrainz Foundation); census populations (ONS, NRS, NISRA, OGL)\n"
       "Documented concerts 1960 to 2025 · maps.tristanhotham.com/band-towns")
A = pd.read_csv(DATA / "la_counts.csv")
ARN = pd.read_csv(DATA / "arenas.csv")


def out(fig, name, page=True, blog=True, paper=True):
    if paper:
        fig.savefig(PAPD / f"f_{name}.pdf", facecolor=fig.get_facecolor())
    p = SCRATCH / f"{name}.png"
    fig.savefig(p, dpi=220, facecolor=fig.get_facecolor()); plt.close(fig)
    im = Image.open(p).convert("RGB")
    if page:
        w = min(1500, im.size[0]); im.resize((w, round(im.size[1] * w / im.size[0])), Image.LANCZOS).save(IMG / f"{name}.jpg", quality=85, optimize=True)
    if blog:
        im.resize((1800, round(im.size[1] * 1800 / im.size[0])), Image.LANCZOS).save(BLOG / f"b_{name}.png", optimize=True)
    os.remove(p)


def title(fig, t, sub, y=0.965):
    fig.text(0.04, y, t, fontsize=21, fontweight="bold", family=DISP, color=INK, va="top")
    fig.text(0.04, y - 0.058, sub, fontsize=12, color=MUT, va="top", linespacing=1.35)


def foot(fig, s=SRC):
    fig.text(0.04, 0.012, s, fontsize=8, family=MONO, color=MUT, va="bottom", linespacing=1.4)


C = R["coverage"]; L = R["la"]; X = R["x"]

# 1. coverage: documented UK concerts per year
cy = pd.read_csv(DATA / "coverage_by_year.csv")
fig = plt.figure(figsize=(10, 5.6))
ax = fig.add_axes([0.08, 0.15, 0.88, 0.62])
ax.bar(cy.year, cy.uk_concerts, color=HOT, width=0.78)
ax.set_xlim(1959, 2026); ax.grid(axis="y", color=RULE, lw=0.6); ax.set_axisbelow(True)
ax.set_ylabel("documented concerts in the UK")
for y, lab in ((1998, "1998: several tours\nentered date by date"), (2024, "2024 to 2025:\nrecent tours entered")):
    v = int(cy.set_index("year").uk_concerts[y])
    ax.annotate(lab, (y, v), xytext=(y - (17 if y == 2024 else 13), v * 0.97), fontsize=10, color=INK, va="top",
                arrowprops=dict(arrowstyle="-", color=MUT, lw=0.8), path_effects=HALO)
title(fig, "A thin, lumpy record", f"Concerts in the UK recorded in MusicBrainz, by year: a median of {C['median_per_year_1980_2023']:.0f} a year from 1980 to 2023. In 2017 a\nlive music census found at least 241 spaces for live music in Glasgow alone.")
foot(fig)
out(fig, "coverage")

# 2. map of observed vs expected
lad = gpd.read_file(LAD).to_crs(27700)
lad = lad.merge(A[["lad", "concerts", "fitted", "ratio"]], left_on="LAD23CD", right_on="lad")
lad["lr"] = np.log2((lad.concerts + 0.5) / (lad.fitted + 0.5)).clip(-4, 4)
fig = plt.figure(figsize=(8.6, 11))
ax = fig.add_axes([0.0, 0.05, 1.0, 0.83]); ax.set_axis_off()
lad.plot(ax=ax, column="lr", cmap=CMAP, norm=TwoSlopeNorm(0, -4, 4), edgecolor="#F6EED8", linewidth=0.25)
ar = gpd.GeoDataFrame(ARN, geometry=gpd.points_from_xy(ARN.lon, ARN.lat), crs=4326).to_crs(27700)
ax.scatter(ar.geometry.x, ar.geometry.y, marker="^", s=46, color=INK, edgecolor=PAPER, linewidth=0.8, zorder=5)
ax.set_xlim(-30000, 680000); ax.set_ylim(-70000, 1060000)
# labels on sea only
for nm, x, y, tx, ty in (("North Norfolk", 615000, 338000, 612000, 470000), ("Westminster", 529000, 179000, 610000, 60000),
                         ("Fife", 340000, 708000, 560000, 740000), ("Wiltshire", 400000, 160000, 470000, -45000)):
    r = A.set_index("la_name").loc[nm]
    ax.annotate(f"{nm}\n{int(r.concerts)} documented, {r.fitted:.0f} expected", (x, y), xytext=(tx, ty), fontsize=9.5, color=INK,
                ha="center", arrowprops=dict(arrowstyle="-", color=INK, lw=0.7), path_effects=HALO)
cax = fig.add_axes([0.05, 0.385, 0.19, 0.014])
sm_ = plt.cm.ScalarMappable(cmap=CMAP, norm=TwoSlopeNorm(0, -4, 4)); cb = fig.colorbar(sm_, cax=cax, orientation="horizontal")
cb.set_ticks([-4, 0, 4]); cb.set_ticklabels(["16x fewer", "as expected", "16x more"]); cb.ax.tick_params(labelsize=8.5)
fig.text(0.05, 0.407, "Documented concerts against\nexpectation (population,\nnation and arenas)", fontsize=9.5, color=INK, va="bottom")
fig.text(0.05, 0.335, "▲ indoor arena of\n   10,000+ seats", fontsize=9.5, color=INK, va="top")
title(fig, "Who the record remembers", f"Each UK local authority: concerts documented in MusicBrainz, 1960 to 2025, against the\nnumber expected from its population, nation and arenas. {L['with_none']} of {L['n']} authorities have none.", y=0.975)
foot(fig)
out(fig, "map")

# 3. scaling scatter
fig = plt.figure(figsize=(10, 6.4))
ax = fig.add_axes([0.09, 0.18, 0.87, 0.6])
y = A.concerts + 1
na = A[A.arena_la == 0]; ya = A[A.arena_la == 1]
ax.scatter(na.population, na.concerts + 1, s=18, color=GREY, alpha=0.75, edgecolor="none", label="other authorities")
ax.scatter(ya.population, ya.concerts + 1, s=46, color=HOT, edgecolor=INK, lw=0.6, label="has a 10,000+ seat arena", zorder=4)
ax.set_xscale("log"); ax.set_yscale("log")
xs = np.geomspace(A.population.min(), A.population.max(), 50)
k = A.concerts.sum() / (A.population ** X["elast"]).sum()
yy = k * xs ** X["elast"]; mm = yy >= 0.9
ax.plot(xs[mm], yy[mm], color=INK, lw=1.6, ls="--")
ax.text(2600, 40, f"dashed line, slope {X['elast']:.2f}: double the people,\n{X['double_pc']:.0f}% more documented gigs", fontsize=10, color=INK, path_effects=HALO)
for nm in ("North Norfolk", "Westminster", "Cambridge", "Wiltshire", "Birmingham", "Manchester"):
    r = A.set_index("la_name").loc[nm]
    off = {"Wiltshire": (1.06, 0.74), "Birmingham": (0.62, 0.55), "Manchester": (1.06, 1.12), "Westminster": (0.52, 1.12), "North Norfolk": (0.62, 1.2), "Cambridge": (0.7, 1.2)}.get(nm, (1.08, 1.15))
    ax.text(r.population * off[0], (r.concerts + 1) * off[1], nm, fontsize=9.5, color=INK, path_effects=HALO)
ax.set_xlabel("population (census 2021/2022, log scale)"); ax.set_ylabel("documented concerts + 1 (log scale)")
ax.grid(color=RULE, lw=0.5); ax.legend(frameon=False, loc="upper left", fontsize=10)
ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
title(fig, "Big places are remembered more than their size", f"Each dot is one of {L['n']} UK local authorities. Documented concerts rise faster than population\n(elasticity {X['elast']:.2f}, 95% CI {X['elast_lo']:.2f} to {X['elast_hi']:.2f}).")
foot(fig)
out(fig, "scaling")

# 4. arena shares
fig = plt.figure(figsize=(10, 5.2))
ax = fig.add_axes([0.30, 0.2, 0.64, 0.54])
labs = ["Population", "Documented concerts", "Tour dates", "Other concerts"]
vals = [L["arena_pop_pc"], L["arena_concerts_pc"], L["arena_tour_pc"], L["arena_other_pc"]]
cols = [GREY, HOT, "#6E1F12", "#E3A08A"]
ax.barh(range(4)[::-1], vals, color=cols, height=0.62)
for i, v in enumerate(vals):
    ax.text(v + 1, 3 - i, f"{v:.0f}%", va="center", fontsize=12, color=INK)
ax.set_yticks(range(4)[::-1]); ax.set_yticklabels(labs, fontsize=12); ax.set_xlim(0, 65); ax.set_xlabel("share held by the 14 authorities with an arena (%)")
ax.grid(axis="x", color=RULE, lw=0.5); ax.set_axisbelow(True)
title(fig, "The arena circuit", f"The {L['arena_las']} authorities with an indoor arena of 10,000+ seats hold {L['arena_pop_pc']:.0f}% of the UK's people but\n{L['arena_tour_pc']:.0f}% of documented tour dates (an act's year with 5 or more UK dates).")
foot(fig)
out(fig, "arenas")

# 5. skipped big authorities
sk = pd.DataFrame(R["skipped"])
fig = plt.figure(figsize=(10, 6.2))
ax = fig.add_axes([0.30, 0.18, 0.64, 0.6])
ax.barh(range(len(sk))[::-1], sk["pop"] / 1000, color=COOL, height=0.66)
for i, r in sk.iterrows():
    ax.text(r["pop"] / 1000 + 6, len(sk) - 1 - i, f"{r['concerts']} documented gig{'s' if r['concerts'] != 1 else ''}", va="center", fontsize=10, color=INK)
ax.set_yticks(range(len(sk))[::-1]); ax.set_yticklabels(sk.la, fontsize=11)
ax.set_xlabel("population (thousands)"); ax.set_xlim(0, 640); ax.grid(axis="x", color=RULE, lw=0.5); ax.set_axisbelow(True)
title(fig, "Big places no tour has been recorded in", f"{L['big_no_tour']} of the {L['big_n']} UK local authorities with 150,000 or more people have no documented tour date,\n1960 to 2025. The largest twelve:")
foot(fig)
out(fig, "skipped")

# 6. decades
D = R["decades"]
fig = plt.figure(figsize=(10, 5.4))
ax = fig.add_axes([0.09, 0.22, 0.86, 0.53])
ds = sorted(D)
xs_ = np.arange(len(ds))
e = [D[d]["elast"]["b"] for d in ds]; lo = [D[d]["elast"]["lo"] for d in ds]; hi = [D[d]["elast"]["hi"] for d in ds]
ax.errorbar(xs_, e, yerr=[np.array(e) - lo, np.array(hi) - e], fmt="o", color=HOT, ms=8, capsize=4, lw=1.6)
ax.axhline(1, color=MUT, lw=1, ls=":"); ax.text(len(ds) - 0.55, 1.04, "in proportion to population", fontsize=9.5, color=MUT, ha="right")
ax.set_xticks(xs_); ax.set_xticklabels([f"{d}s\n{D[d]['n']:,} gigs" for d in ds], fontsize=10.5)
ax.set_ylabel("population elasticity (95% CI)"); ax.grid(axis="y", color=RULE, lw=0.5)
title(fig, "Has the record grown more big-city?", f"How steeply documented concerts rise with population, decade by decade (exploratory). From\n{X['e1970']:.2f} in the 1970s (very uncertain) to {X['e2020']:.2f} in the 2020s; every decade since the 2000s is above 1.")
foot(fig)
out(fig, "decades")

# 7. robustness forest (arena and distance)
rb = R["robust"]
rows = [("Main estimate", R["M2"])] + [(v["label"], v) for v in rb.values()]
fig = plt.figure(figsize=(10, 7.6))
for j, (k, lab) in enumerate((("arena_la", "Arena in the authority (rate ratio)"), ("logdist", "Per doubling... see note"))):
    ax = fig.add_axes([0.36 + j * 0.33, 0.1, 0.28, 0.7])
    for i, (nm, v) in enumerate(rows):
        c = v[k]
        rr, a_, b_ = (c["rr"], c["rr_lo"], c["rr_hi"])
        ax.plot([a_, b_], [len(rows) - 1 - i] * 2, color=INK if i else HOT, lw=1.4)
        ax.plot(rr, len(rows) - 1 - i, "o", color=HOT if i == 0 else INK, ms=5)
    ax.axvline(1, color=MUT, lw=1, ls=":"); ax.set_xscale("log")
    ax.set_yticks(range(len(rows))[::-1]); ax.set_yticklabels([r[0] for r in rows] if j == 0 else [], fontsize=9)
    ax.set_title(["Arena in the authority", "Each log unit farther from an arena"][j], fontsize=11, color=INK)
    ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    if j == 1: ax.set_xticks([0.5, 1, 2])
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}"))
    ax.grid(axis="x", color=RULE, lw=0.5)
title(fig, "The arena premium holds; the 'shadow' needs London out", "Rate ratios with 95% intervals from the main model (red) and each robustness check (black).")
foot(fig)
out(fig, "robust")

# header 1200x630
fig = plt.figure(figsize=(12, 6.3), dpi=100)
fig.patch.set_facecolor(PAPER)
ax = fig.add_axes([0.52, 0.0, 0.48, 1.0]); ax.set_axis_off()
lad.plot(ax=ax, column="lr", cmap=CMAP, norm=TwoSlopeNorm(0, -4, 4), edgecolor=PAPER, linewidth=0.2)
ax.scatter(ar.geometry.x, ar.geometry.y, marker="^", s=30, color=INK, edgecolor=PAPER, linewidth=0.6, zorder=5)
ax.set_xlim(-30000, 680000); ax.set_ylim(0, 1060000)
fig.text(0.05, 0.86, "DATA STUDY · 2026", fontsize=13, family=MONO, color=MUT)
fig.text(0.05, 0.78, "Does anyone play", fontsize=40, family=DISP, fontweight="bold", color=INK, va="top")
fig.text(0.05, 0.64, "your town?", fontsize=40, family=DISP, fontweight="bold", color=HOT, va="top")
fig.text(0.05, 0.44, f"{L['big_no_tour']} of {L['big_n']} big UK councils have no\ndocumented tour date. Arena towns hold\n{L['arena_pop_pc']:.0f}% of people, {L['arena_tour_pc']:.0f}% of tour dates.", fontsize=17, color=INK, va="top", linespacing=1.35)
fig.text(0.05, 0.08, "Concert geography from MusicBrainz · Dr Tristan Hotham", fontsize=12, family=MONO, color=MUT)
fig.savefig(ROOT / "header.png", dpi=100, facecolor=PAPER); plt.close(fig)
assert Image.open(ROOT / "header.png").size == (1200, 630)
print("figures done")
