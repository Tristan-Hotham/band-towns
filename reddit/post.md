**Title:** [OC] 70 of the UK's 167 biggest council areas have no documented tour date in MusicBrainz, while the 14 with a big arena (10% of people) hold 53% of them

**Body:**

I mapped every UK concert that volunteers have entered into MusicBrainz, the open music database: 7,615 gigs from 1960 to 2025, placed by venue into the UK's 361 council areas, and compared each area with what its size predicts.

- 161 of 361 council areas have no documented concert at all (21.8 million people live in them).
- Double an area's population and you get about 213% more documented gigs (elasticity 1.64).
- The 14 areas with an indoor arena of 10,000+ seats: 10% of people, 38% of documented gigs, 53% of documented tour dates.
- Wiltshire (510,334 people) has 1 documented gig. North Norfolk has 335, because somebody entered a long run of gigs at one 1970s venue, the West Runton Pavilion.

Big caveat: this is a map of what the record remembers, not of where music happens. MusicBrainz holds a median of 120 UK concerts a year since 1980.

Interactive map with a decade slider, tap any area: https://maps.tristanhotham.com/band-towns/

**Source comment:**

Data: MusicBrainz JSON dumps 2026 (CC0, MetaBrainz Foundation); census 2021/2022 populations (ONS, NRS, NISRA, OGL); arenas from Wikipedia's list of UK indoor arenas. Method: Poisson (PPML) models of documented concerts on population, nation and arenas, plan written before any area-level count; placebo arenas and 15 robustness checks. Tools: Python (pandas, geopandas, statsmodels, matplotlib), MapLibre. Paper and code: https://github.com/Tristan-Hotham/band-towns
