"""Replace venue names that are street addresses or a private dwelling with a neutral label (privacy rule)."""
from pathlib import Path
D = Path(__file__).resolve().parent.parent / "data"
MASK = {"5 Torren St": "Venue (address withheld)", "62-68 Rosebury Avenue": "Venue (address withheld)",
        "26 Leake Street": "Leake Street arches", "Bron-Yr-Aur Cottage": "Private cottage (name withheld)"}
for f in ["events_uk.csv", "venues_uk.csv", "site.json", "venues.geojson"]:
    p = D / f; t = p.read_text(encoding="utf-8")
    for k, v in MASK.items(): t = t.replace(k, v)
    p.write_text(t, encoding="utf-8")
print("masked")
