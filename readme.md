# Anki Deck: Japanese Cities

## Overview: 

Anki Shared Deck: https://ankiweb.net/shared/info/893061193

This Anki deck helps you memorize 815 Japanese cities/wards (sorted by population) — their names, readings, and locations.

**Why romaji?** Japan's road-sign ordinance puts place names in **Hepburn romaji** on guide/direction signs across national highways and NEXCO expressways nationwide (not only Tokyo). Recognizing a city by its romaji reading is directly useful for driving and navigation. Those signs drop long-vowel macrons (they read "Tokyo"/"Ome", not "Tōkyō"/"Ōme"), which matches the romaji style used here.

The deck is split into two subdecks so the romaji study is **optional and easy to filter out** if you only want the maps:

- **`Japanese Cities::Maps`** — a label-free map → name the city (geography recall).
- **`Japanese Cities::Romaji Names`** *(optional)* — Japanese name ⇄ romaji reading (both directions). Suspend or skip this subdeck if you don't want the reading drills.

## 🗾 Sponsor

This project is sponsored by **[Sansaku](https://sansaku.app)** — your all-in-one Japan travel super app.

Once you've learned these cities, go explore them. Sansaku helps you **discover events and travel spots, build custom travel itineraries, and more** — all in one place, with new features on the way.

🌐 **[sansaku.app](https://sansaku.app)**

## Building / Regenerating the Deck Data:

`build_maps.py` downloads the map tiles and rebuilds `jp_city_final.csv` from the source list `jp_city_v2.csv` in a single pass.

```bash
pip install -r requirements.txt
export GOOGLE_MAPS_API_KEY=your_key

python build_maps.py --dry-run         # preview, no network, no writes
python build_maps.py                   # build/refresh every city
python build_maps.py --skip-existing   # download only tiles not already present
python build_maps.py --fixed --clean   # regenerate just the corrected cities, removing old files
```

`jp_city_v2.csv` is the source of truth — edit it (not `jp_city_final.csv`) and re-run. Each city is one Static Maps request, so a full run bills 815. A real run rebuilds `jp_city_final.csv` at the end (use `--no-csv` to skip).

### Free alternative: Stadia Maps

`build_maps.py --provider stadia` uses [Stadia Maps](https://stadiamaps.com/), whose Static Maps API is **free for non-commercial use** (this deck qualifies). It needs coordinates, so it geocodes each city first — **two** requests per tile. The default style is `stamen_toner_background`, which is **label-free out of the box** (clean roads + coastlines, no city names), so it works for the deck's "no answer on the map" goal with no extra setup:

```bash
export STADIA_API_KEY=your_key
python build_maps.py --provider stadia --skip-existing
# or, for terrain instead of roads:
python build_maps.py --provider stadia --map-style stamen_terrain_background --skip-existing
```

Labelled built-in styles (`alidade_smooth`, `stamen_toner`, etc.) show city names; the tool warns if you pick one. For full control, create a custom style at [client.stadiamaps.com](https://client.stadiamaps.com/) and pass its slug via `--map-style`. The map carries a small Stadia/OSM attribution footer (license requirement), which is not a place label.

> Note: MapTiler's free tier does **not** include the Static Maps API (`--provider maptiler` returns HTTP 403 on free; it needs a paid plan). Stadia is the recommended free option.

## Map Customization:

The map file is generated with [Google Map API](https://developers.google.com/maps/documentation/), with map label customization. It hides the city and prefecture text and shows the train station and attraction. This aims to improve geography knowledge.

Map label customization made with https://mapstyle.withgoogle.com/, customized JSON file included. You can either build on current customization with import `gmap_style.json` on the website or build customization from scratch. 

Google Map static image URL format: 
```
https://maps.googleapis.com/maps/api/staticmap?key=YOUR_API_KEY&center=35.686929517283644,139.74463444470223&zoom=13&format=png&maptype=roadmap&style=feature:administrative.locality%7Celement:labels.text%7Cvisibility:off&style=feature:administrative.neighborhood%7Celement:geometry.fill%7Ccolor:0xff5848&style=feature:landscape.man_made%7Cvisibility:off&style=feature:poi%7Cvisibility:on&style=feature:poi.business%7Cvisibility:off&style=feature:poi.government%7Cvisibility:off&style=feature:poi.school%7Cvisibility:off&style=feature:road%7Celement:labels.icon%7Cvisibility:off&style=feature:road.arterial%7Cvisibility:off&style=feature:road.highway%7Celement:labels%7Cvisibility:off&style=feature:road.local%7Cvisibility:off&style=feature:transit%7Cvisibility:off&style=feature:transit.line%7Celement:geometry.fill%7Cvisibility:on&style=feature:transit.line%7Celement:labels.text%7Cvisibility:on&style=feature:transit.station.airport%7Cvisibility:on%7Cweight:1&style=feature:transit.station.airport%7Celement:geometry.fill%7Cvisibility:on&style=feature:transit.station.rail%7Cvisibility:on&style=feature:transit.station.rail%7Celement:geometry.fill%7Cvisibility:simplified&size=480x360&scale=2
```

Reference: Google Map API Static Maps [Developer Guide](https://developers.google.com/maps/documentation/maps-static/dev-guide)

### Zoom Level:
```
    1: World
    5: Landmass/continent
    10: City
    15: Streets
    20: Buildings
```

### Scale: 
```
    1: Regualr
    2: High resolution
    4: Premium(not available for regular api)
```

## Building the Anki Deck (.apkg):

Once the maps and `jp_city_final.csv` are generated (see above), build the importable deck:

```bash
pip install -r requirements.txt        # includes genanki
python build_deck.py                   # -> japan_city.apkg
```

`build_deck.py` reads `jp_city_final.csv`, bundles the referenced `map/*.png` files as media, and writes `japan_city.apkg` with the two subdecks described in the Overview. Romaji cards live entirely in the `Romaji Names` subdeck, so a user who only wants geography can suspend/delete that one subdeck without touching the maps.

## Deck Field:
1. Japanese Prefecture
2. Japanese City
3. Romaji Prefecture
4. Romaji City
5. Population (Survey: April 2018)
6. Image Html Code

Reference: Japanese City Ranking by Population ([Wikipedia](https://ja.wikipedia.org/wiki/%E6%97%A5%E6%9C%AC%E3%81%AE%E5%B8%82%E3%81%AE%E4%BA%BA%E5%8F%A3%E9%A0%86%E4%BD%8D))

Reference: [Creating Anki Flashcard with Audio and Pictures](http://womenlearnthai.com/index.php/creating-anki-flashcard-decks-with-audio-and-pictures/)

## Issue: 
1. Romaji readings: the original data came from Google Translate and had ~69 wrong readings (foreign readings, literal translations, `市` misread as "ichi"). These have been corrected; if you spot more, please open an issue or PR.
2. Possible inaccurate map: a wrong reading could place a map on the wrong location. Maps are regenerated from the corrected names; report any that still look off.

## Contribution: 
All contributions are welcome:
* Read the issues, For the project and do a Pull Request. 
* Request a new issue with creating a `New issue` with the `enhancement` tag. 
* Find any kind of errors in the deck and create a `New issue` with the details or fork the project and do a Pull Request.
* Suggest an improvement for the deck.
* Contribution [Code of Conduct](code-of-conduct.md)

## License:

[MIT](LICENSE)

