import json
import urllib.parse
import webbrowser
import os

def load_flight_data(json_path="simbrief_flight.json"):
    if not os.path.exists(json_path):
        print("[Erreur] Le fichier simbrief_flight.json est introuvable.")
        return None
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)

def build_simbrief_url(flight_data, pilot_id=25756):
    base_url = "https://www.simbrief.com/system/dispatch.php?"
    params = {
        "userid": pilot_id,
        "type": "xml",
        "airline": flight_data["icao"],
        "fltnum": "1234",  # valeur temporaire ou à personnaliser plus tard
        "origin": flight_data["departure_icao"],
        "destination": flight_data["arrival_icao"],
        "reg": flight_data["registration"],
        "aircraft_type": flight_data["aircraft_model"],
        "units": "KGS",  # ou "LBS"
        "navlog": "1",
        "planstep": "10"
    }
    return base_url + urllib.parse.urlencode(params)

def main():
    print("[SimBrief URL Builder] Lecture du fichier simbrief_flight.json...")
    data = load_flight_data()
    if data is None:
        return

    url = build_simbrief_url(data)
    print("[SimBrief URL Builder] URL générée :")
    print(url)

    print("[SimBrief URL Builder] Ouverture dans le navigateur...")
    webbrowser.open(url)

if __name__ == "__main__":
    main()
