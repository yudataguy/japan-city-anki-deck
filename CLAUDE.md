# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

Builds an Anki flashcard deck for memorizing 815 Japanese cities/wards (sorted by population), covering Japanese↔Romaji names and a label-stripped map for geography recall. Published deck: https://ankiweb.net/shared/info/893061193

## Build Pipeline

The deck is produced by two scripts, run in order:

1. **`build_maps.py`** reads `jp_city_v2.csv` (the hand-curated bilingual source list and the source of truth: `prefecture_jp, city_jp, prefecture, city, population`) and in one pass:
   - Downloads one map PNG per city into `map/` (backend chosen by `--provider`; see below).
   - Rebuilds `jp_city_final.csv`, deriving `html` (an `<img src="...">` tag) and `tag` (the prefecture) columns so the CSV's filenames always match the tiles on disk.
   - The committed `map/` tiles were generated with `--provider stadia` (label-free `stamen_watercolor`), so they are colored.
2. **`build_deck.py`** reads `jp_city_final.csv`, bundles the referenced `map/*.png` as media via `genanki`, and writes `japan_city.apkg` (~17 MB). It produces **two subdecks** — `Japanese Cities::Maps` (map → name) and `Japanese Cities::Romaji Names` (JP⇄romaji, both directions) — so the romaji study is optional/filterable. Each city becomes a map note + a names note (stable `guid`s keep re-imports from duplicating).

### Running the map builder

```bash
pip install -r requirements.txt        # just `requests`
export GOOGLE_MAPS_API_KEY=your_key

python build_maps.py --dry-run         # preview, no network, no writes
python build_maps.py                   # build/refresh every city (815 API requests)
python build_maps.py --skip-existing   # only download tiles not already present
python build_maps.py --fixed           # only the cities whose romaji was corrected
python build_maps.py --fixed --clean   # ...and delete the old misnamed PNGs
```

The API key is read from `GOOGLE_MAPS_API_KEY` (or `--api-key`); no source edits needed. Each city issues one Static Maps request — a full run bills 815. A real run rebuilds `jp_city_final.csv` at the end (skip with `--no-csv`); if any tile fails it leaves the CSV untouched so it never points at a missing image.

`--provider` selects the map backend. Providers are a small registry (`PROVIDERS`) of `fetch(requests, key, city, prefecture, zoom, style)` functions; `combo()`/filenames/CSV are provider-independent, so only the fetch differs.

- **`google`** (default) — one request/tile, inline label-hiding style. Env `GOOGLE_MAPS_API_KEY`.
- **`stadia`** — **free for non-commercial use** and the recommended free backend. Env `STADIA_API_KEY`. Geocodes then fetches static (**2 requests/tile**); static center is `lat,lon`. Default style `stamen_watercolor` is colored + label-free with no setup. Note the `stamen_*_background` slugs (toner/terrain) render even though Stadia's theme docs omit them. Built-in *road-map* styles (outdoors/osm_bright/alidade) all carry labels — a familiar colored label-free map needs a custom style. Verified working end-to-end June 2026.
- **`maptiler`** — env `MAPTILER_API_KEY`, but the **Static Maps API is NOT on the free tier** (returns HTTP 403; tiles + geocoding work, static does not). Needs a paid plan. Kept for completeness.

Non-google providers geocode by name (no coordinates in the source data) so cost 2 requests/tile. Label-hiding is a property of the *style*: `stadia` has label-free built-ins; `maptiler` needs a custom style. The tool warns when the chosen style is in the provider's `labeled` set. Keys load from a gitignored `.env` (`.env.example` is the template); `--limit N` caps tiles for cheap smoke tests and auto-skips the CSV rebuild.

## Critical conventions & gotchas

- **`jp_city_v2.csv` is the source of truth; `jp_city_final.csv` is derived.** Never hand-edit `jp_city_final.csv` — change `jp_city_v2.csv` and rebuild. The two CSVs differ in line endings: `jp_city_v2.csv` is **CRLF with a UTF-8 BOM**; `jp_city_final.csv` is **LF, no BOM**. Preserve these when editing programmatically (read v2 with `utf-8-sig`) or git will show the whole file as changed.
- **The `combo` string is the join key.** `combo = city + '+' + prefecture + '+japan'`, with spaces and `-` replaced by `+`, is used for both the PNG filename (`map/<combo>.png`) and the `html` column. Map filenames, the CSV `html` field, and the Anki media must all agree on this exact string. Fields are stripped first because trailing spaces (e.g. `"Kanagawa "`) appear in the raw v2 data.
- **City romaji had Google-Translate errors (now fixed).** 69 readings were wrong (foreign readings like 深川→"Shenzhen", literal translations like 中間→"Middle market", 市 misread as "ichi"). They are corrected in both CSVs and listed in `build_maps.py`'s `FIXED` table, which also drives `--fixed`/`--clean`. The corresponding `map/` tiles were generated from the bad search strings, so they are misnamed (and the 9 `wrong_location` ones show the wrong place) until regenerated with `--fixed`.
- **`zoom=12`, `scale=1`** in the builder. The example URL in `readme.md` shows `zoom=13`/`scale=2` for illustration; the committed `map/` images use the builder's values.

## Map label styling

Maps must hide city/prefecture labels so cards test geography rather than revealing the answer. How that's achieved depends on the provider:
- **stadia** (current committed maps): label-hiding is a property of the *style*. Default `stamen_watercolor` is colored + label-free; the `stamen_*_background` slugs also work even though Stadia's theme docs omit them. Familiar colored road-map styles all include labels, so a label-free version of those needs a custom style.
- **google**: label-hiding is inline in `build_maps.py`'s `GOOGLE_OPTION` string (URL-encoded `&style=...` params, which also keep transit + POIs). `gmap_style.json` is the human-editable equivalent — import at https://mapstyle.withgoogle.com/ to tweak, then re-export back into `GOOGLE_OPTION`.
