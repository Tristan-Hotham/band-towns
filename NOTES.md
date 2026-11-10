# band-towns: working notes and analysis plan

"Does anyone play your town? Concert geography from MusicBrainz". Author Dr Tristan Hotham, Independent researcher, 2026.

## Status

- Phase 1 (done before any town-level count was made): streamed the MusicBrainz event and place dumps (2026-11-07), measured coverage (below), wrote this plan.
- Phase 2: build the local authority table, run the plan, then the paper, map, blog, collage, GIF. Anything not in this plan is labelled exploratory.

## Coverage facts found in phase 1 (these change the brief)

- The event dump holds 129,282 events worldwide (85,436 typed Concert, 32,137 Festival, 7,448 untyped). 114,144 have a "held at" place, 89,475 a place with coordinates, 9,212 a "held in" area.
- Events located in the UK (place coordinates in a broad UK box, or a place or area carrying a GB ISO 3166-2 code; to be tightened to UK local authority polygons): 11,826, of which 8,890 typed Concert, 1,599 Festival, 1,103 untyped. 209 are flagged cancelled.
- By year, the UK record holds roughly 100 to 250 events a year from the late 1970s to 2023, with spikes (1998: 681; 2002: 515; 2005: 569; 2024: 642; 2025: 919). A spike is usually one or two volunteers entering a set of tours or a venue's archive (2024: Take That 49, Girls Aloud 30). The UK has many tens of thousands of live music events every year, so MusicBrainz holds well under one in a hundred of them in any year. It is NOT a census of gigs.
- The record is dominated by a few artists and venues: top main performers Barry Manilow 269, Bruce Springsteen 163, Girls Aloud 156, Take That 141; top venues Royal Albert Hall 560, Queen's Hall 361 (Proms, 1895 to 1900), West Runton Pavilion 341 (a venue archive), Worthy Farm (Glastonbury) 299, The O2 238. TV studios (Maidstone Studios, BBC Television Centre) appear as places for recorded performances.
- No second source (setlist.fm, Songkick, PRS) can be fetched from the workspace, so no external check of coverage is possible here. Say so.

**Consequence for framing.** A credible census of concerts per town is not possible from these data. The study is reframed honestly as the geography of the *documented* concert record: which towns the crowd-sourced archive of live music remembers, how strongly that record follows population and the big arenas, and which towns big touring acts (whose tours fans document fully) visit and skip. Every public sentence must say "documented" or "recorded in MusicBrainz", never imply that the counts are all concerts.

## Units and data

- Unit: UK local authority districts (361, December 2023; ONS/OSNI boundaries `lad23_bgc.geojson`). Local authority, not town, because it partitions the UK and has a clean population denominator. Map labels use the authority name.
- Population: census usual residents per authority (2021 England, Wales, Northern Ireland; 2022 Scotland) from `/home/claude/studies/religion-map/data/uk_local_authorities.csv` (ONS, NRS, NISRA; Open Government Licence).
- Events placed by their "held at" place coordinates (point in polygon). Events with a place but no coordinates, or only a "held in" area, are placed at the largest Wikidata UK settlement of the same name as the place's area (or area); share reported; robustness drops them. Points outside every UK authority polygon (Ireland, Isle of Man, Channel Islands, France, sea) are dropped (points within 2 km of the coast go to the nearest authority).
- Main outcome: documented concerts = events typed Concert, not cancelled, dated 1960 to 2025 (complete years; 2026 is partial and holds announced future dates). One event = one count, whatever the number of acts.
- Big venues (exposure, fixed from an outside source, not from MusicBrainz): UK indoor arenas of 10,000+ capacity from Wikipedia's "List of indoor arenas in the United Kingdom" (retrieved 2026): Birmingham (bp pulse LIVE at the NEC, Solihull authority; Utilita Arena Birmingham), Coventry, Leeds, Liverpool, London (The O2, Greenwich; Wembley Arena, Brent), Manchester (AO Arena; Co-op Live), Newcastle, Nottingham, Sheffield, Belfast, Aberdeen (P&J Live), Glasgow (OVO Hydro). Distance from each authority centroid to the nearest such arena (km), using all 15 (pooled models) or those open by the decade (decade models).

## Pre-specified analysis plan (written before any authority-level count was computed)

**H1 (size).** Documented concerts rise more than in proportion to population (urban scaling, elasticity above 1). Model M1: PPML (Poisson pseudo-maximum likelihood), concerts ~ log population + nation fixed effects, robust (HC1) standard errors (one observation per authority, so no clustering). Report the elasticity with 95% CI and test it against 1. Against H1: CI including or below 1.

**H2 (arena shadow, gravity).** Conditional on population, authorities with a 10,000+ arena have more documented concerts, and among the others, authorities closer to an arena have fewer (they sit in its shadow; people travel to the arena city). Model M2 (main specification): concerts ~ log population + arena dummy + log(distance to nearest arena, km) + nation FE, PPML, HC1. H2 predicts arena > 0 and distance > 0. Against H2: distance coefficient at or below 0 or CI including 0. "Played more or less than its size predicts" on the map = observed / fitted from M2.

**H3 (touring circuit).** Tour dates are more concentrated in big places than other documented concerts. Tour = an artist-year with 5 or more UK documented concerts as main performer; tour dates = those concerts. Model M3: stack the two outcomes per authority (tour dates, other concerts), PPML with outcome-specific intercepts, log population x tour interaction (plus arena and distance with their own tour interactions), standard errors clustered by authority. H3 predicts a positive log population x tour term. Descriptive: share of tour dates in the 10 authorities with most tour dates; authorities of 150,000+ people with no tour date at all (the "skipped").

**H4 (time; descriptive and exploratory).** Elasticity of M1 by decade (1970s to 2020s), and the share of documented concerts in the top 10 authorities by decade. Expectation: concentration rises after the arena era begins (1990s).

**Robustness (all on M2 unless stated).** (1) negative binomial instead of PPML; (2) cap each artist at 3 concerts per authority (so one heavily documented act cannot drive a town); (3) drop the 10 most documented main performers; (4) drop events placed by area name only; (5) add festivals and untyped events with a performer; (6) 2000 to 2025 only; (7) outcome = distinct documented venues; (8) outcome = distinct main performers; (9) leave one nation out, and drop London (the 33 London authorities); (10) add log distance to central London; (11) OLS on log(1 + concerts).

**Placebo / falsification.** Assign the arena status and arena distances to 15 random authorities of similar population (same population decile as each real arena authority), 500 draws, seed 2026; the real distance coefficient should lie outside the bulk of the placebo distribution. A second falsification: recording studios (MusicBrainz places of type Studio) per authority, which should not show the arena shadow (studios are not visited by touring audiences); exploratory.

**What counts against the hypotheses** is stated per hypothesis above; the planned specification is the main result whatever it shows.

**Caveats to state everywhere.** Volunteer-entered, well under 1% of UK concerts; biased to famous acts, fan-documented tours and a few venue archives; one volunteer can move a town; the record says where concerts were *documented*, not where music happened; the analysis is correlational; arena list from Wikipedia; census population at 2021/2022 used for all decades (exploratory decade models only).

## Literature to verify (phase 2)

Urban scaling (Bettencourt et al. 2007 PNAS); music scenes and geography (Connell and Gibson 2003 Sound Tracks; Florida, Mellander and Stolarick 2010 music scenes; Leyshon 2001?); live music economics (Frith 2007 "Live music matters"; Frith, Brennan, Cloonan, Webster "The History of Live Music in Britain" vol 1 2013; Krueger 2005 J Labor Econ; Mortimer, Nosko and Sorensen 2012 "Supply responses to digital distribution: recorded music and live performances"; Holt 2010); concert data from crowdsourced sources (setlist.fm studies); MusicBrainz (Swartz 2002 IEEE Intelligent Systems); gravity / central place (Christaller); PPML (Santos Silva and Tenreyro 2006); UK Live Music Census 2017 (Webster et al. 2018). Each to be checked online before it is cited.

## Log

- 2026: dumps streamed (01_extract.py). Coverage measured. Plan written. No authority-level count computed yet.

## Phase 2 log (after the plan)

- Placement: 11,329 UK events (10,425 by venue coordinates, 904 by area name); 350 box events outside every UK authority and 147 unplaceable GB-area events dropped. 7,615 documented concerts 1960 to 2025.
- Measurement detail fixed at build time, before results: distance floored at 1 km before logging (one authority centroid sits within 1 km of an arena).
- Results as planned: H1 supported (elasticity 1.64, CI 1.21 to 2.08). H2 arena premium 3.80 (CI 1.05 to 13.73); shadow not supported (log distance -0.22, CI -0.68 to 0.24). H3 population interaction not supported (0.31, CI -0.22 to 0.84); arena x tour 7.0 (CI 2.3 to 21.8). H4 exploratory.
- Exploratory, labelled as such everywhere: the shadow appears without London and with distance to London controlled.
- Arena premium CI includes 1 in: cap 3 per act, without top 10 acts, 2000 to 2025, distinct performers, without England.
- Privacy: performer names published only for acts with 5+ documented UK events (754 acts); others keep their MusicBrainz id only. Venue names are public venues; no addresses kept.
- Literature verified online (WebSearch/WebFetch) for every reference in the paper. Florida and Jackson (2010) and Frith (2007) dropped: journal details could not be confirmed. Journal word limits for the cover note could not be checked (search budget exhausted).
- Coverage comparison: 2017 UK Live Music Census (Webster et al. 2018) venue counts for Glasgow (241), Newcastle-Gateshead (137), Oxford (110) vs MusicBrainz venues 57, 22, 6.

## Independent review (2026)

- Headline numbers recomputed from events_uk.csv and authorities.csv (7,615 concerts, 161 blank authorities, M1 1.64, M2 arena 3.80 [1.05, 13.73], arena shares, 70 of 167, median 120.5): all match results.json.
- Brennan and Webster (2011) confirmed as Scottish Music Review 2(1), 1 to 25 (Edinburgh Research Explorer PDF). Behr et al. (2016) author list confirmed (Glasgow eprints). Census figures (241, 137, 110; 24-hour snapshot 9 March 2017) confirmed from the report's executive summary.
- Popular Music word limit confirmed (10,000 words); Area and Journal of Cultural Geography author pages could not be loaded, limits left for the lead.
- Text softened where the arena premium was called robust and where tour completeness was asserted; studio falsification wording corrected; map, blog, collage, GIF label placement fixed.
