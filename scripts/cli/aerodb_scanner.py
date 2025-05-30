import os
import sys
import requests
import time
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

# Ajout du dossier courant (scripts/) au path Python pour les imports locaux
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils import read_json_file, write_json_file

# Chargement de la config .env (API keys etc)
load_dotenv()

API_KEY = os.getenv("AERODATABOX_API_KEY")
if not API_KEY:
    print("❌ Clé API manquante. Assure-toi que le fichier .env contient bien AERODATABOX_API_KEY.")
    exit()

HEADERS = {
    "X-RapidAPI-Key": API_KEY,
    "X-RapidAPI-Host": "aerodatabox.p.rapidapi.com"
}

def get_scheduled_departures(icao, start_time, end_time):
    url = f"https://aerodatabox.p.rapidapi.com/airports/icao/{icao}/scheduled-departures/{start_time}/{end_time}"
    params = {
        "withLeg": "false",
        "withCancelled": "false",
        "withCodeshared": "false",
        "withCargo": "false"
    }
    response = requests.get(url, headers=HEADERS, params=params)
    response.raise_for_status()
    return response.json()

def scan_future_departures(icao="EGLL", days=1):
    print(f"\n🔍 Recherche des vols à venir au départ de {icao} pour les {days} prochains jours...\n")

    now = datetime(2024, 5, 28, tzinfo=timezone.utc)
    for d in range(days):
        date = now + timedelta(days=d)
        date_str = date.strftime("%Y-%m-%d")
        print(f"\n📅 {date_str} :")
        for hour in range(0, 24, 6):
            start = date.replace(hour=hour, minute=0, second=0)
            end = start + timedelta(hours=6)
            start_str = start.strftime("%Y-%m-%dT%H:%M")
            end_str = end.strftime("%Y-%m-%dT%H:%M")
            try:
                data = get_scheduled_departures(icao, start_str, end_str)
                flights = data.get("departures", [])
                if not flights:
                    print(f"  ❌ Aucun vol prévu entre {start_str} et {end_str}")
                else:
                    for flight in flights:
                        time_str = flight['departure']['scheduledTimeLocal']
                        to = flight['arrival'].get('airport', {}).get('name', '???')
                        number = flight.get('number', '???')
                        print(f"  🛫 {time_str} - Vol {number} vers {to}")
            except requests.exceptions.RequestException as e:
                print(f"⚠️ Erreur pour la plage {start_str} → {end_str} : {e}")
            time.sleep(7)  # Pause pour éviter les limites API

# Point d'entrée
if __name__ == "__main__":
    scan_future_departures(icao="LFPG", days=1)
