import sys
import os

# Ajoute le dossier utils pour l'import du config_helper
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "utils"))
)
from config_helper import load_config

import json

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RESULTS_DIR = os.path.join(BASE_DIR, "results")


def guess_engine_type(folder_name):
    folder_name = folder_name.lower()
    if "cfm" in folder_name:
        return "CFM"
    elif "iae" in folder_name:
        return "IAE"
    else:
        return "UNKNOWN"


def parse_aircraft_cfg(cfg_path):
    registration = ""
    company = ""
    icao = ""
    model = ""
    with open(cfg_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    in_flight_sim = False
    for line in lines:
        if line.strip().lower().startswith("[fltsim.0]"):
            in_flight_sim = True
        elif in_flight_sim:
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip().lower()
            value = value.strip().strip('"')
            if key == "atc_id":
                registration = value
            elif key == "atc_airline":
                company = value
            elif key == "icao_airline":
                icao = value
            elif key == "title":
                if "A319" in value.upper():
                    model = "A319"
                elif "A320" in value.upper():
                    model = "A320"
                elif "A321" in value.upper():
                    model = "A321"
    return registration, company, icao, model


def scan_fenix_aircraft(community_path):
    liveries_folders = [
        "fnx-aircraft-319-liveries",
        "fnx-aircraft-320-liveries",
        "fnx-aircraft-321-liveries",
    ]
    results = []
    for folder in liveries_folders:
        full_livery_path = os.path.join(community_path, folder)
        simobjects_path = os.path.join(full_livery_path, "SimObjects", "Airplanes")
        if not os.path.isdir(simobjects_path):
            continue
        for livery_folder in os.listdir(simobjects_path):
            livery_path = os.path.join(simobjects_path, livery_folder)
            if not os.path.isdir(livery_path):
                continue
            aircraft_cfg = os.path.join(livery_path, "aircraft.cfg")
            if not os.path.isfile(aircraft_cfg):
                continue
            registration, company, icao, model = parse_aircraft_cfg(aircraft_cfg)
            engine_type = guess_engine_type(livery_folder)
            if registration and model:
                results.append(
                    {
                        "model": model,
                        "registration": registration,
                        "company": company if company else "UNKNOWN",
                        "icao": icao if icao else "UNKNOWN",
                        "engine_type": engine_type,
                    }
                )
    return results


def save_results(results, filename):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(os.path.join(RESULTS_DIR, filename), "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    config = load_config()
    community_path = config.get("community_dir", "")
    if not community_path or not os.path.isdir(community_path):
        print("[ERREUR] Chemin Community non défini ou invalide dans la config !")
        sys.exit(1)
    results = scan_fenix_aircraft(community_path)
    save_results(results, "aircraft_scanresults.json")
    print("[Scanner] Fichier JSON généré avec succès : aircraft_scanresults.json")
    print()
    print("[INFO] Pensez à choisir manuellement l'Airframe dans SimBrief :")
    print("→ Fenix Simulations (MSFS) - A319/A320/A321 CFM selon le modèle")
