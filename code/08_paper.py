"""The paper: fills code/paper_template.tex from data/results.json, adds tables, compiles with xelatex.
Output: release/paper/Hotham_Band_Towns.pdf and .tex. The DOI stays the placeholder https://doi.org/10.5281/zenodo.24113541 unless the
environment variable DOI is set:  DOI=10.5281/zenodo.N python3 code/08_paper.py"""
import os, subprocess
import pandas as pd
from common import *

R = load_results()
OUT = ROOT / "release" / "paper"; NAME = "Hotham_Band_Towns"
assert R["arena_ci_incl1"] == ["cap3", "no_En", "notop10", "performers", "y2000"], R["arena_ci_incl1"]


def tex(s): return str(s).replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#")
def p(v): return "$<$0.001" if v < 0.001 else f"{v:.3f}"
def rr(c, d=2): return f"{c['rr']:.{d}f} [{c['rr_lo']:.{d}f}, {c['rr_hi']:.{d}f}]"
def b(c, d=2): return f"{c['b']:.{d}f} [{c['lo']:.{d}f}, {c['hi']:.{d}f}]"


ar = pd.read_csv(DATA / "arenas.csv")
rows = "".join(f"{tex(r.arena)} & {tex(r.la_name)} & {r.capacity:,} & {r.opened}\\\\\n" for r in ar.itertuples())
T_AR = ("\\begin{table}[tbp]\\centering\\small\\caption{UK indoor arenas of 10,000 or more seats (Wikipedia list, retrieved 2026) and the local authority containing each.}\\label{tab:arenas}"
        "\\begin{tabular}{llrr}\\toprule Arena & Local authority & Capacity & Opened\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")

M1, M2, M3 = R["M1"], R["M2"], R["M3"]
T_MAIN = ("\\begin{table}[tbp]\\centering\\small\\caption{Main models (PPML; nation fixed effects; HC1 standard errors for M1 and M2, clustered by authority for M3). "
          "Coefficients with 95\\% CI; for arena and distance terms the rate ratio is also shown.}\\label{tab:main}"
          "\\begin{tabular}{p{6.3cm}lrr}\\toprule Term & Estimate [95\\% CI] & $p$ & N\\\\\\midrule\n"
          f"M1: log population (elasticity) & {b(M1)} & {p(M1['p'])} & {M1['n']}\\\\\n"
          f"\\quad test of elasticity = 1 & z = {M1['z_vs1']:.2f} & {p(M1['p_vs1'])} & \\\\\\midrule\n"
          f"M2: log population & {b(M2['logpop'])} & {p(M2['logpop']['p'])} & {M2['logpop']['n']}\\\\\n"
          f"M2: arena in the authority (rate ratio) & {rr(M2['arena_la'])} & {p(M2['arena_la']['p'])} & {M2['arena_la']['n']}\\\\\n"
          f"M2: log distance to nearest arena & {b(M2['logdist'])} & {p(M2['logdist']['p'])} & {M2['logdist']['n']}\\\\\n"
          f"M2: pseudo-$R^2$ (deviance) & {M2['pseudo_r2']:.2f} & & \\\\\\midrule\n"
          f"M3: log population (other concerts) & {b(M3['logpop'])} & {p(M3['logpop']['p'])} & {M3['logpop']['n']}\\\\\n"
          f"M3: log population $\\times$ tour & {b(M3['logpop_x_tour'])} & {p(M3['logpop_x_tour']['p'])} & {M3['logpop']['n']}\\\\\n"
          f"M3: arena (other concerts, rate ratio) & {rr(M3['arena_la'])} & {p(M3['arena_la']['p'])} & {M3['logpop']['n']}\\\\\n"
          f"M3: arena $\\times$ tour (ratio of rate ratios) & {rr(M3['arena_la_x_tour'])} & {p(M3['arena_la_x_tour']['p'])} & {M3['logpop']['n']}\\\\\n"
          f"M3: log distance (other concerts) & {b(M3['logdist'])} & {p(M3['logdist']['p'])} & {M3['logpop']['n']}\\\\\n"
          f"M3: log distance $\\times$ tour & {b(M3['logdist_x_tour'])} & {p(M3['logdist_x_tour']['p'])} & {M3['logpop']['n']}\\\\\n"
          "\\bottomrule\\end{tabular}\\end{table}")

rows = ""
for d, v in sorted(R["decades"].items()):
    rows += f"{d}s & {v['n']:,} & {v['las_with_any']} & {b(v['elast'])} & {rr(v['arena'])} & {b(v['dist'])} & {100 * v['top10_share']:.0f}\\%\\\\\n"
T_DEC = ("\\begin{table}[tbp]\\centering\\footnotesize\\caption{Decade models (exploratory): documented concerts, authorities with any, M1 elasticity, and M2 arena rate ratio and log-distance coefficient using arenas open by the decade; share in the ten leading authorities. N = 361 per decade.}\\label{tab:decades}"
         "\\begin{tabular}{lrrlllr}\\toprule Decade & Concerts & Areas & Elasticity & Arena RR & Log distance & Top 10\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")

rows = f"Main estimate (M2) & {rr(M2['arena_la'])} & {b(M2['logdist'])} & {M2['logdist']['n']}\\\\\\midrule\n"
for k, v in R["robust"].items():
    import math
    ld = v["logdist"]
    rows += f"{tex(v['label'])} & {rr(v['arena_la'])} & {math.log(ld['rr']):.2f} [{math.log(ld['rr_lo']):.2f}, {math.log(ld['rr_hi']):.2f}] & {ld['n']}\\\\\n"
T_ROB = ("\\begin{table}[tbp]\\centering\\footnotesize\\caption{Robustness of M2: arena rate ratio and log-distance coefficient with 95\\% CI. The OLS row reports exponentiated OLS coefficients on log(1 + concerts).}\\label{tab:robust}"
         "\\begin{tabular}{p{6.2cm}llr}\\toprule Check & Arena rate ratio & Log distance & N\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")

lab = {"const": "Constant", "logpop": "log population", "arena_la": "arena", "logdist": "log distance to arena", "nat_Sc": "Scotland",
       "nat_Wa": "Wales", "nat_No": "Northern Ireland", "tour": "tour", "logpop_x_tour": "log population $\\times$ tour",
       "arena_la_x_tour": "arena $\\times$ tour", "logdist_x_tour": "log distance $\\times$ tour"}
rows = ""
for m, t in R["tables"].items():
    rows += f"\\multicolumn{{4}}{{l}}{{\\textbf{{{m}}}}}\\\\\n"
    for k, v in t.items():
        rows += f"\\quad {lab.get(k, tex(k))} & {v['b']:.3f} & {v['se']:.3f} & {p(v['p'])}\\\\\n"
T_APPX = ("\\begin{table}[htbp]\\centering\\small\\caption{Full coefficient tables (PPML). M1 and M2: N = 361, HC1 standard errors; M3: N = 722 authority-outcome rows, standard errors clustered by authority. England is the reference nation.}\\label{tab:appx}"
          "\\begin{tabular}{lrrr}\\toprule Term & Coefficient & SE & $p$\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")

t = (CODE / "paper_template.tex").read_text()
for k, v in (("TABLE_ARENAS", T_AR), ("TABLE_MAIN", T_MAIN), ("TABLE_DECADES", T_DEC), ("TABLE_ROBUST", T_ROB), ("TABLE_APPX", T_APPX)):
    t = t.replace("{{" + k + "}}", v)
t = t.replace("{{AI}}", AI)
t = re.sub(r"\{\{([^{}|]+)(\|(\w+))?\}\}", lambda m: m.group(0) if m.group(1) in KEEP else tex(fmt(get(R, m.group(1)), m.group(3))) if m.group(3) == "raw" else fmt(get(R, m.group(1)), m.group(3)).replace("%", "\\%"), t)
doi = os.environ.get("DOI")
t = t.replace("https://doi.org/10.5281/zenodo.24113541", f"https://doi.org/{doi}" if doi else "\\{\\{DOI\\_URL\\}\\}")
assert "{{" not in t, re.findall(r"\{\{[^}]+\}\}", t)
for bad in ("—", "–", "D" "SIT", "D" "CMS", "pre-" "registered"):
    assert bad not in t, bad
OUT.mkdir(parents=True, exist_ok=True)
(OUT / f"{NAME}.tex").write_text(t)
for _ in range(2):
    subprocess.run(["xelatex", "-interaction=nonstopmode", f"{NAME}.tex"], cwd=OUT, capture_output=True, text=True)
log = (OUT / f"{NAME}.log").read_text(errors="ignore")
print("undefined refs:", log.count("undefined"), "| pages:", re.findall(r"Output written on .*?\((\d+) pages", log))
for e in ("aux", "log", "out"):
    f = OUT / f"{NAME}.{e}"
    if f.exists(): f.unlink()
txt = subprocess.run(["pdftotext", str(OUT / f"{NAME}.pdf"), "-"], capture_output=True, text=True).stdout
body = txt.split("References")[0]
print("words (whole pdf):", len(txt.split()), "| before references:", len(body.split()))
ab = re.search(r"Abstract(.*?)Keywords", txt, re.S)
print("abstract words:", len(ab.group(1).split()) if ab else None)
