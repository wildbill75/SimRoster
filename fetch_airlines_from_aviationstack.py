import requests
import csv

API_KEY = "***REMOVED***"
API_URL = "http://api.aviationstack.com/v1/airlines"

def fetch_airlines():
    airlines_data = []
    offset = 0
    limit = 100

    while True:
        print(f"[INFO] Fetching {offset} to {offset + limit}...")
        response = requests.get(API_URL, params={
            "access_key": API_KEY,
            "limit": limit,
            "offset": offset
        })

        if response.status_code != 200:
            print(f"[ERROR] Code {response.status_code}: {response.text}")
            break

        data = response.json().get("data", [])
        if not data:
            break

        for airline in data:
            callsign = (airline.get("callsign") or "").strip().upper()
            name = (airline.get("airline_name") or "").strip()
            icao = (airline.get("icao_code") or "").strip().upper()
            iata = (airline.get("iata_code") or "").strip().upper()

            if callsign and name:
                airlines_data.append({
                    "callsign": callsign,
                    "name": name,
                    "icao": icao,
                    "iata": iata
                })

        offset += limit

    # Export to CSV
    csv_path = "airline_callsigns_full.csv"
    with open(csv_path, mode="w", newline='', encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["callsign", "name", "icao", "iata"])
        writer.writeheader()
        for row in airlines_data:
            writer.writerow(row)

    print(f"[OK] {len(airlines_data)} compagnies enregistrées dans {csv_path}")

if __name__ == "__main__":
    fetch_airlines()
