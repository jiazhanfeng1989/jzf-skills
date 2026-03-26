---
name: create-iso-country-geohash
description: Create geohash.data and optional geohash.html from one or more ISO country codes (alpha-2 or alpha-3, comma-separated). Script downloads Natural Earth 110m GeoJSON; configurable starting geohash length (default 3) and max split length for land/water (default 4); merges countries, dedupes, sorts, compacts full 32-sibling groups. Use for multi-country geohash lists and map preview without manual GIS files.
---

# create-iso-country-geohash

**Input**: One or more codes — **comma- or space-separated**, ISO **alpha-2** (`IN`, `DE`) or **alpha-3** / Natural Earth **`ADM0_A3`** (`IND`, `DEU`). Duplicate codes are ignored.

**Geohash length (configurable)**

| Flag | Meaning | Default |
|------|---------|---------|
| `--base-level` / `--base-prec` `N` | Starting string length (number of base-32 characters) | **3** |
| `--max-level` / `--max-prec` `N` | Maximum length when a cell is partly land and partly water (no finer splits) | **4** |

Constraint: `1 ≤ base ≤ max ≤ 12`. Omit both flags for the usual “3 + split to 4” behaviour.

**Outputs** (default names, cwd or `--out-dir`):

| File | Role |
|------|------|
| `geohash.data` | UTF-8, one geohash per line, sorted; lengths between base and max (then **compact** may shorten where all 32 siblings exist) |
| `geohash.html` | Leaflet map: grid + cell labels; **OpenStreetMap** tiles; load failures use a blank placeholder (hide OSM blocked graphic); `localhost` recommended for full tiles |

**Run** (repo root):

```bash
python3 -m pip install -r skills/create-iso-country-geohash/scripts/requirements.txt

# defaults: base 3, max 4
python3 skills/create-iso-country-geohash/scripts/generate_country_geohash.py --iso IND,DEU,FRA

# example: start at 4 chars, split up to 6
python3 skills/create-iso-country-geohash/scripts/generate_country_geohash.py --iso IND --base-level 4 --max-level 6

# map (reads geohash.data by default → geohash.html)
python3 skills/create-iso-country-geohash/scripts/geohash_data_to_map.py
```

Other flags: `--out` / `--out-dir`; `--no-compact`; `geohash_data_to_map.py [path/to.data] -o other.html`.

**Agent**: uppercase codes; install deps; forward user-supplied `--base-level` / `--max-level` if any; run generator then map script; confirm `geohash.data` and `geohash.html` exist.

**Caveats**: Alpha-3 uses `ADM0_A3`; alpha-2 uses `ISO_A2` / `WB_A2`. Rivers are approximated by buffered lines; 110m data is coarse.
