#!/usr/bin/env python3
"""
Generate geohash.data from one or more ISO country codes (alpha-2 or alpha-3).
Downloads Natural Earth 110m GeoJSON (countries, ocean, lakes, rivers) into a local cache.

Rules:
  - Default starting length 3; subdivide mixed land/water cells up to length 4 (overridable).
  - Drop cells with no intersection with terrestrial (country minus water).
  - Multiple codes: merge geohash sets, dedupe, sort; default output file geohash.data.
  - Starting length and max split length: --base-level / --max-level (or --base-prec / --max-prec).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.request
from pathlib import Path
from typing import Any

import geohash as ghlib
from shapely import make_valid
from shapely.geometry import Polygon, box, shape
from shapely.ops import unary_union

# Standard geohash base32 (child suffixes).
BASE32 = "0123456789bcdefghjkmnpqrstuvwxyz"

MIN_LAT, MAX_LAT = -90.0, 90.0
MIN_LON, MAX_LON = -180.0, 180.0

# Natural Earth vector (GeoJSON, no shapefile deps).
NE_BASE = (
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/"
    "master/geojson"
)
NE_SOURCES = {
    "countries": f"{NE_BASE}/ne_110m_admin_0_countries.geojson",
    "ocean": f"{NE_BASE}/ne_110m_ocean.geojson",
    "lakes": f"{NE_BASE}/ne_110m_lakes.geojson",
    "rivers": f"{NE_BASE}/ne_110m_rivers_lake_centerlines.geojson",
}


def default_cache_dir() -> Path:
    base = os.environ.get("XDG_CACHE_HOME", str(Path.home() / ".cache"))
    return Path(base) / "create-iso-country-geohash"


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "evplanner-create-iso-country-geohash/1.0"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        tmp.write_bytes(resp.read())
    tmp.replace(dest)


def load_geojson(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def ensure_cached(name: str, cache_dir: Path) -> Path:
    url = NE_SOURCES[name]
    dest = cache_dir / Path(url).name
    if not dest.is_file():
        print(f"Downloading {name} …", file=sys.stderr)
        download(url, dest)
    return dest


def feature_alpha2(props: dict[str, Any]) -> str | None:
    a2 = props.get("ISO_A2")
    if a2 and isinstance(a2, str) and a2.strip() and a2 != "-99":
        return a2.strip().upper()
    wb = props.get("WB_A2")
    if wb and isinstance(wb, str) and wb.strip() and wb != "-99":
        return wb.strip().upper()
    return None


def feature_alpha3(props: dict[str, Any]) -> str | None:
    """Natural Earth ADM0_A3 (matches ISO 3166-1 alpha-3 for most sovereignties)."""
    a3 = props.get("ADM0_A3")
    if a3 and isinstance(a3, str) and a3.strip():
        return a3.strip().upper()
    return None


def country_geometry(code: str, countries_path: Path):
    """Match country by alpha-2 (ISO_A2/WB_A2) or alpha-3 (ADM0_A3)."""
    data = load_geojson(countries_path)
    geoms = []
    for feat in data.get("features", []):
        props = feat.get("properties") or {}
        if len(code) == 2:
            if feature_alpha2(props) != code:
                continue
        elif len(code) == 3:
            if feature_alpha3(props) != code:
                continue
        else:
            raise SystemExit("country code must be length 2 or 3")
        g = shape(feat["geometry"])
        if g.is_empty:
            continue
        geoms.append(g)
    if not geoms:
        raise SystemExit(f"No country feature found for code {code!r} in Natural Earth.")
    return unary_union(geoms)


def load_polygon_union(path: Path):
    data = load_geojson(path)
    geoms = []
    for feat in data.get("features", []):
        g = shape(feat["geometry"])
        if g.is_empty:
            continue
        geoms.append(g)
    if not geoms:
        return Polygon()
    return unary_union(geoms)


def load_rivers_buffered(path: Path, deg: float = 0.012):
    """Approximate river area by buffering line geometries in degrees (WGS84)."""
    data = load_geojson(path)
    geoms = []
    for feat in data.get("features", []):
        g = shape(feat["geometry"])
        if g.is_empty:
            continue
        geoms.append(g.buffer(deg))
    if not geoms:
        return Polygon()
    return unary_union(geoms)


def ensure_valid(g):
    if not g.is_valid:
        g = make_valid(g)
    return g


def geohash_cell_polygon(code: str) -> Polygon:
    b = ghlib.bbox(code)
    return box(b["w"], b["s"], b["e"], b["n"])


def ensure_valid_lat(lat: float) -> float:
    return max(MIN_LAT, min(MAX_LAT, lat))


def ensure_valid_lon(lon: float) -> float:
    if lon > MAX_LON:
        return MIN_LON + lon - MAX_LON
    if lon < MIN_LON:
        return MAX_LON + lon - MIN_LON
    return lon


def geohashes_in_bbox(
    terrestrial,
    min_lat: float,
    min_lon: float,
    max_lat: float,
    max_lon: float,
    precision: int,
) -> list[str]:
    """Enumerate precision-N geohashes in bbox (SouthWest-style grid), keep those intersecting land."""
    hash_sw = ghlib.encode(min_lat, min_lon, precision)
    hash_ne = ghlib.encode(max_lat, max_lon, precision)
    box_sw = ghlib.bbox(hash_sw)
    box_ne = ghlib.bbox(hash_ne)

    per_lat = box_sw["n"] - box_sw["s"]
    per_lon = box_sw["e"] - box_sw["w"]
    if per_lat <= 0 or per_lon <= 0:
        return []

    lat_step = round((box_ne["s"] - box_sw["s"]) / per_lat)
    lon_diff = box_ne["w"] - box_sw["w"]
    if lon_diff < -180:
        lon_diff += 360
    elif lon_diff > 180:
        lon_diff -= 360
    lon_step = round(lon_diff / per_lon)
    lat_step = abs(lat_step)
    lon_step = abs(lon_step)

    center_lat = (box_sw["n"] + box_sw["s"]) / 2
    center_lon = (box_sw["e"] + box_sw["w"]) / 2

    seen: set[str] = set()
    out: list[str] = []

    for lat_i in range(0, int(lat_step) + 1):
        for lon_i in range(0, int(lon_step) + 1):
            nlat = ensure_valid_lat(center_lat + lat_i * per_lat)
            nlon = ensure_valid_lon(center_lon + lon_i * per_lon)
            h = ghlib.encode(nlat, nlon, precision)
            if h in seen:
                continue
            seen.add(h)
            cell = geohash_cell_polygon(h)
            if terrestrial.intersects(cell):
                out.append(h)

    return out


def collect_geohashes(
    code: str,
    terrestrial,
    max_prec: int,
    out: list[str],
    seen: set[str],
) -> None:
    cell = geohash_cell_polygon(code)
    if not terrestrial.intersects(cell):
        return

    if terrestrial.covers(cell):
        _append_if_new(out, seen, code)
        return

    land_part = cell.intersection(terrestrial)
    if land_part.is_empty:
        return

    ca, la = cell.area, land_part.area
    if ca > 0 and la / ca >= 1 - 1e-8:
        _append_if_new(out, seen, code)
        return

    if len(code) >= max_prec:
        _append_if_new(out, seen, code)
        return

    for ch in BASE32:
        collect_geohashes(code + ch, terrestrial, max_prec, out, seen)


def _append_if_new(out: list[str], seen: set[str], code: str) -> None:
    if code in seen:
        return
    seen.add(code)
    out.append(code)


def parse_iso_list(raw: str) -> list[str]:
    """Split comma/whitespace-separated codes; dedupe while keeping first-seen order."""
    parts = [p for p in re.split(r"[\s,]+", raw.strip()) if p]
    out: list[str] = []
    seen: set[str] = set()
    for p in parts:
        c = p.upper()
        if c in seen:
            continue
        seen.add(c)
        out.append(c)
    return out


def validate_code(c: str) -> None:
    if len(c) not in (2, 3) or not c.isalpha():
        sys.exit(f"Invalid country code {c!r}: need 2 (alpha-2) or 3 (alpha-3) letters A–Z.")


def geohashes_for_terrestrial(terrestrial, base_prec: int, max_prec: int) -> list[str]:
    if terrestrial.is_empty:
        return []
    min_lon, min_lat, max_lon, max_lat = terrestrial.bounds
    candidates = geohashes_in_bbox(
        terrestrial,
        min_lat,
        min_lon,
        max_lat,
        max_lon,
        base_prec,
    )
    if not candidates:
        return []
    out: list[str] = []
    seen: set[str] = set()
    for h in candidates:
        if len(h) != base_prec:
            continue
        collect_geohashes(h, terrestrial, max_prec, out, seen)
    return out


def compact_geohashes(hashes: set[str], min_len: int) -> list[str]:
    """
    If all 32 children (parent + one base32 char) are present, replace them with the parent.
    Repeat until stable. Does not shorten below min_len (e.g. 3).
    This recovers cases where float/boundary checks forced a full subdivide even though the
    whole parent cell is on land.
    """
    s = set(hashes)
    exp_cache: dict[str, set[str]] = {}

    def expected_children(parent: str) -> set[str]:
        if parent not in exp_cache:
            exp_cache[parent] = {parent + c for c in BASE32}
        return exp_cache[parent]

    changed = True
    while changed:
        changed = False
        max_len = max((len(h) for h in s), default=0)
        to_remove: set[str] = set()
        to_add: set[str] = set()
        for L in range(max_len, min_len, -1):
            by_parent: dict[str, set[str]] = {}
            for h in s:
                if len(h) != L:
                    continue
                p = h[:-1]
                if len(p) < min_len:
                    continue
                by_parent.setdefault(p, set()).add(h)
            for parent, children in by_parent.items():
                if len(children) == 32 and children == expected_children(parent):
                    to_remove.update(children)
                    to_add.add(parent)
                    changed = True
        s -= to_remove
        s |= to_add

    return sorted(s)


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Generate geohash.data from Natural Earth (one or more countries)."
    )
    ap.add_argument(
        "--iso",
        required=True,
        help="Country code(s): comma or space separated, alpha-2 (IN, DE) or alpha-3 (IND, DEU). "
        "Example: IND,DEU or 'IND DEU FRA'.",
    )
    ap.add_argument(
        "--out",
        default="geohash.data",
        help="Output file name or path (default: geohash.data under --out-dir)",
    )
    ap.add_argument(
        "--out-dir",
        default=".",
        help="Directory for output when --out is relative (default: current directory)",
    )
    ap.add_argument(
        "--cache-dir",
        default="",
        help="Cache for downloaded GeoJSON (default: XDG_CACHE_HOME or ~/.cache)",
    )
    ap.add_argument(
        "--base-prec",
        "--base-level",
        dest="base_prec",
        type=int,
        default=3,
        metavar="N",
        help="Starting geohash string length in characters (default: 3).",
    )
    ap.add_argument(
        "--max-prec",
        "--max-level",
        dest="max_prec",
        type=int,
        default=4,
        metavar="N",
        help="Max string length when splitting mixed land/water cells (default: 4).",
    )
    ap.add_argument(
        "--no-compact",
        action="store_true",
        help="Skip post-pass that merges 32 full siblings back to one parent geohash",
    )
    args = ap.parse_args()

    if args.base_prec < 1 or args.base_prec > 12:
        sys.exit("--base-level/--base-prec N must satisfy 1 <= N <= 12.")
    if args.max_prec < args.base_prec or args.max_prec > 12:
        sys.exit("--max-level/--max-prec must be >= base level and <= 12.")

    codes = parse_iso_list(args.iso)
    if not codes:
        sys.exit("No country codes in --iso.")
    for c in codes:
        validate_code(c)

    cache = Path(args.cache_dir) if args.cache_dir else default_cache_dir()

    countries_path = ensure_cached("countries", cache)
    ocean_path = ensure_cached("ocean", cache)
    lakes_path = ensure_cached("lakes", cache)
    rivers_path = ensure_cached("rivers", cache)

    ocean = ensure_valid(load_polygon_union(ocean_path))
    lakes = ensure_valid(load_polygon_union(lakes_path))
    rivers = ensure_valid(load_rivers_buffered(rivers_path))
    water = ensure_valid(unary_union([ocean, lakes, rivers]))

    merged: set[str] = set()
    for label in codes:
        land = ensure_valid(country_geometry(label, countries_path))
        terrestrial = ensure_valid(land.difference(water))
        part = geohashes_for_terrestrial(terrestrial, args.base_prec, args.max_prec)
        if not part:
            print(f"warning: no geohashes for {label} (empty after water clip?)", file=sys.stderr)
        merged.update(part)

    if not merged:
        sys.exit("No geohashes in combined output (check country codes).")

    before_n = len(merged)
    if args.no_compact:
        out_sorted = sorted(merged)
    else:
        out_sorted = compact_geohashes(merged, min_len=args.base_prec)
    after_n = len(out_sorted)
    if after_n < before_n:
        print(f"compact: {before_n} → {after_n} geohashes (full 32-child groups merged)", file=sys.stderr)

    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = Path(args.out_dir) / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(out_sorted) + "\n", encoding="utf-8")
    print(
        f"Wrote {len(out_sorted)} unique geohash ids from {len(codes)} code(s) to {out_path}",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
