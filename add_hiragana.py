"""One-off: derive city + prefecture hiragana from Japan Post's KEN_ALL data and
cross-check against our corrected romaji.

Default run = REPORT ONLY (writes a proposed-readings file to /tmp, prints
unmatched + low-confidence rows). It does NOT modify jp_city_v2.csv. After the
flagged rows are confirmed, run with --write to apply (optionally with an
--overrides file of manual corrections).

    pip install -r requirements.txt   # needs requests + jaconv
    python add_hiragana.py            # report
    python add_hiragana.py --write    # apply to jp_city_v2.csv
"""

import argparse
import csv
import difflib
import io
import os
import sys
import zipfile

KEN_ALL_URL = "https://www.post.japanpost.jp/zipcode/dl/kogaki/zip/ken_all.zip"
CACHE = "/tmp/ken_all.csv"
PROPOSED = "/tmp/hira_proposed.csv"
SOURCE_CSV = "jp_city_v2.csv"
SIM_THRESHOLD = 0.70  # below this, the kana reading disagrees with our romaji -> flag


def load_kenall_lines():
    if not os.path.exists(CACHE):
        import requests
        print("downloading KEN_ALL ...")
        z = zipfile.ZipFile(io.BytesIO(requests.get(KEN_ALL_URL, timeout=120).content))
        name = next(n for n in z.namelist() if n.upper().endswith(".CSV"))
        open(CACHE, "w", encoding="utf-8").write(z.read(name).decode("shift_jis"))
    return open(CACHE, encoding="utf-8").read().splitlines()


def to_hira(halfwidth_kana):
    import jaconv
    return jaconv.kata2hira(jaconv.h2z(halfwidth_kana.strip(), kana=True, digit=False, ascii=False))


def build_maps(lines):
    """(pref_kanji, city_level_kanji) -> city hira ; pref_kanji -> pref hira.

    Designated cities have one row per ward with the city+ward kana concatenated
    (e.g. ヨコハマシツルミク). The city reading is the longest common prefix across
    all of that city's ward rows (ヨコハマシ). Ordinary cities have identical kana
    on every row, so the prefix is just that reading."""
    groups, pref = {}, {}
    for row in csv.reader(lines):
        if len(row) < 9:
            continue
        pkana, ckana, pk, ck = row[3], row[4], row[6], row[7]
        pref.setdefault(pk, to_hira(pkana))
        lvl = ck[:ck.rfind("市") + 1] if "市" in ck else ck
        groups.setdefault((pk, lvl), []).append(ckana.strip())
    city = {key: to_hira(os.path.commonprefix(kanas)) for key, kanas in groups.items()}
    return city, pref


def kana_to_romaji(hira):
    import jaconv
    return jaconv.kana2alphabet(hira)  # base() strips the shi/ku suffix on both sides


def base(s, sufs=("shi", "ku")):
    s = "".join(c for c in s.lower() if c.isalpha())
    for suf in sufs:
        if s.endswith(suf) and len(s) > len(suf):
            s = s[:-len(suf)]
    return s


def sim(a, b):
    return difflib.SequenceMatcher(None, a, b).ratio()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true", help="apply readings to jp_city_v2.csv")
    ap.add_argument("--overrides", help="CSV of manual fixes: prefecture_jp,city_jp,prefecture_hira,city_hira")
    args = ap.parse_args()

    try:
        import jaconv  # noqa: F401
    except ModuleNotFoundError:
        sys.exit("error: 'jaconv' is required (pip install -r requirements.txt)")

    city_map, pref_map = build_maps(load_kenall_lines())

    overrides = {}
    if args.overrides and os.path.exists(args.overrides):
        for r in csv.DictReader(open(args.overrides, encoding="utf-8")):
            overrides[(r["prefecture_jp"], r["city_jp"])] = (r["prefecture_hira"], r["city_hira"])

    rows = list(csv.DictReader(open(SOURCE_CSV, newline="", encoding="utf-8-sig")))
    unmatched, mismatched, results = [], [], []
    for r in rows:
        pk, ck = r["prefecture_jp"].strip(), r["city_jp"].strip()
        prom, crom = r["prefecture"].strip(), r["city"].strip()
        key = (pk, ck)
        ph = pref_map.get(pk, "")
        chl = ck[:ck.rfind("市") + 1] if "市" in ck else ck
        ch = city_map.get((pk, chl), "")
        status = "ok"
        if key in overrides:
            ph, ch = overrides[key]
            status = "override"
        elif not ch:
            status = "UNMATCHED"
            unmatched.append((pk, ck, crom))
        else:
            cs = sim(base(kana_to_romaji(ch)), base(crom))
            ps = sim(base(kana_to_romaji(ph), ("ken", "fu", "to", "do")),
                     base(prom, ("ken", "fu", "to", "do")))
            if cs < SIM_THRESHOLD or ps < SIM_THRESHOLD:
                status = f"MISMATCH city~{cs:.2f} pref~{ps:.2f}"
                mismatched.append((pk, ck, crom, ch, kana_to_romaji(ch), prom, ph, round(cs, 2), round(ps, 2)))
        results.append((pk, ck, prom, crom, ph, ch, status))

    with open(PROPOSED, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["prefecture_jp", "city_jp", "prefecture", "city", "prefecture_hira", "city_hira", "status"])
        w.writerows(results)

    print(f"\n=== {len(rows)} cities | matched {len(rows)-len(unmatched)} | "
          f"unmatched {len(unmatched)} | mismatch-flags {len(mismatched)} ===")
    print(f"proposed readings written to {PROPOSED}\n")
    if unmatched:
        print("UNMATCHED (no reading in KEN_ALL — likely renamed/merged):")
        for pk, ck, crom in unmatched:
            print(f"  {pk} {ck}  (romaji: {crom})")
    if mismatched:
        print("\nMISMATCH (kana reading disagrees with our romaji — review):")
        for pk, ck, crom, ch, chr_, prom, ph, cs, ps in mismatched:
            print(f"  {pk} {ck}: kana '{ch}' (~{chr_}) vs romaji '{crom}'  [city~{cs} pref~{ps}]")

    if args.write:
        if unmatched:
            sys.exit("\nrefusing --write: resolve UNMATCHED rows first (via --overrides)")
        proposed = {(p, c): (ph, ch) for p, c, _, _, ph, ch, _ in results}
        with open(SOURCE_CSV, newline="", encoding="utf-8-sig") as f:
            data = list(csv.reader(f))
        head = data[0]
        if "city_hira" not in head:
            head += ["prefecture_hira", "city_hira"]
        pj, cj = head.index("prefecture_jp"), head.index("city_jp")
        out = [head]
        for row in data[1:]:
            ph, ch = proposed[(row[pj], row[cj])]
            out.append(row[:5] + [ph, ch])  # keep first 5 source cols, append the two hira
        with open(SOURCE_CSV, "w", newline="", encoding="utf-8-sig") as f:
            csv.writer(f, lineterminator="\r\n").writerows(out)
        print(f"\nwrote prefecture_hira + city_hira into {SOURCE_CSV}")


if __name__ == "__main__":
    main()
