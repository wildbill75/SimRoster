import sys
import os
import csv
import json

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "utils"))
)
from config_helper import load_config

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
    callsign = ""
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
            elif key == "atc_flight_number":
                callsign = value
    return registration, company, icao, model, callsign


def load_callsign_dict(csv_path):
    callsign_dict = {}
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Stocke par ICAO (toujours en majuscule)
            icao = row.get("ICAO", "").upper()
            if icao:
                callsign_dict[icao] = {
                    "callsign": row.get("Callsign", "").title(),
                    "company": row.get("Companyname", ""),
                    "iata": row.get("IATA", ""),
                }
    return callsign_dict


def normalize_registration(registration, company, icao_code):
    # Correction spéciale Aegean "SXDDNH" => "SX-DNH"
    if registration:
        reg = registration.upper().replace("-", "")
        if reg.startswith("SXD") and len(reg) == 6:
            return "SX-" + reg[3:]
        if reg.startswith("SX") and len(reg) == 5:
            return "SX-" + reg[2:]
    return registration


def get_callsign_for_company(company, icao, airline_callsign_map):
    company_clean = (company or "").strip().lower()
    icao_clean = (icao or "").strip().upper()
    for entry in airline_callsign_map:
        if entry["ICAO"].upper() == icao_clean:
            return entry["Callsign"]
    for entry in airline_callsign_map:
        if entry["Companyname"].lower() == company_clean:
            return entry["Callsign"]
    return None


def is_fenix_stock_livery(entry):
    """
    Renvoie True si cette entrée correspond à une livrée 'maison' Fenix à exclure.
    On identifie :
        - Company == "Fenix" ou "Unknown" ou "Default" ou "Asobo" ou "FBW"
        - Registration dans la liste des stocks connus
        - Le chemin contient fnx-aircraft-319-321 (ou variantes), sans -liveries
    """
    stock_registrations = {
        "G-FBIG",
        "G-FENX",
        "G-SMOL",
        "G-FENY",
        "G-FENZ",
        "G-FENW",
        "OE-LWF",
        # Ajoute d'autres si tu veux être exhaustif sur les registrations maison Phoenix
    }
    stock_companies = {"fenix", "asobo", "fbw", "unknown", "default"}
    registration = (entry.get("registration") or "").upper()
    company = (entry.get("company") or "").lower()
    path = (entry.get("path") or "").replace("\\", "/").lower()
    # Exclusion stricte sur le dossier
    if "fnx-aircraft-319-321" in path and "-liveries" not in path:
        return True
    # Exclusion stricte sur company
    if company in stock_companies:
        return True
    # Exclusion stricte sur registration
    if registration in stock_registrations:
        return True
    # Exclusion si modèle mais pas de compagnie, registration ou path douteux
    return False


def scan_all_aircraft(community_path):
    blacklist = [
        "fsltl",
        "aig-",
        "ivao-",
        "traffic",
        "ai-",
        "bgl",
        "statics",
        "simple aircraft",
        "justflight-traffic",
    ]
    strict_blacklist = [
        "fnx-aircraft-319",
        "fnx-aircraft-320",
        "fnx-aircraft-321",
    ]
    callsign_csv = os.path.join("data", "airline_callsign_full.csv")
    callsign_dict = load_callsign_dict(callsign_csv)

    results = []
    for item in os.listdir(community_path):
        lower_item = item.lower()
        if lower_item in strict_blacklist or any(kw in lower_item for kw in blacklist):
            print(f"[EXCLU] {item} (blacklist)")
            continue
        addon_path = os.path.join(community_path, item)
        if not os.path.isdir(addon_path):
            continue
        simobj_base = os.path.join(addon_path, "SimObjects", "Airplanes")
        if not os.path.isdir(simobj_base):
            continue
        for livery_folder in os.listdir(simobj_base):
            livery_path = os.path.join(simobj_base, livery_folder)
            if not os.path.isdir(livery_path):
                continue
            aircraft_cfg = os.path.join(livery_path, "aircraft.cfg")
            if not os.path.isfile(aircraft_cfg):
                continue
            registration, company, icao, model, callsign = parse_aircraft_cfg(
                aircraft_cfg
            )
            engine_type = guess_engine_type(livery_folder)
            entry = {
                "model": model,
                "registration": registration,
                "company": company if company else "UNKNOWN",
                "icao": icao if icao else "UNKNOWN",
                "engine_type": engine_type,
                "path": livery_path,
            }
            # Ajoute callsign et remplit les infos compagnie depuis le CSV si possible
            if icao and icao.upper() in callsign_dict:
                cdata = callsign_dict[icao.upper()]
                entry["company"] = cdata["company"]
                entry["icao"] = icao.upper()
                entry["iata"] = cdata["iata"]
                entry["callsign"] = cdata["callsign"]
            elif callsign:
                entry["callsign"] = callsign
            results.append(entry)
    # -- Patch registration/callsign via CSV --
    airline_callsign_path = "data/airline_callsign_full.csv"
    airline_callsign_map = []
    with open(airline_callsign_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        airline_callsign_map = sorted(
            [row for row in reader], key=lambda x: x["Companyname"]
        )
    for entry in results:
        reg = entry.get("registration")
        company = entry.get("company")
        icao = entry.get("icao")
        # Patch registration (ex: SX-DNH pour Aegean, etc.)
        entry["registration"] = normalize_registration(reg, company, icao)
        # Patch callsign (CSV prioritaire)
        callsign_csv = get_callsign_for_company(company, icao, airline_callsign_map)
        if callsign_csv:
            entry["callsign"] = callsign_csv

    # -- Exclusion des livrées Fenix de base --
    results_clean = []
    for entry in results:
        if is_fenix_stock_livery(entry):
            print(f"[EXCLU][STOCK] {entry.get('registration')} / {entry.get('path')}")
            continue
        results_clean.append(entry)
    return results_clean


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
    results = scan_all_aircraft(community_path)
    save_results(results, "aircraft_scanresults.json")
    print("[Scanner] Fichier JSON généré avec succès : aircraft_scanresults.json")
    print()
    print("[INFO] Avions scannés dans tous les dossiers Community (A319/A320/A321)")
