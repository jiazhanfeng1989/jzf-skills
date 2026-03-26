#!/usr/bin/env python3
"""Pack a geohash list file into a single offline HTML map (Leaflet, bbox decode in-page)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser(description="Build self-contained HTML map from geohash list.")
    ap.add_argument(
        "data",
        nargs="?",
        type=Path,
        default=Path("geohash.data"),
        help="Input list (default: geohash.data, one hash per line)",
    )
    ap.add_argument(
        "-o",
        "--out",
        type=Path,
        default=Path("geohash.html"),
        help="Output HTML (default: geohash.html)",
    )
    args = ap.parse_args()

    if not args.data.is_file():
        raise SystemExit(f"Missing input file: {args.data}")

    text = args.data.read_text(encoding="utf-8")
    hashes = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not hashes:
        raise SystemExit("No geohashes in file.")

    out = args.out
    payload = json.dumps(hashes, ensure_ascii=False)
    # Break "</script>" sequences in JSON text so embedded payload cannot close a script tag (HTML parsing).
    payload = payload.replace("<", "\\u003c").replace(">", "\\u003e")
    html = TEMPLATE.replace("__GEOHASH_JSON__", payload)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"Wrote {out} ({len(hashes)} cells) from {args.data}")


TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Geohash coverage</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.css" crossorigin="" />
  <style>
    * { box-sizing: border-box; }
    html, body { height: 100%; margin: 0; font-family: "SF Pro Text", "Segoe UI", system-ui, sans-serif; }
    #map { height: 100%; width: 100%; }
    /* Vertical toolbar, left edge, vertically centered (keeps map center clear) */
    .toolbar {
      position: absolute;
      z-index: 1000;
      left: 12px;
      top: 50%;
      right: auto;
      transform: translateY(-50%);
      display: flex;
      flex-direction: column;
      align-items: stretch;
      gap: 8px;
      width: min(132px, 28vw);
      padding: 10px 10px;
      border-radius: 10px;
      background: rgba(255, 255, 255, 0.93);
      box-shadow: 0 2px 14px rgba(0, 0, 0, 0.14);
      font-size: 12px;
    }
    .toolbar .count {
      font-variant-numeric: tabular-nums;
      font-weight: 650;
      color: #1a5fb4;
      text-align: center;
      font-size: 11px;
      line-height: 1.3;
    }
    .toolbar button {
      width: 100%;
      padding: 6px 8px;
      border: none;
      border-radius: 6px;
      background: #1a5fb4;
      color: #fff;
      font-size: 11px;
      cursor: pointer;
    }
    .toolbar button.secondary { background: #555; }
    .toolbar .help-wrap {
      position: relative;
      width: 100%;
    }
    .toolbar details.help > summary {
      cursor: pointer;
      list-style: none;
      padding: 6px 8px;
      border-radius: 6px;
      background: #e8e8e8;
      color: #444;
      font-size: 11px;
      user-select: none;
      text-align: center;
    }
    .toolbar details.help > summary::-webkit-details-marker { display: none; }
    .toolbar .help-body {
      position: absolute;
      left: calc(100% + 8px);
      top: 0;
      right: auto;
      z-index: 1001;
      width: min(260px, 72vw);
      padding: 8px 10px;
      border-radius: 8px;
      background: #fff;
      box-shadow: 0 4px 18px rgba(0, 0, 0, 0.18);
      font-size: 11px;
      line-height: 1.45;
      color: #444;
    }
    /* Cell-center labels (Leaflet permanent tooltips) */
    .leaflet-tooltip.geohash-oncell {
      margin: 0 !important;
      padding: 1px 4px !important;
      background: rgba(255, 255, 255, 0.92) !important;
      border: 1px solid rgba(196, 30, 58, 0.4) !important;
      border-radius: 3px !important;
      box-shadow: 0 1px 2px rgba(0, 0, 0, 0.12) !important;
      color: #1a1a1a !important;
      font-size: clamp(9px, 1.1vw, 11px) !important;
      font-weight: 650 !important;
      font-family: ui-monospace, "Cascadia Code", "SF Mono", Menlo, monospace !important;
      letter-spacing: -0.02em;
      white-space: nowrap !important;
      pointer-events: none !important;
    }
    .leaflet-tooltip.geohash-oncell::before { display: none !important; }
  </style>
</head>
<body>
  <div class="toolbar" id="toolbar">
    <span class="count"><span id="count">0</span> cells</span>
    <button type="button" id="fit">Fit all</button>
    <button type="button" id="toggle" class="secondary">Toggle grid</button>
    <button type="button" id="labels" class="secondary">Always show labels</button>
    <div class="help-wrap">
      <details class="help">
        <summary>Help</summary>
        <div class="help-body">
          Labels show each geohash; click a cell for a popup. Shown at zoom ≥ 8, or force with the labels button.
          Basemap: OpenStreetMap. Data is embedded. If tiles fail from file://, failed cells show a plain placeholder; use <code>http://localhost/…</code> (e.g. python3 -m http.server) for normal OSM tiles.
        </div>
      </details>
    </div>
  </div>
  <div id="map"></div>
  <script src="https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.js" crossorigin=""></script>
  <script id="geohash-payload" type="application/json">__GEOHASH_JSON__</script>
  <script>
  (function () {
    const GEOHASHES = JSON.parse(document.getElementById("geohash-payload").textContent);
    const BASE32 = "0123456789bcdefghjkmnpqrstuvwxyz";
    /** @returns {[number,number,number,number]} minLat, minLon, maxLat, maxLon */
    function decodeBbox(geohash) {
      let even = true;
      const lat = [-90, 90];
      const lon = [-180, 180];
      for (let i = 0; i < geohash.length; i++) {
        const cd = BASE32.indexOf(geohash[i]);
        if (cd < 0) throw new Error("invalid geohash");
        for (let mask = 16; mask >= 1; mask >>= 1) {
          if (even) {
            const mid = (lon[0] + lon[1]) / 2;
            if (cd & mask) lon[0] = mid; else lon[1] = mid;
          } else {
            const mid = (lat[0] + lat[1]) / 2;
            if (cd & mask) lat[0] = mid; else lat[1] = mid;
          }
          even = !even;
        }
      }
      return [lat[0], lon[0], lat[1], lon[1]];
    }

    document.getElementById("count").textContent = GEOHASHES.length;

    function escapeHtml(s) {
      return String(s)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
    }

    const map = L.map("map", { preferCanvas: true }).setView([22, 79], 5);
    /* OSM standard tiles. On load failure (e.g. 403 / referer policy for file://), Leaflet shows errorTileUrl instead of OSM's blocked graphic. */
    const TILE_ERROR_PLACEHOLDER =
      "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==";
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
      errorTileUrl: TILE_ERROR_PLACEHOLDER,
    }).addTo(map);

    const group = L.layerGroup().addTo(map);
    const bounds = [];
    const LABEL_MIN_ZOOM = 8;
    let forceShowLabels = false;

    function syncLabelPane() {
      const pane = map.getPane("tooltipPane");
      if (!pane) return;
      const show = forceShowLabels || map.getZoom() >= LABEL_MIN_ZOOM;
      pane.style.display = show ? "" : "none";
      pane.style.visibility = show ? "visible" : "hidden";
    }

    function addCell(hash) {
      let box;
      try {
        box = decodeBbox(hash);
      } catch (e) { return; }
      const [minLat, minLon, maxLat, maxLon] = box;
      const rect = L.rectangle([[minLat, minLon], [maxLat, maxLon]], {
        color: "#c41e3a",
        weight: 1,
        opacity: 0.85,
        fillColor: "#e85d75",
        fillOpacity: 0.18,
      });
      rect.bindPopup(
        "<code style='font-size:14px'>" + escapeHtml(hash) + "</code><br><small>Length: " + hash.length + " chars</small>"
      );
      rect.bindTooltip(escapeHtml(hash), {
        permanent: true,
        direction: "center",
        className: "geohash-oncell",
      });
      rect.addTo(group);
      bounds.push([minLat, minLon], [maxLat, maxLon]);
    }

    GEOHASHES.forEach(addCell);

    map.on("zoomend", syncLabelPane);
    map.on("zoom", syncLabelPane);

    let visible = true;
    document.getElementById("toggle").onclick = function () {
      visible = !visible;
      if (visible) map.addLayer(group); else map.removeLayer(group);
    };

    const labelsBtn = document.getElementById("labels");
    labelsBtn.onclick = function () {
      forceShowLabels = !forceShowLabels;
      labelsBtn.textContent = forceShowLabels ? "Zoom-based labels" : "Always show labels";
      labelsBtn.classList.toggle("secondary", !forceShowLabels);
      syncLabelPane();
    };

    function fitAll() {
      if (bounds.length === 0) return;
      map.fitBounds(bounds, { padding: [24, 24], maxZoom: 12 });
    }
    document.getElementById("fit").onclick = fitAll;
    fitAll();
    syncLabelPane();
  })();
  </script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
