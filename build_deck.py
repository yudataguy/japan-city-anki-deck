"""Build japan_city.apkg from jp_city_final.csv + the map/ tiles.

The deck is split into three subdecks so each study mode is optional:

    Japanese Cities::Maps            label-free map  -> name the city
    Japanese Cities::Romaji Names    Japanese name  <-> romaji (both directions)
    Japanese Cities::Hiragana Names  Japanese name  <-> hiragana (both directions)

A user who only wants one mode can suspend/delete the other subdecks. The
Hiragana subdeck is only built for rows that have a city_hira value. Run
build_maps.py first so the CSV + tiles exist.

    pip install -r requirements.txt
    python build_deck.py            # -> japan_city.apkg
"""

import argparse
import csv
import os
import sys

# Stable IDs (hardcoded so re-builds update the same deck/models, per genanki docs)
DECK_MAPS_ID = 1607392319
DECK_NAMES_ID = 1607392320
MODEL_MAP_ID = 1607392321
MODEL_NAMES_ID = 1607392322
DECK_HIRA_ID = 1607392323
MODEL_HIRA_ID = 1607392324

CSS = """
.card { font-family: sans-serif; font-size: 22px; text-align: center; color: black; background: white; }
.sub { color: #888; font-size: 16px; }
img { max-width: 100%; height: auto; }
hr { margin: 14px 0; }
"""

MAP_TEMPLATE = {
    "name": "Map",
    "qfmt": "{{Map}}",
    "afmt": '{{FrontSide}}<hr>{{CityRomaji}} <span class="sub">({{CityJP}})</span>'
            '<br><span class="sub">{{PrefectureRomaji}} / {{PrefectureJP}} · pop. {{Population}}</span>',
}
NAMES_TEMPLATES = [
    {
        "name": "JP to Romaji",
        "qfmt": '{{CityJP}}<br><span class="sub">{{PrefectureJP}}</span>',
        "afmt": '{{FrontSide}}<hr>{{CityRomaji}}<br><span class="sub">{{PrefectureRomaji}}</span>',
    },
    {
        "name": "Romaji to JP",
        "qfmt": '{{CityRomaji}}<br><span class="sub">{{PrefectureRomaji}}</span>',
        "afmt": '{{FrontSide}}<hr>{{CityJP}}<br><span class="sub">{{PrefectureJP}}</span>',
    },
]
HIRA_TEMPLATES = [
    {
        "name": "Kanji to Hiragana",
        "qfmt": '{{CityJP}}<br><span class="sub">{{PrefectureJP}}</span>',
        "afmt": '{{FrontSide}}<hr>{{CityHira}}<br><span class="sub">{{PrefectureHira}}</span>'
                '<br><span class="sub">{{CityRomaji}}</span>',
    },
    {
        "name": "Hiragana to Kanji",
        "qfmt": '{{CityHira}}<br><span class="sub">{{PrefectureHira}}</span>',
        "afmt": '{{FrontSide}}<hr>{{CityJP}}<br><span class="sub">{{PrefectureJP}}</span>'
                '<br><span class="sub">{{CityRomaji}}</span>',
    },
]


def src_from_html(html):
    """Pull the filename out of '<img src="X.png">'."""
    if 'src="' in html:
        return html.split('src="', 1)[1].split('"', 1)[0]
    return ""


def fmt_pop(value):
    try:
        return f"{int(float(value)):,}"
    except ValueError:
        return value.strip()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--csv", default="jp_city_final.csv")
    ap.add_argument("--map-dir", default="map")
    ap.add_argument("--out", default="japan_city.apkg")
    args = ap.parse_args()

    try:
        import genanki
    except ModuleNotFoundError:
        sys.exit("error: 'genanki' is required (pip install -r requirements.txt)")

    map_model = genanki.Model(
        MODEL_MAP_ID, "JP City Map",
        fields=[{"name": n} for n in ("CityJP", "CityRomaji", "PrefectureJP", "PrefectureRomaji", "Population", "Map")],
        templates=[MAP_TEMPLATE], css=CSS,
    )
    names_model = genanki.Model(
        MODEL_NAMES_ID, "JP City Names",
        fields=[{"name": n} for n in ("CityJP", "CityRomaji", "PrefectureJP", "PrefectureRomaji")],
        templates=NAMES_TEMPLATES, css=CSS,
    )
    hira_model = genanki.Model(
        MODEL_HIRA_ID, "JP City Hiragana",
        fields=[{"name": n} for n in ("CityJP", "CityHira", "PrefectureJP", "PrefectureHira", "CityRomaji")],
        templates=HIRA_TEMPLATES, css=CSS,
    )

    maps_deck = genanki.Deck(DECK_MAPS_ID, "Japanese Cities::Maps")
    names_deck = genanki.Deck(DECK_NAMES_ID, "Japanese Cities::Romaji Names")
    hira_deck = genanki.Deck(DECK_HIRA_ID, "Japanese Cities::Hiragana Names")

    media, missing, n, hira_n = [], [], 0, 0
    with open(args.csv, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cjp, crom = row["city_jp"].strip(), row["city"].strip()
            pjp, prom = row["prefecture_jp"].strip(), row["prefecture"].strip()
            chira, phira = row.get("city_hira", "").strip(), row.get("prefecture_hira", "").strip()
            pop = fmt_pop(row["population"])
            fname = src_from_html(row["html"])
            path = os.path.join(args.map_dir, fname)
            if fname and os.path.exists(path):
                media.append(path)
                map_field = row["html"]
            else:
                missing.append(crom or cjp)
                map_field = ""  # keep the card but without a broken image
            n += 1

            maps_deck.add_note(genanki.Note(
                model=map_model, fields=[cjp, crom, pjp, prom, pop, map_field],
                guid=genanki.guid_for(pjp, cjp, "map")))
            names_deck.add_note(genanki.Note(
                model=names_model, fields=[cjp, crom, pjp, prom],
                guid=genanki.guid_for(pjp, cjp, "names")))
            if chira:
                hira_deck.add_note(genanki.Note(
                    model=hira_model, fields=[cjp, chira, pjp, phira, crom],
                    guid=genanki.guid_for(pjp, cjp, "hira")))
                hira_n += 1

    genanki.Package([maps_deck, names_deck, hira_deck], media_files=media).write_to_file(args.out)
    print(f"wrote {args.out}: {n} cities, {len(media)} map images bundled, {hira_n} hiragana notes")
    if missing:
        print(f"WARNING: {len(missing)} cities missing a map tile (cards made image-less): "
              + ", ".join(missing[:15]) + (" ..." if len(missing) > 15 else ""))


if __name__ == "__main__":
    main()
