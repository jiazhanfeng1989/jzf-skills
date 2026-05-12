#!/usr/bin/env python3
"""Filter arbitrary geohash ids by duplicates, optional ISO countries, and water."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.request
from pathlib import Path
from typing import Any

from shapely import make_valid
from shapely.geometry import Polygon, box, shape
from shapely.ops import unary_union

GEOHASH_BASE32 = "0123456789bcdefghjkmnpqrstuvwxyz"
GEOHASH_DECODE = {char: idx for idx, char in enumerate(GEOHASH_BASE32)}

NE_BASE = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson"
NE_LAYER_FILES = {
    "countries": "admin_0_countries",
    "ocean": "ocean",
    "lakes": "lakes",
    "rivers": "rivers_lake_centerlines",
}
NE_SCALES = {"10m", "50m", "110m"}
DEFAULT_NE_SCALE = "10m"

# Natural Earth can omit small countries or territories.
FALLBACK_COUNTRY_BBOX = {
    "AD": (1.40, 42.42, 1.80, 42.68),
    "AND": (1.40, 42.42, 1.80, 42.68),
    "HK": (113.80, 22.10, 114.45, 22.60),
    "HKG": (113.80, 22.10, 114.45, 22.60),
    "LI": (9.45, 47.03, 9.66, 47.28),
    "LIE": (9.45, 47.03, 9.66, 47.28),
    "MO": (113.50, 22.08, 113.62, 22.24),
    "MAC": (113.50, 22.08, 113.62, 22.24),
    "MT": (14.15, 35.75, 14.60, 36.12),
    "MLT": (14.15, 35.75, 14.60, 36.12),
    "SG": (103.55, 1.15, 104.10, 1.50),
    "SGP": (103.55, 1.15, 104.10, 1.50),
}

def default_cache_dir() -> Path:
    base = os.environ.get("XDG_CACHE_HOME", str(Path.home() / ".cache"))
    return Path(base) / "filter-geohash-ids"


def natural_earth_url(name: str, scale: str) -> str:
    return f"{NE_BASE}/ne_{scale}_{NE_LAYER_FILES[name]}.geojson"


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    req = urllib.request.Request(url, headers={"User-Agent": "jzf-filter-geohash-ids/1.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        tmp.write_bytes(resp.read())
    tmp.replace(dest)


def ensure_cached(name: str, cache_dir: Path, scale: str) -> Path:
    url = natural_earth_url(name, scale)
    dest = cache_dir / Path(url).name
    if not dest.is_file():
        print(f"downloading {scale} {name} data", file=sys.stderr)
        download(url, dest)
    return dest


def load_geojson(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def ensure_valid(geom):
    return make_valid(geom) if not geom.is_valid else geom


def load_polygon_union(path: Path):
    geoms = []
    for feat in load_geojson(path).get("features", []):
        geom = shape(feat["geometry"])
        if not geom.is_empty:
            geoms.append(geom)
    return unary_union(geoms) if geoms else Polygon()


def load_rivers_buffered(path: Path, deg: float):
    geoms = []
    for feat in load_geojson(path).get("features", []):
        geom = shape(feat["geometry"])
        if not geom.is_empty:
            geoms.append(geom.buffer(deg))
    return unary_union(geoms) if geoms else Polygon()


def feature_alpha2(props: dict[str, Any]) -> str | None:
    for key in ("ISO_A2", "WB_A2"):
        value = props.get(key)
        if isinstance(value, str) and value.strip() and value != "-99":
            return value.strip().upper()
    return None


def feature_alpha3(props: dict[str, Any]) -> str | None:
    value = props.get("ADM0_A3")
    return value.strip().upper() if isinstance(value, str) and value.strip() else None


def parse_iso_list(raw: str) -> list[str]:
    parts = [part for part in re.split(r"[\s,]+", raw.strip()) if part]
    out: list[str] = []
    seen: set[str] = set()
    for part in parts:
        code = part.upper()
        if len(code) not in (2, 3) or not code.isalpha():
            raise ValueError(f"invalid ISO country code {part!r}")
        if code not in seen:
            seen.add(code)
            out.append(code)
    return out


def country_geometry(code: str, countries_path: Path):
    geoms = []
    for feat in load_geojson(countries_path).get("features", []):
        props = feat.get("properties") or {}
        if len(code) == 2 and feature_alpha2(props) != code:
            continue
        if len(code) == 3 and feature_alpha3(props) != code:
            continue
        geom = shape(feat["geometry"])
        if not geom.is_empty:
            geoms.append(geom)
    if not geoms:
        fallback_bbox = FALLBACK_COUNTRY_BBOX.get(code)
        if fallback_bbox is not None:
            return box(*fallback_bbox)
        raise ValueError(f"no Natural Earth country feature found for {code}")
    return unary_union(geoms)


def fallback_keep_geometry(codes: list[str]):
    geoms = [box(*FALLBACK_COUNTRY_BBOX[code]) for code in codes if code in FALLBACK_COUNTRY_BBOX]
    return unary_union(geoms) if geoms else Polygon()


def all_country_geometry(countries_path: Path):
    geoms = []
    for feat in load_geojson(countries_path).get("features", []):
        geom = shape(feat["geometry"])
        if not geom.is_empty:
            geoms.append(geom)
    geoms.extend(box(*bbox) for bbox in FALLBACK_COUNTRY_BBOX.values())
    return unary_union(geoms) if geoms else Polygon()


def geohash_cell_polygon(code: str):
    lat_range = [-90.0, 90.0]
    lon_range = [-180.0, 180.0]
    even_bit = True
    for char in code:
        value = GEOHASH_DECODE.get(char)
        if value is None:
            raise ValueError(f"invalid geohash character {char!r} in {code!r}")
        for mask in (16, 8, 4, 2, 1):
            if even_bit:
                mid = (lon_range[0] + lon_range[1]) / 2
                if value & mask:
                    lon_range[0] = mid
                else:
                    lon_range[1] = mid
            else:
                mid = (lat_range[0] + lat_range[1]) / 2
                if value & mask:
                    lat_range[0] = mid
                else:
                    lat_range[1] = mid
            even_bit = not even_bit
    return box(lon_range[0], lat_range[0], lon_range[1], lat_range[1])


def parse_geohash_ids(raw: str) -> list[str]:
    # Supports quoted entries, comma-separated lists, whitespace lists, and plain line files.
    quoted = re.findall(r'"([^"]+)"', raw.lower())
    if quoted:
        tokens = [token.strip() for token in quoted if token.strip()]
    else:
        tokens = re.findall(r"(?<![0-9a-z_])([0-9bcdefghjkmnpqrstuvwxyz]{1,12})(?![0-9a-z_])", raw.lower())
    invalid = [token for token in tokens if any(char not in GEOHASH_DECODE for char in token)]
    if invalid:
        raise ValueError(f"invalid geohash id(s): {', '.join(invalid[:20])}")
    return tokens


def read_geohash_ids(args: argparse.Namespace) -> list[str]:
    raw_parts = []
    if args.input:
        raw_parts.append(args.input.read_text(encoding="utf-8"))
    if args.geoids:
        raw_parts.append(args.geoids)
    if args.stdin:
        raw_parts.append(sys.stdin.read())
    if not raw_parts:
        raise ValueError("pass --input, --geoids, or --stdin")
    entries = parse_geohash_ids("\n".join(raw_parts))
    if not entries:
        raise ValueError("no geohash ids found")
    return entries


def dedupe_entries(entries: list[str]) -> tuple[list[str], list[str]]:
    seen: set[str] = set()
    unique: list[str] = []
    duplicates: list[str] = []
    for entry in entries:
        if entry in seen:
            duplicates.append(entry)
            continue
        seen.add(entry)
        unique.append(entry)
    return unique, duplicates


def build_geometries(codes: list[str], cache_dir: Path, scale: str, river_buffer_deg: float):
    countries_path = ensure_cached("countries", cache_dir, scale)
    ocean = ensure_valid(load_polygon_union(ensure_cached("ocean", cache_dir, scale)))
    lakes = ensure_valid(load_polygon_union(ensure_cached("lakes", cache_dir, scale)))
    rivers = ensure_valid(load_rivers_buffered(ensure_cached("rivers", cache_dir, scale), river_buffer_deg))
    water = ensure_valid(unary_union([ocean, lakes, rivers]))

    world_land = ensure_valid(all_country_geometry(countries_path))
    world_terrestrial = ensure_valid(world_land.difference(water))

    if not codes:
        return world_land, world_terrestrial, None, None

    target_land_parts = [ensure_valid(country_geometry(code, countries_path)) for code in codes]
    target_land = ensure_valid(unary_union(target_land_parts))
    fallback_keep = ensure_valid(fallback_keep_geometry(codes))
    keep_parts = [fallback_keep] if not fallback_keep.is_empty else []
    if keep_parts:
        target_land = ensure_valid(unary_union([target_land, *keep_parts]))
    target_terrestrial = ensure_valid(target_land.difference(water))
    if keep_parts:
        target_terrestrial = ensure_valid(unary_union([target_terrestrial, *keep_parts]))
    return world_land, world_terrestrial, target_land, target_terrestrial


def classify_removed(cell, has_iso: bool, world_terrestrial, target_land) -> str:
    if not world_terrestrial.intersects(cell):
        return "water_or_river"
    if has_iso and target_land is not None and not target_land.intersects(cell):
        return "outside_iso"
    return "water_or_river"


def write_marker_file(path: Path, rows: list[tuple[str, str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["geoId\taction\treason"]
    lines.extend(f"{geo_id}\t{action}\t{reason}" for geo_id, action, reason in rows)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_geoids_only_file(path: Path, rows: list[tuple[str, str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    geoids = [geo_id for geo_id, _, _ in rows]
    path.write_text("\n".join(geoids) + ("\n" if geoids else ""), encoding="utf-8")


def summarize(values: list[str], limit: int) -> str:
    shown = values[:limit]
    suffix = f", ... (+{len(values) - limit} more)" if len(values) > limit else ""
    return ", ".join(shown) + suffix


def run(args: argparse.Namespace) -> int:
    entries = read_geohash_ids(args)
    unique_entries, duplicate_removed = dedupe_entries(entries)
    codes = parse_iso_list(args.iso) if args.iso else []

    cache_dir = Path(args.cache_dir) if args.cache_dir else default_cache_dir()
    world_land, world_terrestrial, target_land, target_terrestrial = build_geometries(
        codes,
        cache_dir,
        args.ne_scale,
        args.river_buffer_deg,
    )
    keep_geometry = target_terrestrial if target_terrestrial is not None else world_terrestrial
    if keep_geometry is None or keep_geometry.is_empty:
        raise ValueError("keep geometry is empty")
    if world_land.is_empty or world_terrestrial.is_empty:
        raise ValueError("world terrestrial geometry is empty")

    filter_removed: list[tuple[str, str, str]] = []
    for geo_id in unique_entries:
        cell = geohash_cell_polygon(geo_id)
        if keep_geometry.intersects(cell):
            continue
        reason = classify_removed(cell, bool(codes), world_terrestrial, target_land)
        filter_removed.append((geo_id, "filter_remove", reason))

    rows = filter_removed + [
        (geo_id, "dedupe_duplicate", "duplicate_after_first_occurrence")
        for geo_id in duplicate_removed
    ]

    out_dir = args.out_dir.resolve()
    removed_out = args.removed_out.resolve() if args.removed_out else out_dir / "conservative_removed_geoids.txt"
    geoids_only_out = (
        args.geoids_only_out.resolve()
        if args.geoids_only_out
        else out_dir / "conservative_removed_geoids_only.txt"
    )
    write_marker_file(removed_out, rows)
    write_geoids_only_file(geoids_only_out, rows)

    action_counts: dict[str, int] = {}
    for _, action, _ in rows:
        action_counts[action] = action_counts.get(action, 0) + 1

    print(f"entries before: {len(entries)}")
    print(f"unique entries: {len(unique_entries)}")
    print(f"iso codes: {','.join(codes) if codes else '(none; world land only)'}")
    print(f"natural earth scale: {args.ne_scale}")
    print(f"removed total: {len(rows)}")
    for action in sorted(action_counts):
        print(f"{action}: {action_counts[action]}")
    if rows and args.sample_limit > 0:
        print(f"removed sample: {summarize([geo_id for geo_id, _, _ in rows], args.sample_limit)}")
    print(f"marker file written: {removed_out}")
    print(f"geoIds-only file written: {geoids_only_out}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="file containing geohash ids")
    parser.add_argument("--geoids", help="inline geohash ids, comma or whitespace separated")
    parser.add_argument("--stdin", action="store_true", help="read geohash ids from stdin")
    parser.add_argument("--iso", help="optional ISO alpha-2/alpha-3 country codes, comma or whitespace separated")
    parser.add_argument("--out-dir", type=Path, default=Path.cwd(), help="output directory")
    parser.add_argument("--removed-out", type=Path, help="override detailed TSV output path")
    parser.add_argument("--geoids-only-out", type=Path, help="override geoIds-only output path")
    parser.add_argument("--cache-dir", default="", help="Natural Earth GeoJSON cache directory")
    parser.add_argument(
        "--ne-scale",
        choices=sorted(NE_SCALES),
        default=DEFAULT_NE_SCALE,
        help=f"Natural Earth detail scale (default: {DEFAULT_NE_SCALE})",
    )
    parser.add_argument(
        "--river-buffer-deg",
        type=float,
        default=0.0,
        help="optional river line buffer in WGS84 degrees; default 0 avoids false removals near urban rivers",
    )
    parser.add_argument("--sample-limit", type=int, default=20, help="number of removed ids to print")
    args = parser.parse_args()
    try:
        return run(args)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
