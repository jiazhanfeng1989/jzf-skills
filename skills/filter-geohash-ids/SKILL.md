---
name: filter-geohash-ids
description: Filter geohash id lists by duplicates, optional ISO country coverage, and conservative water/river removal. Use when the user needs removed-id marker files from a generic geohash list.
---

# filter-geohash-ids

Filter arbitrary geohash ids without modifying the input file.

## Inputs

- `--input path/to/file`, `--geoids "abc def,ghi"`, or `--stdin`.
- Optional `--iso` with comma- or space-separated ISO alpha-2/alpha-3 country codes.
- Optional `--out-dir`; default is the current directory.

## Behavior

- Removes duplicate occurrences after the first.
- With `--iso`, removes cells outside the target countries.
- Removes cells that do not intersect terrestrial land after subtracting Natural Earth ocean and lakes.
- River removal is off by default; enable it with `--river-buffer-deg`.

## Outputs

- `conservative_removed_geoids.txt`: TSV with columns `geoId`, `action`, and `reason`.
- `conservative_removed_geoids_only.txt`: one removed geoId per line, no header.

## Run

```bash
SKILL_DIR=/path/to/filter-geohash-ids
python3 -m venv .venv-filter-geohash-ids
.venv-filter-geohash-ids/bin/python -m pip install -r "$SKILL_DIR/scripts/requirements.txt"

.venv-filter-geohash-ids/bin/python "$SKILL_DIR/scripts/filter_geohash_ids.py" \
  --input /path/to/geohashes.txt \
  --iso SGP,MYS \
  --out-dir .
```

Useful flags: `--removed-out`, `--geoids-only-out`, `--ne-scale`, `--river-buffer-deg`, `--cache-dir`, `--sample-limit`.

## Agent Notes

- Do not read or paste large geohash files into chat; pass paths to the script.
- Summarize counts and output paths.
