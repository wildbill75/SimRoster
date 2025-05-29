import os
import json
import csv
import re
import configparser


def get_executable_folder():
    import sys
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def load_airports_database(csv_path):
    airports_db = {}
    try:
        with open(csv_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                icao = row.get('ICAO', '').strip()
                name = row.get('Name', '').strip()
                if icao:
                    airports_db[icao.upper()] = name
    except Exception as e:
        print(f"Erreur lors du chargement du fichier CSV : {e}")
    return airports_db


def is_airport_folder(folder_name):
    return re.match(r"^[A-Z0-9]{4}$", folder_name.upper()) is not None or 'airport' in folder_name.lower()


def is_aircraft_folder(folder_name):
    return 'aircraft' in folder_name.lower() or 'livery' in folder_name.lower()


def scan_directory_for_airports(root_path, airports_db, log_lines):
    found = []
    if not os.path.exists(root_path):
        log_lines.append(f"❌ Dossier introuvable : {root_path}")
        return found
    for entry in os.listdir(root_path):
        entry_path = os.path.join(root_path, entry)
        if os.path.isdir(entry_path):
            if is_airport_folder(entry):
                icao = entry.upper()[:4]
                name = airports_db.get(icao, entry)
                found.append({'icao': icao, 'name': name})
                log_lines.append(f"✅ Aéroport détecté : {icao} - {name}")
    return found


def scan_directory_for_aircraft(root_path, log_lines):
    found = []
    if not os.path.exists(root_path):
        log_lines.append(f"❌ Dossier introuvable : {root_path}")
        return found
    for entry in os.listdir(root_path):
        entry_path = os.path.join(root_path, entry)
        if os.path.isdir(entry_path):
            if is_aircraft_folder(entry):
                found.append(entry)
                log_lines.append(f"🛩️ Avion détecté : {entry}")
    return found


def scan_msfs_content(
    community_folder=None,
    streamed_folder=None,
    official_folder_2020=None,
    official_folder_2024=None,
    airports_csv_path=None,
    log_lines=None
):
    if log_lines is None:
        log_lines = []

    log_lines.append("\n🔍 Début de l'analyse...")
    airports_db = load_airports_database(airports_csv_path) if airports_csv_path else {}

    community_airports = scan_directory_for_airports(community_folder, airports_db, log_lines)
    asobo_airports = scan_directory_for_airports(official_folder_2020, airports_db, log_lines)
    marketplace_airports = scan_directory_for_airports(official_folder_2024, airports_db, log_lines)
    aircraft = scan_directory_for_aircraft(community_folder, log_lines)

    result = {
        "community_airports": community_airports,
        "asobo_airports": asobo_airports,
        "marketplace_airports": marketplace_airports,
        "aircraft": aircraft,
    }

    json_path = os.path.join(get_executable_folder(), "scanresults.json")
    try:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        log_lines.append(f"\n✅ JSON exporté : {json_path}")
    except Exception as e:
        log_lines.append(f"❌ Erreur export JSON : {e}")

    return result
