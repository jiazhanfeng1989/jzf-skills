---
name: filter-geohash-ids
description: Filter arbitrary geohash id lists by duplicate ids, optional ISO country coverage, and conservative water/river removal. Use when the user provides geohash ids and wants conservative_removed_geoids.txt plus conservative_removed_geoids_only.txt, or asks to remove duplicate, outside-country, ocean, sea, lake, or river geohashes from a generic list.
---

# filter-geohash-ids

Use this skill for generic geohash lists, not EV Planner `const_{region}_geoids.go` files. For EV Planner region constants, prefer the project-specific `filter-region-geohashes` skill.

## Inputs

- Geohash ids from one of:
  - `--input path/to/file`
  - `--geoids "abc def,ghi"`
  - `--stdin`
- Optional `--iso` with comma- or whitespace-separated ISO alpha-2/alpha-3 country codes.
- Optional `--out-dir`; defaults to the current working directory.

The parser accepts plain lines, comma-separated ids, and quoted Go-style entries.

## Behavior

- Marks repeated ids with `action=dedupe_duplicate`, keeping the first occurrence.
- If `--iso` is provided, marks cells that intersect land but not the target ISO countries with `reason=outside_iso`.
- Marks cells that do not intersect terrestrial land after subtracting Natural Earth ocean, lakes, and buffered rivers with `reason=water_or_river`.
- Uses Natural Earth `10m` by default. `--ne-scale 50m` or `--ne-scale 110m` are available but less precise around coasts and islands.
- Adds conservative fallback bounding boxes for small countries/territories such as `SGP`, `HKG`, `MAC`, `MLT`, `AND`, and `LIE`.
- Does not modify the input file. It only writes output marker files.

## Outputs

The script always writes:

- `conservative_removed_geoids.txt`: TSV with columns `geoId`, `action`, and `reason`.
- `conservative_removed_geoids_only.txt`: one removed geoId per line, no header.

`action` is the operation type: `filter_remove` or `dedupe_duplicate`.
`reason` is the delete reason: `outside_iso`, `water_or_river`, or `duplicate_after_first_occurrence`.

## Run

From the skill repository root:

```bash
python3 -m venv /tmp/jzf-filter-geohash-ids-venv
/tmp/jzf-filter-geohash-ids-venv/bin/python -m pip install -r skills/filter-geohash-ids/scripts/requirements.txt

/tmp/jzf-filter-geohash-ids-venv/bin/python skills/filter-geohash-ids/scripts/filter_geohash_ids.py \
  --input /path/to/geohashes.txt \
  --iso SGP,MYS \
  --out-dir .
```

Without ISO filtering, only duplicates and global water/river cells are marked:

```bash
/tmp/jzf-filter-geohash-ids-venv/bin/python skills/filter-geohash-ids/scripts/filter_geohash_ids.py \
  --input /path/to/geohashes.txt \
  --out-dir .
```

Other useful flags: `--removed-out`, `--geoids-only-out`, `--ne-scale`, `--river-buffer-deg`, `--cache-dir`, `--sample-limit`.

## Agent Notes

- Keep output files in the current project directory unless the user asks for another path.
- Do not read or paste large geohash files into chat; pass paths to the script.
- Summarize counts by action and mention the two output file paths.
