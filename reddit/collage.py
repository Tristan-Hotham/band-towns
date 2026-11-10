"""Reddit collage for band-towns (r/dataisbeautiful style, light background). Run from the study root:
python3 reddit/collage.py  ->  reddit/band_towns_collage.png (2400 px wide). All numbers from data/results.json."""
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib import font_manager as fm
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
import numpy as np, pandas as pd, geopandas as gpd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = "/home/claude/ref/fonts"
for f in ("FrauncesVar.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf", "IBMPlexMono-Regular.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
DISP = fm.FontProperties(fname=f"{FONTS}/FrauncesVar.ttf").get_name()
plt.rcParams.update({"font.family": "Source Serif 4", "axes.unicode_minus": False})
PAPER, INK, MUT, RULE, SEA = "#F7F2E6", "#2B2119", "#6E604E", "#DCCFAF", "#E4ECF1"
HOT, COOL, GREY = "#B4442E", "#2F6A9E", "#9C9384"
CMAP = LinearSegmentedColormap.from_list("g", ["#1F4F7A", "#6F9CC4", "#D8D1C3", "#E3A08A", "#B4442E", "#6E1F12"])
HALO = [pe.withStroke(linewidth=4, foreground=SEA)]
R = json.load(open(f"{ROOT}/data/results.json")); L = R["la"]; X = R["x"]; C = R["coverage"]
A = pd.read_csv(f"{ROOT}/data/la_counts.csv")
lad = gpd.read_file("/home/claude/newdata/raw/geo/lad23_bgc.geojson").to_crs(27700).merge(A[["lad", "concerts", "fitted"]], left_on="LAD23CD", right_on="lad")
lad["lr"] = np.log2((lad.concerts + 0.5) / (lad.fitted + 0.5)).clip(-4, 4)
ar = pd.read_csv(f"{ROOT}/data/arenas.csv")
arg = gpd.GeoDataFrame(ar, geometry=gpd.points_from_xy(ar.lon, ar.lat), crs=4326).to_crs(27700)

fig = plt.figure(figsize=(24, 27), dpi=100, facecolor=PAPER)
fig.text(0.035, 0.975, "Does anyone play your town?", fontsize=64, fontweight="bold", family=DISP, color=INK, va="top")
fig.text(0.035, 0.935, f"Every UK concert volunteers have documented in MusicBrainz, 1960 to 2025 ({L['concerts']:,} gigs), by council area,\n"
         "against the number expected from its population, nation and arenas. A map of what the record remembers, not of all gigs.",
         fontsize=25, color=MUT, va="top", linespacing=1.4)

# map
ax = fig.add_axes([0.0, 0.11, 0.56, 0.77]); ax.set_facecolor(SEA)
ax.set_xticks([]); ax.set_yticks([]); [s.set_visible(False) for s in ax.spines.values()]
lad.plot(ax=ax, column="lr", cmap=CMAP, norm=TwoSlopeNorm(0, -4, 4), edgecolor="white", linewidth=0.3)
ax.scatter(arg.geometry.x, arg.geometry.y, marker="^", s=170, color=INK, edgecolor="white", linewidth=1.4, zorder=5)
ax.set_xlim(-60000, 690000); ax.set_ylim(-70000, 1070000); ax.set_xlabel(""); ax.set_ylabel("")
lab = A.set_index("la_name")
for nm, x, y, tx, ty, ha in (("North Norfolk", 615000, 340000, 686000, 560000, "right"),
                            ("Westminster", 529000, 179000, 686000, 20000, "right"),
                            ("Fife", 340000, 708000, 686000, 740000, "right"),
                            ("Wiltshire", 400000, 160000, 330000, -45000, "center")):
    r = lab.loc[nm]
    ax.annotate(f"{nm}\n{int(r.concerts)} documented, {r.fitted:.0f} expected", (x, y), xytext=(tx, ty), fontsize=19, color=INK, ha=ha,
                arrowprops=dict(arrowstyle="-", color=INK, lw=1.2), path_effects=HALO)
# legend on sea (Irish Sea / Atlantic, south of Northern Ireland and west of Wales)
cax = fig.add_axes([0.025, 0.405, 0.11, 0.012])
cb = fig.colorbar(plt.cm.ScalarMappable(cmap=CMAP, norm=TwoSlopeNorm(0, -4, 4)), cax=cax, orientation="horizontal")
cb.set_ticks([-4, 0, 4]); cb.set_ticklabels(["16x\nfewer", "as\nexpected", "16x\nmore"]); cb.ax.tick_params(labelsize=15)
fig.text(0.03, 0.423, "Documented concerts\nagainst expectation\n(size, nation, arenas)", fontsize=19, color=INK, va="bottom")
fig.text(0.03, 0.36, "▲  indoor arena,\n    10,000+ seats", fontsize=19, color=INK, va="top")
fig.text(0.03, 0.322, "Ratios capped at 16x. Areas\nwith none documented are\nblue, darker where more\nwere expected.", fontsize=15, color=MUT, va="top", linespacing=1.3)

# right column: numbers and charts
def big(y, num, txt, col=HOT):
    fig.text(0.60, y, num, fontsize=66, fontweight="bold", family=DISP, color=col, va="top")
    fig.text(0.60, y - 0.045, txt, fontsize=21, color=INK, va="top", linespacing=1.35)
big(0.87, f"{L['with_none']} of {L['n']}", f"council areas have no documented\nconcert at all ({L['pop_none_m']:.1f} million people)")
big(0.76, f"{X['elast']:.2f}", f"elasticity: double the people,\nabout {X['double_pc']:.0f}% more documented gigs")

a2 = fig.add_axes([0.62, 0.43, 0.34, 0.18]); a2.set_facecolor(PAPER)
labs = ["Population", "Documented\nconcerts", "Tour dates", "Other\nconcerts"]
vals = [L["arena_pop_pc"], L["arena_concerts_pc"], L["arena_tour_pc"], L["arena_other_pc"]]
a2.barh(range(4)[::-1], vals, color=[GREY, HOT, "#6E1F12", "#E3A08A"], height=0.65)
for i, v in enumerate(vals):
    a2.text(v + 1, 3 - i, f"{v:.0f}%", va="center", fontsize=20, color=INK)
a2.set_yticks(range(4)[::-1]); a2.set_yticklabels(labs, fontsize=17); a2.set_xlim(0, 68); a2.set_xticks([])
for s in ("top", "right", "bottom"): a2.spines[s].set_visible(False)
fig.text(0.60, 0.655, f"The arena circuit: share held by the {L['arena_las']}\ncouncil areas with a 10,000+ seat arena", fontsize=23, fontweight="bold", color=INK, va="top")

sk = pd.DataFrame(R["skipped"]).head(8)
fig.text(0.60, 0.385, f"{L['big_no_tour']} of {L['big_n']} areas of 150,000+ people have\nno documented tour date. The biggest:", fontsize=23, fontweight="bold", color=INK, va="top")
a3 = fig.add_axes([0.70, 0.12, 0.26, 0.20]); a3.set_facecolor(PAPER)
a3.barh(range(len(sk))[::-1], sk["pop"] / 1000, color=COOL, height=0.65)
for i, r in sk.iterrows():
    a3.text(r["pop"] / 1000 + 8, len(sk) - 1 - i, f"{r['pop'] / 1000:.0f}k", va="center", fontsize=16, color=INK)
a3.set_yticks(range(len(sk))[::-1]); a3.set_yticklabels(sk.la, fontsize=17); a3.set_xlim(0, 640); a3.set_xticks([])
for s in ("top", "right", "bottom"): a3.spines[s].set_visible(False)

fig.text(0.035, 0.095, f"Caveat: MusicBrainz is volunteer-entered. It holds a median of {C['median_per_year_1980_2023']:.0f} UK concerts a year since 1980; one venue archive (West Runton Pavilion,\n"
         f"{R['top_venues'][1]['n']} gigs) makes North Norfolk the fourth most documented area. Areas with nothing documented still have gigs; nobody has written them down here.",
         fontsize=19, color=MUT, va="top", linespacing=1.4)
fig.text(0.035, 0.012, "Data: MusicBrainz dumps 2026 (CC0, MetaBrainz Foundation); census 2021/2022 (ONS, NRS, NISRA, OGL); arenas: Wikipedia list of UK indoor arenas\n"
         "Dr Tristan Hotham · maps.tristanhotham.com/band-towns", fontsize=17, family="IBM Plex Mono", color=MUT, va="bottom", linespacing=1.5)
out = f"{ROOT}/reddit/band_towns_collage.png"
fig.savefig(out, dpi=100, facecolor=PAPER)
print(out)
