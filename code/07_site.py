"""index.html from code/page_template.html + page.css + page_essay.html + fullscreen snippet, filled from data/results.json.
10.5281/zenodo.24113541, https://doi.org/10.5281/zenodo.24113541 and https://blog.tristanhotham.com/2026/10/31/band-towns/ stay for the publisher."""
from common import *

R = load_results()
t = (CODE / "page_template.html").read_text()
t = t.replace("{{CSS}}", (CODE / "page.css").read_text()).replace("%%ESSAY%%", (CODE / "page_essay.html").read_text())
t = t.replace("{{FULLSCREEN}}", (CODE / "fullscreen_snippet.html").read_text())
t = t.replace("{{REPO}}", REPO).replace("{{AI}}", AI).replace("{{BYLINE}}", BYLINE).replace("{{VERSION}}", "2026a")
t = fill(t, R)
assert set(re.findall(r"\{\{([^}]+)\}\}", t)) <= KEEP, set(re.findall(r"\{\{([^}]+)\}\}", t))
vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", t, flags=re.S)
for bad in BAD:
    assert bad not in vis, bad
assert "site-nav.js" in t and "data-fullscreen-map" in t
(ROOT / "index.html").write_text(t)
print("index.html", len(t) // 1024, "KB")
