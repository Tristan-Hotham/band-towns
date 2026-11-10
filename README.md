# Does anyone play your town?

Concert geography from MusicBrainz. Every UK concert documented in the open MusicBrainz database, 1960 to 2025, placed in its local authority and compared with what the area's size predicts. **This is a map of the documented record, not of all concerts**: MusicBrainz is edited by volunteers and holds a small, uneven slice of the UK's live music.

Interactive page: https://maps.tristanhotham.com/band-towns/
Paper: https://doi.org/10.5281/zenodo.24113541
Blog post: https://blog.tristanhotham.com/2026/10/31/band-towns/
Code and data: https://github.com/Tristan-Hotham/band-towns

## Coverage first

- 129,282 events worldwide in the dump; 11,329 placed in the UK (10,425 by venue coordinates, 904 by area name); 7,615 concerts (typed Concert, not cancelled) dated 1960 to 2025.
- A median of 120 documented UK concerts a year from 1980 to 2023 (minimum 28), with spikes when whole tours were entered (582 in 1998, 485 in 2024).
- The ten most documented acts account for 12% of documented concerts and the ten most documented venues for 26%. One venue archive (West Runton Pavilion, 335 concerts, 1975 to 1983) makes North Norfolk the fourth most documented area.
- The 2017 UK Live Music Census found at least 241 live music spaces in Glasgow; MusicBrainz documents concerts at 57 Glasgow venues across 66 years.

## Headline results (plan written before any area-level count)

- 161 of 361 local authorities (21.8 million people) have no documented concert.
- H1, size: population elasticity 1.64 (95% CI 1.21 to 2.08), above 1: double the people, about 213% more documented concerts.
- H2, arenas: an authority with a 10,000+ seat indoor arena has 3.80 times the documented concerts (95% CI 1.05 to 13.73); the real premium beats 99.6% of 500 placebo assignments. The 14 arena authorities hold 10% of people, 38% of documented concerts and 53% of documented tour dates.
- H2, shadow: not supported (log distance -0.22, 95% CI -0.68 to 0.24). Exploratory: positive without London (0.65, 0.27 to 1.02).
- H3, touring: the population elasticity of tour dates is not significantly higher than that of other concerts (difference 0.31, CI -0.22 to 0.84), but the arena premium is 7.0 times larger for tour dates (CI 2.3 to 21.8). 70 of the 167 authorities with 150,000+ people have no documented tour date.
- H4, time (exploratory): elasticity 0.84 in the 1970s (very wide interval) and 1.91 in the 2020s.
- Robustness: the arena premium keeps its sign in all 15 checks; its interval includes 1 when each act is capped at 3 concerts per area, without the 10 most documented acts, for 2000 to 2025 only, for distinct performers, and without England.

## Files

| File | What it is |
|---|---|
| `index.html`, `js/page.js` | Interactive page: MapLibre on OpenFreeMap Positron; council areas sized by documented concerts and coloured against expectation, decade slider, tour-date view, venues, arenas, search, full screen. |
| `header.png` | Social card, 1200 x 630. |
| `data/events_uk.csv` | Every UK MusicBrainz event placed in a local authority (MusicBrainz ids, type, date, venue, performers). |
| `data/venues_uk.csv`, `data/venues.geojson` | Venues (public names, no addresses). |
| `data/authorities.csv`, `data/la_counts.csv` | Local authorities with population, arena distance, counts by outcome and decade, model fit. |
| `data/tours.csv` | Artist-years with 5+ documented UK concerts. |
| `data/arenas.csv` | The 15 arenas of 10,000+ seats. |
| `data/coverage_by_year.csv` | Events worldwide and in the UK by year. |
| `data/results.json`, `data/results_models.json` | Every number quoted anywhere. |
| `data/site.json`, `data/la_outlines.geojson` | Page data. |
| `code/` | Scripts in order, templates, `qa.js`. |
| `release/` | Paper (PDF, LaTeX, figures, `cover_note.md`), blog post and figures, Zenodo files. |
| `reddit/` | Collage, its script, the looping GIF and the post text. |
| `NOTES.md` | Working notes and the analysis plan. |

## How to rerun

Python 3 with pandas, numpy, geopandas, shapely, pyproj, statsmodels, scipy, matplotlib, Pillow; xelatex; node with Playwright for QA. Inputs are listed in `code/common.py` (the MusicBrainz dumps are streamed from their .tar.xz archives).

```
python3 code/01_extract.py      # stream the event and place dumps (scratch files)
python3 code/02_build.py        # place events in local authorities; authorities, arenas
python3 code/03_models.py       # counts and the planned models, robustness, placebo
python3 code/04_results.py      # data/results.json
python3 code/05_figures.py      # figures and header.png
python3 code/06_site_data.py    # page data
python3 code/07_site.py         # index.html
python3 code/08_paper.py        # paper (DOI=10.5281/zenodo.N to fill the DOI)
python3 code/10_readme.py       # README, Reddit post, cover note
python3 code/09_release.py      # blog post, Zenodo files
python3 reddit/collage.py
```

## Sources and licences

- MusicBrainz JSON data dumps, 2026, MetaBrainz Foundation: CC0.
- Census 2021 (ONS for England and Wales, NISRA for Northern Ireland) and Scotland's Census 2022 (NRS); local authority boundaries, December 2023 (ONS, OSNI): Open Government Licence v3.0, contains OS data © Crown copyright.
- Arenas: Wikipedia, List of indoor arenas in the United Kingdom, retrieved 2026 (CC BY-SA 4.0).
- Settlements for area-name placement: Wikidata (CC0).
- Base map: OpenFreeMap Positron (OpenStreetMap contributors, ODbL).

Code: MIT. Text, figures and derived data: CC BY 4.0 (see `LICENSE`).

## Citation

Hotham, T. (2026) Does anyone play your town? The geography of the documented concert record in the United Kingdom, 1960 to 2025. Zenodo. https://doi.org/10.5281/zenodo.24113541

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
