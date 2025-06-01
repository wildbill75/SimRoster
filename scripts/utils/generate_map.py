import os
import json
import csv

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RESULTS_DIR = os.path.join(BASE_DIR, "results")
DATA_DIR = os.path.join(BASE_DIR, "data")
MAP_DIR = os.path.join(BASE_DIR, "map")
MAP_JSON_PATH = os.path.join(MAP_DIR, "map_data.json")
MAP_HTML_PATH = os.path.join(MAP_DIR, "map.html")

def generate_airports_map_data():
    selected_path = os.path.join(RESULTS_DIR, "selected_airports.json")
    csv_path = os.path.join(DATA_DIR, "airports.csv")

    if not os.path.exists(selected_path) or not os.path.exists(csv_path):
        print("[ERREUR] Fichier sélectionné ou CSV introuvable.")
        return

    with open(selected_path, "r", encoding="utf-8") as f:
        selected = json.load(f)
        selected_icaos = set(a["icao"].upper() for a in selected)

    matched = []
    with open(csv_path, newline='', encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            icao = row.get("ident") or row.get("icao")
            if icao and icao.upper() in selected_icaos:
                matched.append({
                    "icao": icao.upper(),
                    "name": row.get("name", "Unknown"),
                    "lat": float(row.get("latitude_deg", 0)),
                    "lon": float(row.get("longitude_deg", 0))
                })

    with open(MAP_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(matched, f, indent=4, ensure_ascii=False)

    print(f"[INFO] Carte JSON créée : {MAP_JSON_PATH}")

def generate_airports_map_html():
    if not os.path.exists(MAP_JSON_PATH):
        print("[ERREUR] map_data.json introuvable.")
        return

    with open(MAP_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Carte des aéroports</title>
        <meta charset="utf-8" />
        <style>
            #map { height: 100vh; width: 100%; }
        </style>
        <link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
    </head>
    <body>
        <div id="map"></div>
        <script>
            var map = L.map('map').setView([47.0, 2.0], 6);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors'
            }).addTo(map);

            var airports = """ + json.dumps(data) + """;

            airports.forEach(function(a) {
                L.marker([a.lat, a.lon]).addTo(map)
                    .bindPopup("<b>" + a.icao + "</b><br>" + a.name);
            });
        </script>
    </body>
    </html>
    """

    with open(MAP_HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"[INFO] Fichier HTML carte généré : {MAP_HTML_PATH}")
