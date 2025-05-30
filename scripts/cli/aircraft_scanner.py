import os
import sys
import json

# Ajoute le dossier courant au path Python (utile pour imports locaux)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Ici tu mets directement ton code :
def guess_engine_type(folder_name):
    folder_name = folder_name.lower()
    if "cfm" in folder_name:
        return "CFM"
    elif "iae" in folder_name:
        return "IAE"
    else:
        return "UNKNOWN"

def scan_fenix_aircraft():
    community_path = os.path.expandvars(
        "C:/Users/Bertrand/AppData/Local/Packages/Microsoft.Limitless_8wekyb3d8bbwe/LocalCache/Packages/Community"
    )
    liveries_folders = [
        "fnx-aircraft-319-liveries",
        "fnx-aircraft-320-liveries",
        "fnx-aircraft-321-liveries"
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

            registration = ""
            company = ""
            icao = ""
            model = ""
            engine_type = guess_engine_type(livery_folder)

            with open(aircraft_cfg, "r", encoding="utf-8", errors="ignore") as f:
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
                        if "A319" in value:
                            model = "A319"
                        elif "A320" in value:
                            model = "A320"
                        elif "A321" in value:
                            model = "A321"

            if registration and model:
                results.append({
                    "model": model,
                    "registration": registration,
                    "company": company if company else "UNKNOWN",
                    "icao": icao if icao else "UNKNOWN",
                    "engine_type": engine_type
                })

    results_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'results'))
    os.makedirs(results_dir, exist_ok=True)
    output_file = os.path.join(results_dir, "aircraft_scanresults.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)

    print("[Scanner] Fichier JSON généré avec succès : aircraft_scanresults.json")
    print()
    print("[INFO] Pensez à choisir manuellement l'Airframe dans SimBrief :")
    print("→ Fenix Simulations (MSFS) - A319/A320/A321 CFM selon le modèle")

if __name__ == "__main__":
    scan_fenix_aircraft()
