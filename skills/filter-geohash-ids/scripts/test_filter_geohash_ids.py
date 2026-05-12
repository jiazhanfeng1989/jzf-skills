#!/usr/bin/env python3
"""Tests for filter_geohash_ids."""

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from shapely.geometry import mapping, box


SCRIPT_PATH = Path(__file__).with_name("filter_geohash_ids.py")
SPEC = importlib.util.spec_from_file_location("filter_geohash_ids", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
filter_geohash_ids = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(filter_geohash_ids)


class FilterGeohashIdsTest(unittest.TestCase):
    def test_iso_geometry_does_not_add_unlisted_land(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            countries_path = self.write_geojson(
                tmp / "countries.geojson",
                [
                    {
                        "type": "Feature",
                        "properties": {"ISO_A2": "TS", "WB_A2": "TS", "ADM0_A3": "TST"},
                        "geometry": mapping(box(20.0, 48.0, 30.0, 52.0)),
                    }
                ],
            )
            empty_path = self.write_geojson(tmp / "empty.geojson", [])
            paths = {
                "countries": countries_path,
                "ocean": empty_path,
                "lakes": empty_path,
                "rivers": empty_path,
            }
            original_ensure_cached = filter_geohash_ids.ensure_cached
            filter_geohash_ids.ensure_cached = lambda name, _cache_dir, _scale: paths[name]
            try:
                _, _, _, target_terrestrial = filter_geohash_ids.build_geometries(
                    ["TST"],
                    tmp,
                    "10m",
                    0.0,
                )
            finally:
                filter_geohash_ids.ensure_cached = original_ensure_cached

        self.assertIsNotNone(target_terrestrial)
        self.assertFalse(target_terrestrial.intersects(box(33.0, 44.0, 34.0, 45.0)))

    def write_geojson(self, path: Path, features: list[dict]) -> Path:
        path.write_text(
            json.dumps({"type": "FeatureCollection", "features": features}),
            encoding="utf-8",
        )
        return path


if __name__ == "__main__":
    unittest.main()
