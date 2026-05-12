---
name: create-iso-country-geohash
description: Generate geohash.data and optional geohash.html for one or more ISO alpha-2/alpha-3 countries using Natural Earth data. Use when the user needs country geohash coverage or a quick map preview.
---

# create-iso-country-geohash

Generate terrestrial geohash coverage for ISO country codes.

## Inputs

- `--iso`: comma- or space-separated ISO alpha-2/alpha-3 codes, such as `IN,DE` or `IND DEU`.
- Optional precision: `--base-level` and `--max-level` (defaults: `3` and `4`).
- Optional data scale: `--ne-scale 10m|50m|110m` (default: `10m`).

## Behavior

- Downloads Natural Earth countries, ocean, lakes, and river centerlines into a cache.
- Generates cells that intersect terrestrial country geometry after subtracting ocean and lakes.
- River removal is off by default; enable it with `--river-buffer-deg`.
- Deduplicates, sorts, and compacts complete 32-child geohash groups unless `--no-compact` is set.

## Outputs

- `geohash.data`: one geohash per line.
- `geohash.html`: optional Leaflet preview generated from `geohash.data`.

## Run

```bash
SKILL_DIR=/path/to/create-iso-country-geohash
python3 -m pip install -r "$SKILL_DIR/scripts/requirements.txt"

python3 "$SKILL_DIR/scripts/generate_country_geohash.py" --iso IND,DEU,FRA
python3 "$SKILL_DIR/scripts/generate_country_geohash.py" --iso IND --base-level 4 --max-level 6
python3 "$SKILL_DIR/scripts/geohash_data_to_map.py"
```

Useful flags: `--out`, `--out-dir`, `--no-compact`, `--cache-dir`, `--ne-scale`, `--river-buffer-deg`.

## Agent Notes

- Use user-supplied precision and output paths when provided.
- Generate the map only when requested or useful for preview.
- Report output paths and geohash count.
