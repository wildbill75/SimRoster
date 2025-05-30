import os
import json

def get_data_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data'))

def get_results_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'results'))

def load_json_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_flight_json(flight, results_dir):
    os.makedirs(results_dir, exist_ok=True)
    output_path = os.path.join(results_dir, "simbrief_flight.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(flight, f, indent=4, ensure_ascii=False)
    print(f"[SimBrief] Fichier {output_path} généré avec succès.")

def main():
    data_dir = get_data_dir()
    results_dir = get_results_dir()

    # Charger la liste des aéroports
    airport_path = os.path.join(results_dir, "airport_scanresults.json")
    airports = load_json_file(airport_path)
    print("--- Sélection du vol ---\nAéroports disponibles :")
    for i, ap in enumerate(airports):
        print(f"[{i}] {ap['icao']} | {ap['name']}")

    dep_idx = int(input("\n--- Sélection du vol (départ) ---\nChoisir l'index du vol (départ) : ").strip())
    arr_idx = int(input("\n--- Sélection du vol (arrivée) ---\nChoisir l'index du vol (arrivée) : ").strip())
    dep_airport = airports[dep_idx]
    arr_airport = airports[arr_idx]

    # Charger la liste des avions
    aircraft_path = os.path.join(results_dir, "aircraft_scanresults.json")
    aircraft_list = load_json_file(aircraft_path)
    print("\n--- Sélection du avion ---")
    for i, ac in enumerate(aircraft_list):
        print(f"[{i}] {ac['model']} | {ac['company']} | {ac['registration']}")
    ac_idx = int(input("Choisir l'index du avion : ").strip())
    aircraft = aircraft_list[ac_idx]

    # Générer la structure du vol SimBrief
    flight = {
        "departure_icao": dep_airport["icao"],
        "arrival_icao": arr_airport["icao"],
        "aircraft_model": aircraft["model"],
        "airline": aircraft["company"],
        "icao": aircraft["icao"],
        "registration": aircraft["registration"]
    }

    save_flight_json(flight, results_dir)

if __name__ == "__main__":
    main()
