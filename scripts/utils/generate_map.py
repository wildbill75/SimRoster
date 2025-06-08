import os
import csv
import json

# BASE_DIR = racine du projet
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
AIRPORTS_CSV_PATH = os.path.join(BASE_DIR, "data", "airports.csv")
RESULTS_DIR = os.path.join(BASE_DIR, "results")
MAP_JSON_PATH = os.path.join(RESULTS_DIR, "map_data.json")
MAP_HTML_PATH = os.path.join(RESULTS_DIR, "map.html")

def generate_airports_map_data():
    """
    Génère map_data.json uniquement à partir des aéroports scannés (results/airport_scanresults.json).
    """
    import os
    import json

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    RESULTS_DIR = os.path.join(BASE_DIR, "..", "results")
    AIRPORTS_SCAN_JSON = os.path.join(RESULTS_DIR, "airport_scanresults.json")
    MAP_JSON_PATH = os.path.join(BASE_DIR, "map_data.json")

    # On charge la liste scannée au lieu du CSV complet
    if not os.path.exists(AIRPORTS_SCAN_JSON):
        print("[ERROR] airport_scanresults.json introuvable : pas de markers générés.")
        with open(MAP_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump([], f)
        return

    with open(AIRPORTS_SCAN_JSON, encoding="utf-8") as f:
        airports = json.load(f)

    with open(MAP_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(airports, f, ensure_ascii=False, indent=2)

    print(f"[INFO] Carte JSON créée (aéroports scannés uniquement) : {MAP_JSON_PATH}")

def generate_airports_map_html():
    # Style sombre CartoDB Dark
    leaflet_tiles = "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
    leaflet_attr = "© OpenStreetMap, © CartoDB"
    center_lat, center_lon = 48.8566, 2.3522  # Paris par défaut

    # Récupérer les aéroports
    with open(MAP_JSON_PATH, "r", encoding="utf-8") as f:
        airports = json.load(f)

    # Centrer la carte sur la moyenne si dispo
    if airports:
        try:
            center_lat = sum(a["latitude"] for a in airports) / len(airports)
            center_lon = sum(a["longitude"] for a in airports) / len(airports)
        except Exception:
            pass

    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Airports Map</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css" />
  <style>
    html, body, #map {{
      height: 100%;
      margin: 0;
      background: #181821;
    }}
    #map {{
      width: 100vw;
      height: 100vh;
      background: #181821;
    }}
    .leaflet-control-attribution {{
      background: rgba(30,30,30,0.7);
      color: #fff;
    }}
  </style>
</head>
<body>
<div id="map"></div>
<script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
<script>
  var map = L.map('map', {{
    center: [{center_lat}, {center_lon}],
    zoom: 5,
    zoomControl: true,
    scrollWheelZoom: true
  }});
  L.tileLayer('{leaflet_tiles}', {{
    attribution: '{leaflet_attr}',
    maxZoom: 15,
    minZoom: 2
  }}).addTo(map);

  var airports = {json.dumps(airports)};
  airports.forEach(function(ap) {{
    if (!ap.latitude || !ap.longitude) return;
    var marker = L.circleMarker([ap.latitude, ap.longitude], {{
      radius: 4,
      color: "#86888c",
      fillColor: "rgba(0,0,0,0)",
      fillOpacity: 0,
      weight: 1
    }}).addTo(map);
    var popup = "<b>" + ap.icao + "</b><br/>" + ap.name;
    if (ap.city) popup += "<br/>" + ap.city;
    if (ap.country) popup += "<br/>" + ap.country;
    marker.bindPopup(popup);
  }});
</script>
</body>
</html>
"""
    with open(MAP_HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[INFO] Fichier HTML carte généré : {MAP_HTML_PATH}")


# === LANCEUR PRINCIPAL ===
if __name__ == "__main__":
    generate_airports_map_data()
    generate_airports_map_html()
