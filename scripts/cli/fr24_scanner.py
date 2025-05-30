import os
import json

def get_data_dir():
    # Chemin absolu du dossier data à la racine du projet
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data'))

def get_results_dir():
    # Chemin absolu du dossier results à la racine du projet
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'results'))

def load_flights(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_selected_flight(flight, results_dir):
    os.makedirs(results_dir, exist_ok=True)
    output_path = os.path.join(results_dir, "selected_fr24_flight.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(flight, f, indent=4, ensure_ascii=False)
    print(f"[FR24Scanner] Fichier {output_path} généré avec succès.")

def main():
    data_dir = get_data_dir()
    results_dir = get_results_dir()
    mock_path = os.path.join(data_dir, "mock_fr24_flights.json")
    flights = load_flights(mock_path)

    print("--- Vols simulés disponibles ---")
    for i, flight in enumerate(flights):
        print(f"[{i}] {flight['flight_number']} | {flight['airline']} | {flight['departure_icao']}({flight.get('departure_gate', '-')}) -> {flight['arrival_icao']}({flight.get('arrival_gate', '-')}) | Dép. {flight['scheduled_departure']}")

    idx = int(input("Choisir l'index du vol : ").strip())
    chosen = flights[idx]

    print("\n--- Vol sélectionné ---")
    print(json.dumps(chosen, indent=4, ensure_ascii=False))

    save_selected_flight(chosen, results_dir)

if __name__ == "__main__":
    main()
