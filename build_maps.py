"""Build the Japanese-city Anki map tiles and the final deck CSV.

Single entry point for the whole map step. It reads the source list
(jp_city_v2.csv), downloads map tiles into map/, and rebuilds jp_city_final.csv
(with the <img> html + tag columns) so the CSV's filenames always match the
tiles on disk.

Two backends via --provider (default: google):
  google   - Google Static Maps; one request per tile; inline label-hiding style.
  maptiler - free tier; geocodes the name then fetches a static tile (TWO
             requests per tile). Hiding place labels needs a custom style id
             (see --map-style); built-in styles still show city names.

Quick start:
    pip install -r requirements.txt
    export GOOGLE_MAPS_API_KEY=your_key      # or MAPTILER_API_KEY

    python build_maps.py                                   # Google, every city
    python build_maps.py --provider maptiler --map-style <id>
    python build_maps.py --skip-existing  # only download tiles not already present
    python build_maps.py --fixed          # only the cities whose names were corrected
    python build_maps.py --fixed --clean  # ...and delete the old misnamed PNGs
    python build_maps.py --dry-run        # preview actions, no network, no writes

By default it rebuilds jp_city_final.csv at the end of a real run; pass
--no-csv to skip that. --dry-run never writes anything.
"""

import argparse
import csv
import os
import sys
import time

SOURCE_CSV = "jp_city_v2.csv"
FINAL_CSV = "jp_city_final.csv"
MAP_DIR = "map"

DEFAULT_ZOOM = 12
TILE_SIZE = "480x360"
# Tiles are saved as JPEG to keep the deck small (watercolor compresses well).
# Set IMAGE_EXT = "png" for lossless. Providers are fetched as PNG and re-encoded.
IMAGE_EXT = "jpg"
JPEG_QUALITY = 65

# --- Google Static Maps (default provider) ---
GOOGLE_URL = "https://maps.googleapis.com/maps/api/staticmap?key="
# Map styling: hide city/road labels, keep transit + POIs so cards test
# geography rather than reading the answer off the map. See gmap_style.json
# for the human-editable equivalent (import at mapstyle.withgoogle.com).
GOOGLE_OPTION = "&format=png&maptype=roadmap&style=feature:administrative.locality%7Celement:labels.text%7Cvisibility:off&style=feature:administrative.neighborhood%7Celement:geometry.fill%7Ccolor:0xff5848&style=feature:landscape.man_made%7Cvisibility:off&style=feature:poi%7Cvisibility:on&style=feature:poi.business%7Cvisibility:off&style=feature:poi.government%7Cvisibility:off&style=feature:poi.school%7Cvisibility:off&style=feature:road%7Celement:labels.icon%7Cvisibility:off&style=feature:road.arterial%7Cvisibility:off&style=feature:road.highway%7Celement:labels%7Cvisibility:off&style=feature:road.local%7Cvisibility:off&style=feature:transit%7Cvisibility:off&style=feature:transit.line%7Celement:geometry.fill%7Cvisibility:on&style=feature:transit.line%7Celement:labels.text%7Cvisibility:on&style=feature:transit.station.airport%7Cvisibility:on%7Cweight:1&style=feature:transit.station.airport%7Celement:geometry.fill%7Cvisibility:on&style=feature:transit.station.rail%7Cvisibility:on&style=feature:transit.station.rail%7Celement:geometry.fill%7Cvisibility:simplified&size=" + TILE_SIZE + "&scale=1"

# --- MapTiler (free alternative) ---
# Built-in styles still show place labels. To match Google's label-hiding,
# create a custom style at cloud.maptiler.com with locality/place labels turned
# off and pass its id via --map-style.
MAPTILER_GEOCODE = "https://api.maptiler.com/geocoding/{q}.json?key={key}&country=jp&limit=1"
MAPTILER_STATIC = "https://api.maptiler.com/maps/{style}/static/{lon},{lat},{zoom}/{size}.png?key={key}"
MAPTILER_LABELED_STYLES = {"streets-v2", "basic-v2", "outdoor-v2", "topo-v2", "winter-v2", "satellite"}

# --- Stadia Maps (free for non-commercial use) ---
# Static API needs lat,lon (note the order, opposite of MapTiler), so we geocode
# first. Built-in styles mostly show labels; for the deck's "no answer on the
# map" goal use a custom style (labels off) via --map-style, or stamen_watercolor
# (label-free but artistic). Geocoding + static are both on the free tier.
STADIA_GEOCODE = "https://api.stadiamaps.com/geocoding/v1/search?text={q}&size=1&api_key={key}"
STADIA_STATIC = "https://tiles.stadiamaps.com/static/{style}.png?api_key={key}&center={lat},{lon}&zoom={zoom}&size={size}"
STADIA_LABELED_STYLES = {"alidade_smooth", "alidade_smooth_dark", "alidade_satellite",
                         "outdoors", "stamen_toner", "stamen_terrain", "osm_bright"}

# Cities whose romaji readings were corrected (Google Translate artifacts).
# (prefecture_jp, city_jp, old_romaji, wrong_location)
# old_romaji locates the stale PNG for --clean; wrong_location flags tiles that
# resolved to a different real place (foreign reading / literal translation).
FIXED = [
    ("千葉県", "市川市", "Ichigawa", False),
    ("愛知県", "一宮市", "Ichimiya", False),
    ("神奈川県", "大和市", "Yamatoichi", False),
    ("宮崎県", "都城市", "Utsukushi", False),
    ("東京都", "東久留米市", "Higokurume", False),
    ("愛知県", "江南市", "Gangnam-cho", True),
    ("鹿児島県", "薩摩川内市", "Satsuma Kawauchi", True),
    ("愛知県", "大府市", "Ouu-shi", False),
    ("愛知県", "日進市", "Nichin-shi", False),
    ("愛媛県", "四国中央市", "Shikoku", False),
    ("愛知県", "あま市", "Asama", False),
    ("東京都", "東大和市", "Higashiyamasa", False),
    ("茨城県", "龍ケ崎市", "Ryukezaki", False),
    ("奈良県", "香芝市", "Koshi-shi", False),
    ("京都府", "城陽市", "Joyang", False),
    ("山梨県", "甲斐市", "KA-shi", False),
    ("埼玉県", "桶川市", "Okagawa-shi", False),
    ("千葉県", "八街市", "Yachimi-shi", False),
    ("香川県", "三豊市", "Mifune", False),
    ("大阪府", "藤井寺市", "Fujiiji", False),
    ("愛知県", "愛西市", "AISI-SHI", False),
    ("栃木県", "下野市", "Shimotsu", False),
    ("沖縄県", "糸満市", "Itoumi", False),
    ("東京都", "福生市", "Fuuki", False),
    ("福島県", "二本松市", "Nipponmatsu", False),
    ("福岡県", "小郡市", "Ogura-city", False),
    ("福岡県", "直方市", "Nagata", False),
    ("滋賀県", "湖南市", "Hunan", True),
    ("宮城県", "塩竈市", "Shioga", False),
    ("京都府", "向日市", "Tomaruka", False),
    ("和歌山県", "海南市", "Hainan", True),
    ("茨城県", "小美玉市", "Komiyama", False),
    ("千葉県", "大網白里市", "Oimi Shirasato", False),
    ("茨城県", "下妻市", "Shimousare", False),
    ("茨城県", "稲敷市", "Inagaki", False),
    ("茨城県", "常陸大宮市", "Hitoshi Omiya", False),
    ("福岡県", "中間市", "Middle market", True),
    ("兵庫県", "篠山市", "Shinoyama", False),
    ("島根県", "雲南市", "Yunnan", True),
    ("愛媛県", "西予市", "Nishiichi", False),
    ("福岡県", "嘉麻市", "Koma", False),
    ("滋賀県", "米原市", "Mihara", False),
    ("茨城県", "行方市", "Megao", False),
    ("愛媛県", "東温市", "Tozen", False),
    ("秋田県", "北秋田市", "Hokuto Akita", False),
    ("山梨県", "中央市", "Central", True),
    ("奈良県", "宇陀市", "Uba", False),
    ("奈良県", "五條市", "Gogo", False),
    ("福島県", "本宮市", "Honma", False),
    ("新潟県", "胎内市", "Wessai", False),
    ("長野県", "東御市", "Tōgi", False),
    ("福岡県", "宮若市", "Miyawakaichi", False),
    ("栃木県", "那須烏山市", "Nasu Osan-shi", False),
    ("熊本県", "上天草市", "Uesakusa", False),
    ("奈良県", "御所市", "Gosho-shi", False),
    ("岩手県", "八幡平市", "Hachimantairi", False),
    ("山口県", "美祢市", "Misaki", False),
    ("秋田県", "にかほ市", "Nakaho-shi", False),
    ("北海道", "深川市", "Shenzhen", True),
    ("北海道", "士別市", "Sobetsu-shi", False),
    ("山形県", "尾花沢市", "Ozawaza", False),
    ("鹿児島県", "西之表市", "Nishinooma", False),
    ("北海道", "赤平市", "Akabane", True),
    ("北海道", "歌志内市", "Utashinaichi", False),
    # romanization touch-ups (macron-less spelling; also fixes geocoding)
    ("京都府", "木津川市", "Kizukawa-shi", False),
    ("滋賀県", "栗東市", "Rito", False),
    ("東京都", "青梅市", "Oume", False),
    ("福井県", "大野市", "Oono", False),
    ("広島県", "大竹市", "Ootake", False),
    # caught by the hiragana cross-check (same-kanji-different-reading)
    ("兵庫県", "三田市", "Mita", False),
    ("滋賀県", "甲賀市", "Koga", False),
    ("島根県", "大田市", "Ota-shi", False),
]

FIXED_KEYS = {(p, c) for p, c, _, _ in FIXED}
WRONG_LOCATION_KEYS = {(p, c) for p, c, _, w in FIXED if w}
OLD_ROMAJI = {(p, c): old for p, c, old, _ in FIXED}


def combo(city, prefecture):
    """Reproduce the search string / filename key: '<city>+<pref>+japan'."""
    s = f"{city.strip()}+{prefecture.strip()}+japan"
    return s.replace(" ", "+").replace("-", "+")


def encode(content):
    """Re-encode fetched PNG bytes to the configured tile format (JPEG by default,
    quality JPEG_QUALITY) so the deck stays small. PNG passes through untouched."""
    if IMAGE_EXT == "png":
        return content
    from io import BytesIO
    from PIL import Image
    im = Image.open(BytesIO(content)).convert("RGB")
    buf = BytesIO()
    im.save(buf, "JPEG", quality=JPEG_QUALITY, optimize=True)
    return buf.getvalue()


def _check_image(resp, what="request"):
    if resp.status_code != 200 or not resp.headers.get("Content-Type", "").startswith("image"):
        raise RuntimeError(f"{what} HTTP {resp.status_code} {resp.text[:120]!r}")


def _get(requests, url, tries=4):
    """GET with retry/backoff on rate-limit (429) and transient 5xx errors."""
    delay = 1.0
    for i in range(tries):
        try:
            r = requests.get(url, timeout=30)
        except requests.RequestException:
            if i == tries - 1:
                raise
            time.sleep(delay)
            delay *= 2
            continue
        if r.status_code in (429, 500, 502, 503, 504) and i < tries - 1:
            time.sleep(delay)
            delay *= 2
            continue
        return r
    return r


def google_fetch(requests, key, city, prefecture, zoom, style):
    """Google geocodes the place-name center implicitly — one request per tile."""
    center = combo(city, prefecture)
    r = _get(requests, GOOGLE_URL + key + "&center=" + center + "&zoom=" + str(zoom) + GOOGLE_OPTION)
    _check_image(r)
    return r.content


def maptiler_fetch(requests, key, city, prefecture, zoom, style):
    """Free alternative — TWO requests per tile: geocode the name to lon/lat,
    then fetch a static image. Label-hiding depends on `style` being a custom
    MapTiler style with place labels turned off."""
    q = requests.utils.quote(f"{city.strip()}, {prefecture.strip()}, Japan")
    g = _get(requests, MAPTILER_GEOCODE.format(q=q, key=key))
    if g.status_code != 200:
        raise RuntimeError(f"geocode HTTP {g.status_code} {g.text[:120]!r}")
    features = g.json().get("features") or []
    if not features:
        raise RuntimeError("geocode: no match")
    lon, lat = features[0]["center"]
    r = _get(requests, MAPTILER_STATIC.format(style=style, lon=lon, lat=lat, zoom=zoom, size=TILE_SIZE, key=key))
    _check_image(r)
    return r.content


def stadia_fetch(requests, key, city, prefecture, zoom, style):
    """Free for non-commercial use — TWO requests per tile (geocode then static).
    Static center is lat,lon. Label-hiding depends on `style` (custom style with
    labels off, or stamen_watercolor)."""
    q = requests.utils.quote(f"{city.strip()}, {prefecture.strip()}, Japan")
    g = _get(requests, STADIA_GEOCODE.format(q=q, key=key))
    if g.status_code != 200:
        raise RuntimeError(f"geocode HTTP {g.status_code} {g.text[:120]!r}")
    features = g.json().get("features") or []
    if not features:
        raise RuntimeError("geocode: no match")
    lon, lat = features[0]["geometry"]["coordinates"]
    r = _get(requests, STADIA_STATIC.format(style=style, lat=lat, lon=lon, zoom=zoom, size=TILE_SIZE, key=key))
    _check_image(r)
    return r.content


# provider registry: env var, default style, fetch fn, requests/tile, label set
PROVIDERS = {
    "google":   {"env": "GOOGLE_MAPS_API_KEY", "style": None,             "fetch": google_fetch,   "reqs": 1, "labeled": set()},
    "maptiler": {"env": "MAPTILER_API_KEY",    "style": "streets-v2",     "fetch": maptiler_fetch, "reqs": 2, "labeled": MAPTILER_LABELED_STYLES},
    "stadia":   {"env": "STADIA_API_KEY",      "style": "stamen_watercolor", "fetch": stadia_fetch, "reqs": 2, "labeled": STADIA_LABELED_STYLES},
}


def load_rows(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def select_targets(rows, mode):
    if mode == "all":
        return rows
    keys = WRONG_LOCATION_KEYS if mode == "wrong-location" else FIXED_KEYS
    return [r for r in rows if (r["prefecture_jp"], r["city_jp"]) in keys]


def rebuild_final_csv(rows, path):
    """Derive jp_city_final.csv (html + tag columns) from the source rows.
    Carries prefecture_hira/city_hira through from the source if present."""
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["prefecture_jp", "city_jp", "prefecture", "city", "population",
                    "prefecture_hira", "city_hira", "html", "tag"])
        for r in rows:
            pe, ce = r["prefecture"].strip(), r["city"].strip()
            try:
                pop = str(int(float(r["population"])))
            except ValueError:
                pop = r["population"].strip()
            html = f'<img src="{combo(ce, pe)}.{IMAGE_EXT}">'
            w.writerow([r["prefecture_jp"].strip(), r["city_jp"].strip(), pe, ce, pop,
                        r.get("prefecture_hira", "").strip(), r.get("city_hira", "").strip(), html, pe])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--csv", default=SOURCE_CSV, help=f"source list (default: {SOURCE_CSV})")
    ap.add_argument("--out", default=MAP_DIR, help=f"tile output dir (default: {MAP_DIR})")
    ap.add_argument("--final-csv", default=FINAL_CSV, help=f"deck CSV to rebuild (default: {FINAL_CSV})")
    ap.add_argument("--provider", choices=sorted(PROVIDERS), default="google",
                    help="map backend (default: google)")
    ap.add_argument("--api-key", default="", help="overrides the provider's env var")
    ap.add_argument("--map-style", default="",
                    help="provider style id (maptiler: a custom style that hides place labels)")
    ap.add_argument("--zoom", type=int, default=DEFAULT_ZOOM, help=f"zoom level (default: {DEFAULT_ZOOM})")
    group = ap.add_mutually_exclusive_group()
    group.add_argument("--fixed", action="store_true", help="only the corrected cities")
    group.add_argument("--wrong-location-only", action="store_true",
                       help="only the cities that resolved to the wrong place")
    ap.add_argument("--clean", action="store_true", help="delete the old misnamed PNG after success")
    ap.add_argument("--skip-existing", action="store_true", help="skip tiles already on disk")
    ap.add_argument("--limit", type=int, default=0, help="cap to the first N tiles (0 = no cap; for smoke tests)")
    ap.add_argument("--delay", type=float, default=0.0, help="seconds to sleep between cities (rate-limit friendly)")
    ap.add_argument("--no-csv", action="store_true", help="do not rebuild the final CSV")
    ap.add_argument("--dry-run", action="store_true", help="print actions, no network, no writes")
    args = ap.parse_args()

    prov = PROVIDERS[args.provider]
    api_key = args.api_key or os.environ.get(prov["env"], "")
    style = args.map_style or prov["style"]

    if not api_key and not args.dry_run:
        sys.exit(f"error: set {prov['env']} (or pass --api-key), or use --dry-run")
    if not args.dry_run:
        try:
            import requests
        except ModuleNotFoundError:
            sys.exit("error: 'requests' is required (pip install -r requirements.txt)")
        if IMAGE_EXT != "png":
            try:
                import PIL  # noqa: F401
            except ModuleNotFoundError:
                sys.exit("error: 'Pillow' is required for JPEG tiles (pip install -r requirements.txt)")
        os.makedirs(args.out, exist_ok=True)

    rows = load_rows(args.csv)
    mode = "wrong-location" if args.wrong_location_only else "fixed" if args.fixed else "all"
    targets = select_targets(rows, mode)
    if args.limit > 0:
        targets = targets[:args.limit]
    print(f"provider={args.provider}  style={style}  mode={mode}  "
          f"targets={len(targets)}  requests~{len(targets) * prov['reqs']}")
    if style in prov["labeled"]:
        print(f"  WARNING: '{style}' shows place labels — set --map-style to a custom "
              "label-free style, or cards will reveal the answer")

    ok = skipped = failed = 0
    fails = []
    total = len(targets)
    for i, r in enumerate(targets, 1):
        key = (r["prefecture_jp"], r["city_jp"])
        center = combo(r["city"], r["prefecture"])
        new_path = os.path.join(args.out, center + "." + IMAGE_EXT)
        old_path = os.path.join(args.out, combo(OLD_ROMAJI.get(key, r["city"]), r["prefecture"]) + "." + IMAGE_EXT)

        if args.skip_existing and os.path.exists(new_path):
            skipped += 1
            continue
        if args.dry_run:
            note = "  [WRONG-LOCATION]" if key in WRONG_LOCATION_KEYS else ""
            print(f"WOULD  {r['city_jp']} -> {new_path}{note}")
            if args.clean and old_path != new_path:
                print(f"         delete {old_path}")
            continue

        # fetch() validates the response is really an image and raises otherwise,
        # so a failed request can't silently save an error page as a .png.
        try:
            content = encode(prov["fetch"](requests, api_key, r["city"], r["prefecture"], args.zoom, style))
        except Exception as exc:
            print(f"FAIL  [{i}/{total}] {r['city_jp']} ({r['city']}): {exc}")
            failed += 1
            fails.append(f"{r['city_jp']}/{r['city']}")
            continue
        with open(new_path, "wb") as f:
            f.write(content)
        ok += 1
        if args.clean and old_path != new_path and os.path.exists(old_path):
            os.remove(old_path)
        if i % 50 == 0 or i == total:
            print(f"  progress {i}/{total}  ok={ok} failed={failed} skipped={skipped}", flush=True)
        if args.delay:
            time.sleep(args.delay)

    print(f"tiles: ok={ok} failed={failed} skipped={skipped}")
    if fails:
        print("failed cities: " + ", ".join(fails))

    if args.dry_run:
        print(f"(dry-run) would rebuild {args.final_csv} from {len(rows)} rows")
    elif args.limit:
        print("skipped CSV rebuild (--limit: partial tile set, would point html at missing tiles)")
    elif args.no_csv:
        print("skipped CSV rebuild (--no-csv)")
    elif ok == 0:
        print(f"NOT rebuilding {args.final_csv}: no tiles succeeded")
    else:
        rebuild_final_csv(rows, args.final_csv)
        msg = f"rebuilt {args.final_csv} ({len(rows)} rows)"
        if failed:
            msg += f"  — WARNING: {failed} tile(s) missing; re-run with --skip-existing to fill gaps"
        print(msg)


if __name__ == "__main__":
    main()
