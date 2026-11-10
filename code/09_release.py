"""Blog post and meta (release/blog), Zenodo files and metadata (release/zenodo).
10.5281/zenodo.24113541, https://doi.org/10.5281/zenodo.24113541 and https://blog.tristanhotham.com/2026/10/31/band-towns/ are left for the publisher to fill."""
import json, shutil, zipfile, os
from PIL import Image
from common import *

R = load_results()
REL = ROOT / "release"; NAME = "Hotham_Band_Towns"
post = (CODE / "blog_template.html").read_text()
post = re.sub(r"\{\{(?!IMG)([^{}|]+)(\|(\w+))?\}\}", lambda m: m.group(0) if m.group(1) in KEEP else fmt(get(R, m.group(1)), m.group(3)), post)
used = re.findall(r"\{\{IMG\|([^|]+)\|", post)
assert 5 <= len(used) <= 8, len(used)
assert all(re.search(r"^\{\{IMG\|" + re.escape(u), post, re.M) for u in used) and "wp:image" not in post
for img in used:
    assert Image.open(REL / "blog" / img).size[0] == 1800, img
for fn in os.listdir(REL / "blog"):
    if fn.startswith("b_") and fn not in used:
        os.remove(REL / "blog" / fn)
assert set(re.findall(r"\{\{([^|}]+)\}\}", post)) <= KEEP
vis = re.sub(r"<!--.*?-->", "", post, flags=re.S)
for bad in BAD:
    assert bad not in vis, bad
assert AI in post
(REL / "blog" / "post.html").write_text(post)
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", vis).split())
L = R["la"]
meta = {"title": "Does anyone play your town?",
        "slug": "band-towns",
        "excerpt": f"Volunteers have documented {L['concerts']:,} UK concerts in MusicBrainz. I mapped every one by council area. {L['big_no_tour']} of {L['big_n']} big council areas have no documented tour date, and arena towns hold {L['arena_tour_pc']:.0f}% of them.",
        "seo_description": f"Every UK concert documented in MusicBrainz, 1960 to 2025, mapped by council area: arena towns hold {L['arena_pop_pc']:.0f}% of people but {L['arena_tour_pc']:.0f}% of tour dates.",
        "tags": ["maps", "data visualisation", "music", "live music", "concerts", "MusicBrainz", "open data", "UK"],
        "header_alt": "Title card on cream paper reading 'Does anyone play your town?' beside a map of UK council areas, most shaded blue, with red patches and black arena triangles."}
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
json.dump(meta, open(REL / "blog" / "meta.json", "w"), ensure_ascii=False, indent=2)

Z = REL / "zenodo"; Z.mkdir(parents=True, exist_ok=True)
for fn in os.listdir(Z):
    os.remove(Z / fn)
shutil.copy(REL / "paper" / f"{NAME}.pdf", Z / f"{NAME}.pdf")
zp = Z / f"{SLUG}_data_and_code.zip"
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for fn in sorted(os.listdir(CODE)):
        if fn.endswith(".pyc") or fn == "__pycache__":
            continue
        z.write(CODE / fn, f"{SLUG}/code/{fn}")
    for fn in sorted(os.listdir(DATA)):
        z.write(DATA / fn, f"{SLUG}/data/{fn}")
    for fn in ("README.md", "LICENSE", "NOTES.md"):
        z.write(ROOT / fn, f"{SLUG}/{fn}")
    z.write(REL / "paper" / "cover_note.md", f"{SLUG}/release/paper/cover_note.md")
    z.write(ROOT / "reddit" / "collage.py", f"{SLUG}/reddit/collage.py")
tex = (REL / "paper" / f"{NAME}.tex").read_text()
ab = re.search(r"\\begin\{center\}\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n", tex, re.S).group(1)
ab = ab.replace("\\%", "%").replace("\\&", "&").replace("$", "").replace("``", "\"").replace("''", "\"").replace("~", " ")
zmeta = {"title": "Does Anyone Play Your Town? The Geography of the Documented Concert Record in the United Kingdom, 1960 to 2025",
         "upload_type": "publication", "publication_type": "workingpaper",
         "description": f"<p>{ab}</p><p>Interactive version: <a href=\"{PAGE}\">{PAGE}</a>. Data and code: <a href=\"{REPO}\">{REPO}</a>. Blog post: {{https://blog.tristanhotham.com/2026/10/31/band-towns/}}.</p>"
                        "<p>Sources: MusicBrainz JSON data dumps, 2026 (MetaBrainz Foundation, CC0); Census 2021 (ONS, NISRA) and Scotland's Census 2022 (NRS), "
                        "local authority boundaries December 2023 (ONS, OSNI), Open Government Licence v3.0; Wikipedia, List of indoor arenas in the United Kingdom (CC BY-SA 4.0); "
                        "Wikidata (CC0). Text, figures and data CC BY 4.0; code MIT.</p>",
         "creators": [{"name": "Hotham, Tristan", "affiliation": "Independent researcher", "orcid": "0000-0003-4931-9349"}],
         "keywords": ["live music", "concerts", "touring", "MusicBrainz", "crowd-sourced data", "volunteered geographic information", "urban scaling", "United Kingdom"],
         "license": "cc-by-4.0", "language": "eng",
         "related_identifiers": [{"identifier": REPO, "relation": "isSupplementedBy", "resource_type": "software"},
                                 {"identifier": PAGE, "relation": "isSupplementedBy", "resource_type": "other"}],
         "files": sorted(os.listdir(Z))}
sj = json.dumps(zmeta, ensure_ascii=False) + json.dumps(meta, ensure_ascii=False)
for bad in BAD:
    assert bad not in sj, bad
json.dump(zmeta, open(Z / "metadata.json", "w"), ensure_ascii=False, indent=2)
print("blog words", words, "figures", len(used), "; zenodo", sorted(os.listdir(Z)), zp.stat().st_size // 1024, "KB zip")
