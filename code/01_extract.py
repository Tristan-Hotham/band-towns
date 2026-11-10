"""Stream the MusicBrainz event and place dumps (no extraction to disk) and keep compact records.

Outputs (scratch, deleted at the end of the build):
  events_all.jsonl.gz : every event, compact (id, type, cancelled, dates, held-at places, held-in areas, performers)
  places_uk.jsonl.gz  : places whose coordinates fall in a broad UK box or whose area carries a GB ISO 3166-2 code
  area_iso.json       : area id -> ISO 3166-2 codes seen on any place (to classify events located only by area)
"""
import tarfile, json, gzip, sys
from common import *

SCRATCH.mkdir(parents=True, exist_ok=True)


def stream(tar_path, member):
    t = tarfile.open(tar_path, "r|xz")
    for m in t:
        if m.name == member:
            f = t.extractfile(m)
            for line in f:
                yield json.loads(line)
            return


def area_c(a):
    if not a:
        return None
    return {"id": a.get("id"), "name": a.get("name"), "type": a.get("type"),
            "iso": a.get("iso-3166-2-codes") or a.get("iso-3166-1-codes") or []}


def do_events():
    n = 0
    with gzip.open(SCRATCH / "events_all.jsonl.gz", "wt") as out:
        for e in stream(EVENT_TAR, "mbdump/event"):
            places, areas, artists = [], [], []
            for r in e.get("relations", []):
                tt = r.get("target-type")
                if tt == "place" and r.get("type") == "held at":
                    p = r["place"]
                    c = p.get("coordinates") or {}
                    places.append({"id": p["id"], "name": p.get("name"), "type": p.get("type"),
                                   "lat": c.get("latitude"), "lon": c.get("longitude"),
                                   "area": area_c(p.get("area"))})
                elif tt == "area" and r.get("type") == "held in":
                    areas.append(area_c(r["area"]))
                elif tt == "artist":
                    a = r["artist"]
                    artists.append({"rel": r.get("type"), "id": a["id"], "name": a.get("name"),
                                    "atype": a.get("type"), "country": a.get("country")})
            ls = e.get("life-span") or {}
            rec = {"id": e["id"], "name": e.get("name"), "type": e.get("type"), "cancelled": e.get("cancelled"),
                   "begin": ls.get("begin"), "end": ls.get("end"), "places": places, "areas": areas,
                   "artists": artists, "nrel": len(e.get("relations", [])),
                   "setlist": bool(e.get("setlist"))}
            out.write(json.dumps(rec, ensure_ascii=False) + "\n")
            n += 1
    print("events", n, flush=True)


def do_places():
    n = k = 0
    area_iso = {}
    with gzip.open(SCRATCH / "places_uk.jsonl.gz", "wt") as out:
        for p in stream(PLACE_TAR, "mbdump/place"):
            n += 1
            a = p.get("area") or {}
            iso = a.get("iso-3166-2-codes") or []
            if a.get("id") and iso:
                area_iso[a["id"]] = iso
            c = p.get("coordinates") or {}
            lat, lon = c.get("latitude"), c.get("longitude")
            gb = any(str(x).startswith("GB") for x in iso)
            if (lat is not None and in_box(lat, lon)) or gb:
                nev = sum(1 for r in p.get("relations", []) if r.get("target-type") == "event")
                ls = p.get("life-span") or {}
                rec = {"id": p["id"], "name": p.get("name"), "type": p.get("type"), "lat": lat, "lon": lon,
                       "area": area_c(a), "address": p.get("address"), "begin": ls.get("begin"),
                       "end": ls.get("end"), "ended": ls.get("ended"), "n_event_rel": nev}
                out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                k += 1
    (SCRATCH / "area_iso.json").write_text(json.dumps(area_iso))
    print("places", n, "kept", k, flush=True)
    (SCRATCH / "place_total.json").write_text(json.dumps({"places_total": n, "places_kept": k}))


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "both"
    if which in ("events", "both"):
        do_events()
    if which in ("places", "both"):
        do_places()
