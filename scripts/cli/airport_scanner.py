import sys
import os
import json
import re
import csv

# Gestion intelligente des imports pour tous contextes d'exécution
try:
    from scripts.utils.config_helper import load_config
except ImportError:
    sys.path.insert(
        0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "utils"))
    )
    try:
        from config_helper import load_config
    except ImportError:
        from ..utils.config_helper import load_config

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RESULTS_DIR = os.path.join(BASE_DIR, "results")
CSV_PATH = os.path.abspath(os.path.join(BASE_DIR, "data", "airports.csv"))

def load_icao_dict_from_csv(csv_path):
    icao_dict = {}
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=",", quotechar='"')
        for row in reader:
            icao = row["icao"].strip().upper()
            name = row["name"].strip()
            city = row["city"].strip()
            country = row["country"].strip()
            lat = row["latitude"].strip()
            lon = row["longitude"].strip()
            # Sécurise la conversion float
            try:
                lat = float(lat)
            except Exception:
                lat = None
            try:
                lon = float(lon)
            except Exception:
                lon = None
            icao_dict[icao] = {
                "name": name,
                "city": city,
                "country": country,
                "latitude": lat,
                "longitude": lon,
            }
    return icao_dict

def extract_airport_info(manifest_path, icao_official=None):
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            name = data.get("name") or data.get("title") or ""
            name = name.replace("_", " ").replace("-", " ").strip()
            name = re.sub(r"\s+", " ", name)
            possible_fields = [
                data.get("title", ""),
                data.get("name", ""),
                data.get("package_version", ""),
                data.get("package_path", ""),
                os.path.basename(manifest_path),
            ]
            found_icao = None
            if icao_official:
                for field in possible_fields:
                    upper_field = str(field).upper()
                    for known_icao in icao_official:
                        if known_icao in upper_field:
                            found_icao = known_icao
                            break
                    if found_icao:
                        break
            if not found_icao:
                for field in possible_fields:
                    match = re.search(r"([A-Z0-9]{4})", str(field).upper())
                    if match:
                        found_icao = match.group(1)
                        break
            if found_icao and name:
                return found_icao, name
            if found_icao:
                return found_icao, found_icao
    except Exception:
        pass
    return None, None

def find_icao_in_content_info(directory, icao_official, max_depth=3):
    candidates = ["ContentHistory.json", "content_info.json", "contenthistory.json"]
    for root, dirs, files in os.walk(directory):
        depth = root[len(directory) :].count(os.sep)
        if depth > max_depth:
            dirs[:] = []
            continue
        for fname in candidates:
            if fname in files:
                try:
                    test_path = os.path.join(root, fname)
                    with open(test_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if "items" in data:
                            for entry in data["items"]:
                                if (
                                    entry.get("type", "").lower() == "airport"
                                    and "content" in entry
                                ):
                                    candidate_icao = entry["content"].strip().upper()
                                    if (
                                        icao_official
                                        and candidate_icao in icao_official
                                    ):
                                        return candidate_icao
                        elif "content" in data:
                            candidate_icao = str(data["content"]).strip().upper()
                            if icao_official and candidate_icao in icao_official:
                                return candidate_icao
                except Exception as e:
                    print(f"[DEBUG] Erreur lecture {fname}: {e}")
    return None

def find_icao_in_bgl(directory, icao_official, max_depth=3):
    """
    Recherche récursive d'un ICAO connu dans le nom des fichiers BGL.
    Prend toujours le plus long match pour éviter "IBI" dans "LEIB".
    """
    icao_list = sorted(list(icao_official), key=len, reverse=True)  # plus longs d'abord
    for root, dirs, files in os.walk(directory):
        depth = root[len(directory) :].count(os.sep)
        if depth > max_depth:
            dirs[:] = []
            continue
        for file in files:
            if file.lower().endswith(".bgl"):
                upper_file = file.upper()
                for known_icao in icao_list:
                    if upper_file.startswith(known_icao):
                        return known_icao
    return None

def scan_airports(directories, csv_path):
    import os
    import re

    icao_dict = load_icao_dict_from_csv(csv_path)
    # On force les ICAO CSV en majuscule pour la recherche
    icao_official = set(k.upper() for k in icao_dict.keys())
    found_airports = []
    ignored = []

    keywords_to_ignore = [
        "landingchallenge",
        "bushtrip",
        "training",
        "wasm",
        "module",
        "simobjects",
        "lib",
        "library",
        "liveries",
        "material",
        "asset",
        "model",
        "texture",
        "scenery",
        "mesh",
        "heliport",
        "helipad",
        "animals",
        "vfx",
        "aircraft",
        "passiveaircraft",
        "travelbook",
        "base-coverage",
        "character",
        "procedural",
        "materiallib",
        "vehicle",
        "passenger",
        "rally",
        "lepack",
        "eventtriggers",
        "simple scenery",
        "fsuipc",
        "gsx",
        "coverage-map",
        "lowalt",
        "precisionlanding",
        "palettelib",
        "simattachmentlib",
        "livingworld",
        "winwing",
        "tools-only",
        "asobo-challenges",
        "discovery",
        "ships",
        "fsltl",
        "ground",
        "city",
    ]
    icao_regex = re.compile(r"^[A-Z0-9]{4}$")
    report_ignored = []  # Pour générer le rapport

    for base_dir in directories:
        print(f"[DEBUG] SCAN DIR: {base_dir}")
        if not os.path.exists(base_dir):
            print(f"[Scanner] Dossier introuvable : {base_dir}")
            continue
        for item in os.listdir(base_dir):
            lower_item = item.lower()
            if any(kw in lower_item for kw in keywords_to_ignore):
                continue
            item_path = os.path.join(base_dir, item)
            if os.path.isdir(item_path):
                manifest_paths = []
                main_manifest = os.path.join(item_path, "manifest.json")
                if os.path.exists(main_manifest):
                    manifest_paths.append(main_manifest)
                for subitem in os.listdir(item_path):
                    subitem_path = os.path.join(item_path, subitem)
                    if os.path.isdir(subitem_path):
                        sub_manifest = os.path.join(subitem_path, "manifest.json")
                        if os.path.exists(sub_manifest):
                            manifest_paths.append(sub_manifest)
                found_icao, display_name = None, None
                # Recherche ICAO dans manifest
                for manifest_path in manifest_paths:
                    icao, name = extract_airport_info(manifest_path, icao_official)
                    if icao and icao.upper() in icao_official:
                        found_icao = icao.upper()
                        display_name = name
                        break
                # Fallback ICAO dans le nom du dossier si rien trouvé
                if not found_icao:
                    upper_item = item.upper()
                    for known_icao in icao_official:
                        if known_icao in upper_item:
                            found_icao = known_icao
                            display_name = item
                            break
                # Fallback ContentHistory/Info JSON récursif
                if not found_icao:
                    ch_icao = find_icao_in_content_info(
                        item_path, icao_official, max_depth=3
                    )
                    if ch_icao:
                        found_icao = ch_icao.upper()
                        display_name = item
                # Fallback BGL récursif
                if not found_icao:
                    bgl_icao = find_icao_in_bgl(item_path, icao_official, max_depth=3)
                    if bgl_icao:
                        found_icao = bgl_icao.upper()
                        display_name = item
                # Final check
                if (
                    found_icao
                    and found_icao.upper() in icao_official
                    and icao_regex.match(found_icao.upper())
                ):
                    # Récupère le nom réel (sans ICAO doublonné) depuis le CSV si possible
                    name_csv = icao_dict.get(found_icao.upper(), {}).get("name")
                    if name_csv:
                        cleaned_name = name_csv
                        if cleaned_name.upper().startswith(found_icao.upper()):
                            cleaned_name = cleaned_name[len(found_icao) :].lstrip(" -–")
                        cleaned_name = cleaned_name.strip()
                        label = cleaned_name if cleaned_name else name_csv
                    else:
                        cleaned_name = display_name
                        if cleaned_name and cleaned_name.strip().upper().startswith(
                            found_icao.upper()
                        ):
                            cleaned_name = cleaned_name[len(found_icao) :].lstrip(" -–")
                        label = cleaned_name.strip() if cleaned_name else found_icao

                    # Ajoute les coordonnées depuis le CSV si disponibles
                    lat = icao_dict.get(found_icao.upper(), {}).get("latitude")
                    lon = icao_dict.get(found_icao.upper(), {}).get("longitude")
                    entry = {
                        "icao": found_icao.upper(),
                        "name": label,
                        "path": item_path,
                    }
                    if lat is not None and lon is not None:
                        entry["latitude"] = lat
                        entry["longitude"] = lon
                    found_airports.append(entry)
                else:
                    ignored.append(f"{found_icao if found_icao else item} ({item})")

    # PATCH ICAO UNIQUE – Garde un seul aéroport par ICAO
    unique_icao = {}
    for ap in found_airports:
        icao_upper = ap["icao"].upper()
        if icao_upper not in unique_icao:
            unique_icao[icao_upper] = ap
    found_airports = sorted(list(unique_icao.values()), key=lambda x: x["icao"])

    for entry in ignored:
        print(f"[Scanner] [IGNORÉ] icao non listé en base officielle : {entry}")

    # -------- NOUVEAU : Rapport CSV des ignorés avec ICAO partiel dans le nom du dossier --------
    for base_dir in directories:
        if not os.path.exists(base_dir):
            continue
        for item in os.listdir(base_dir):
            upper_item = item.upper()
            matched_icaos = [icao for icao in icao_official if icao in upper_item]
            if matched_icaos:
                report_ignored.append({"folder": item, "icaos_in_name": matched_icaos})

    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(
        os.path.join(RESULTS_DIR, "scan_report_ignored.csv"), "w", encoding="utf-8"
    ) as f:
        f.write("folder,icaos_in_name\n")
        for entry in report_ignored:
            f.write(f"{entry['folder']},{'|'.join(entry['icaos_in_name'])}\n")

    print(
        f"[Scanner] Scanné {len(found_airports)} aéroports valides. Résultats dans {os.path.abspath(os.path.join(RESULTS_DIR, 'airport_scanresults.json'))}"
    )
    print(
        f"[Scanner] Rapport ignorés généré : {os.path.abspath(os.path.join(RESULTS_DIR, 'scan_report_ignored.csv'))}"
    )
    return found_airports

def save_results(results, filename):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(os.path.join(RESULTS_DIR, filename), "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    config = load_config()
    paths_to_scan = [
        config.get("community_dir", ""),
        config.get("official_onestore_dir", ""),
        config.get("streamedpackages_dir", ""),
    ]
    paths_to_scan = [p for p in paths_to_scan if p]
    airports = scan_airports(paths_to_scan, CSV_PATH)
    save_results(airports, "airport_scanresults.json")
