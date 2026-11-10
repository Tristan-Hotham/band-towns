"""README.md, reddit/post.md and release/paper/cover_note.md, all numbers from data/results.json."""
from common import *

R = load_results(); L = R["la"]; X = R["x"]; C = R["coverage"]; P = R["placebo"]
f = lambda v, d=2: f"{v:.{d}f}"
readme = f"""# Does anyone play your town?

Concert geography from MusicBrainz. Every UK concert documented in the open MusicBrainz database, 1960 to 2025, placed in its local authority and compared with what the area's size predicts. **This is a map of the documented record, not of all concerts**: MusicBrainz is edited by volunteers and holds a small, uneven slice of the UK's live music.

Interactive page: {PAGE}
Paper: {{https://doi.org/10.5281/zenodo.24113541}}
Blog post: {{https://blog.tristanhotham.com/2026/10/31/band-towns/}}
Code and data: {REPO}

## Coverage first

- {C['world_events']:,} events worldwide in the dump; {C['uk_events']:,} placed in the UK ({C['uk_by_coords']:,} by venue coordinates, {C['uk_by_area']:,} by area name); {L['concerts']:,} concerts (typed Concert, not cancelled) dated 1960 to 2025.
- A median of {C['median_per_year_1980_2023']:.0f} documented UK concerts a year from 1980 to 2023 (minimum {C['min_per_year_1980_2023']}), with spikes when whole tours were entered ({C['y1998']} in 1998, {C['y2024']} in 2024).
- The ten most documented acts account for {C['top10_perf_share_pc']:.0f}% of documented concerts and the ten most documented venues for {C['top_venue_share_pc']:.0f}%. One venue archive (West Runton Pavilion, {R['top_venues'][1]['n']} concerts, {R['named']['North Norfolk']['y0']} to {R['named']['North Norfolk']['y1']}) makes North Norfolk the fourth most documented area.
- The 2017 UK Live Music Census found at least {R['census_compare']['glasgow_spaces_2017']} live music spaces in Glasgow; MusicBrainz documents concerts at {R['census_compare']['glasgow_mb']} Glasgow venues across 66 years.

## Headline results (plan written before any area-level count)

- {L['with_none']} of {L['n']} local authorities ({L['pop_none_m']:.1f} million people) have no documented concert.
- H1, size: population elasticity {f(X['elast'])} (95% CI {f(X['elast_lo'])} to {f(X['elast_hi'])}), above 1: double the people, about {X['double_pc']:.0f}% more documented concerts.
- H2, arenas: an authority with a 10,000+ seat indoor arena has {f(X['arena_rr'])} times the documented concerts (95% CI {f(X['arena_lo'])} to {f(X['arena_hi'])}); the real premium beats {100 - X['placebo_share_pc']:.1f}% of {P['draws']} placebo assignments. The {L['arena_las']} arena authorities hold {L['arena_pop_pc']:.0f}% of people, {L['arena_concerts_pc']:.0f}% of documented concerts and {L['arena_tour_pc']:.0f}% of documented tour dates.
- H2, shadow: not supported (log distance {f(X['dist_b'])}, 95% CI {f(X['dist_lo'])} to {f(X['dist_hi'])}). Exploratory: positive without London ({f(X['dist_nolondon_b'])}, {f(X['dist_nolondon_lo'])} to {f(X['dist_nolondon_hi'])}).
- H3, touring: the population elasticity of tour dates is not significantly higher than that of other concerts (difference {f(X['tour_pop_b'])}, CI {f(X['tour_pop_lo'])} to {f(X['tour_pop_hi'])}), but the arena premium is {f(X['tour_arena_rr'], 1)} times larger for tour dates (CI {f(X['tour_arena_lo'], 1)} to {f(X['tour_arena_hi'], 1)}). {L['big_no_tour']} of the {L['big_n']} authorities with 150,000+ people have no documented tour date.
- H4, time (exploratory): elasticity {f(X['e1970'])} in the 1970s (very wide interval) and {f(X['e2020'])} in the 2020s.
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

Hotham, T. (2026) Does anyone play your town? The geography of the documented concert record in the United Kingdom, 1960 to 2025. Zenodo. {{https://doi.org/10.5281/zenodo.24113541}}

{AI}
"""
(ROOT / "README.md").write_text(readme)

post = f"""**Title:** [OC] {L['big_no_tour']} of the UK's {L['big_n']} biggest council areas have no documented tour date in MusicBrainz, while the 14 with a big arena ({L['arena_pop_pc']:.0f}% of people) hold {L['arena_tour_pc']:.0f}% of them

**Body:**

I mapped every UK concert that volunteers have entered into MusicBrainz, the open music database: {L['concerts']:,} gigs from 1960 to 2025, placed by venue into the UK's {L['n']} council areas, and compared each area with what its size predicts.

- {L['with_none']} of {L['n']} council areas have no documented concert at all ({L['pop_none_m']:.1f} million people live in them).
- Double an area's population and you get about {X['double_pc']:.0f}% more documented gigs (elasticity {X['elast']:.2f}).
- The 14 areas with an indoor arena of 10,000+ seats: {L['arena_pop_pc']:.0f}% of people, {L['arena_concerts_pc']:.0f}% of documented gigs, {L['arena_tour_pc']:.0f}% of documented tour dates.
- Wiltshire ({R['named']['Wiltshire']['pop']:,} people) has {R['named']['Wiltshire']['n']} documented gig. North Norfolk has {R['named']['North Norfolk']['n']}, because somebody entered a long run of gigs at one 1970s venue, the West Runton Pavilion.

Big caveat: this is a map of what the record remembers, not of where music happens. MusicBrainz holds a median of {C['median_per_year_1980_2023']:.0f} UK concerts a year since 1980.

Interactive map with a decade slider, tap any area: {PAGE}

**Source comment:**

Data: MusicBrainz JSON dumps 2026 (CC0, MetaBrainz Foundation); census 2021/2022 populations (ONS, NRS, NISRA, OGL); arenas from Wikipedia's list of UK indoor arenas. Method: Poisson (PPML) models of documented concerts on population, nation and arenas, plan written before any area-level count; placebo arenas and 15 robustness checks. Tools: Python (pandas, geopandas, statsmodels, matplotlib), MapLibre. Paper and code: {REPO}
"""
(ROOT / "reddit" / "post.md").write_text(post)

cover = f"""# Cover note: Does Anyone Play Your Town?

## Suitable journals (no fee to publish)

The brief named *Popular Music*, *Journal of Cultural Geography* and *Area*. All three are subscription (hybrid) journals in which open access is optional, so publication does not require an article processing charge. The PDF has about 6,400 words before the references, including tables and figure captions.

1. **Popular Music** (Cambridge University Press). Fits the live music and touring argument and the live music history literature it engages. Word limit checked online (Cambridge author instructions, retrieved 2026): "Articles should not normally exceed 10,000 words but shorter papers are welcome", so the paper fits. Note that the journal charges for colour figures in the print version. Check whether a quantitative paper of this kind suits its scope.
2. **Area** (Wiley, for the Royal Geographical Society with IBG). Best fit for the methodological argument: a coverage audit of volunteered cultural data and the geography of attention. It published Watson (2008) on London's music industry. Its author guidelines page could not be loaded from here, so the word limit is not verified: check it before submitting and expect to cut if the limit is below about 6,400 words.
3. **Journal of Cultural Geography** (Taylor and Francis). Fits the music and place literature. Confirmed online as a hybrid journal (open access optional, Open Select). Its instructions for authors could not be loaded from here, so the word limit is not verified: check it before submitting.

## Summary of the contribution (150 words)

Open, crowd-sourced archives are attractive sources for the geography of live music, but their coverage is rarely audited. I place every UK event in MusicBrainz in its local authority and model the {L['concerts']:,} documented concerts of 1960 to 2025 with a pre-specified plan. The record is thin, a median of {C['median_per_year_1980_2023']:.0f} concerts a year since 1980, and lumpy, shaped by fan-documented tours and a few venue archives. Documented concerts rise steeply with population (elasticity {X['elast']:.2f}). Areas with a 10,000+ seat arena have {X['arena_rr']:.1f} times the documented concerts of comparable areas, a premium concentrated in tour dates and stronger than placebo arenas; the {L['arena_las']} arena areas hold {L['arena_pop_pc']:.0f}% of people and {L['arena_tour_pc']:.0f}% of tour dates. The expected arena shadow is not found. {L['big_no_tour']} of {L['big_n']} large areas have no documented tour date. The paper argues that such data map attention to music, and offers a coverage audit.
"""
(ROOT / "release" / "paper" / "cover_note.md").write_text(cover)
for t in (readme, post, cover):
    for bad in ("—", "–", "D" "SIT", "D" "CMS", "pre-" "registered", "civil" " serv"):
        assert bad not in t, bad
print("README, post, cover note written")
