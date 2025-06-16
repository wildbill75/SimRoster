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
# === Chargement mapping custom aéroports ===
CUSTOM_AIRPORT_MAP_PATH = os.path.abspath(
    os.path.join(BASE_DIR, "data", "custom_airport_mapping.json")
)
try:
    with open(CUSTOM_AIRPORT_MAP_PATH, "r", encoding="utf-8") as f:
        CUSTOM_AIRPORT_MAPPING = json.load(f)
except Exception:
    CUSTOM_AIRPORT_MAPPING = []
    print(f"[WARN] Fichier de mapping custom non trouvé : {CUSTOM_AIRPORT_MAP_PATH}")


def extract_icao_from_folder_or_name(folder_name):
    """
    Extrait le premier code ICAO (4 lettres/nombres) juste après 'airport-' dans un nom de dossier ou manifest.
    Exemple: 'fs24-microsoft-airport-cycg-castlegar,LEGA|EGAR|CYCG' -> 'CYCG'
    """
    import re

    match = re.search(r"airport-([a-z0-9]{4})", folder_name, re.IGNORECASE)
    if match:
        return match.group(1).upper()
    return None

def extract_airport_info(manifest_path, icao_official):
    """
    Tente d’extraire l’ICAO et le nom à partir d’un manifest.json et applique le mapping custom si besoin.
    Retourne (icao, name)
    """
    import json
    import os

    found_icao = None
    name = None

    if not os.path.exists(manifest_path):
        print(f"[DEBUG] Manifest absent : {manifest_path}")
        return None, None

    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"[DEBUG] Erreur lecture manifest {manifest_path}: {e}")
        return None, None

    # 1. Recherche ICAO dans les champs classiques (standard)
    # (ne pas toucher cette section si elle marche déjà)

    # 2. Fallback: mapping custom (whitelist)
    if not found_icao:
        print(f"[DEBUG] Tentative mapping custom pour manifest: {manifest_path}")
        print(f"[DEBUG] Data manifest: {data}")
        if "creator" in data and "title" in data:
            print(
                f"[DEBUG] mapping custom: call avec creator={data['creator']} / title={data['title']}"
            )
            custom_icao = match_custom_mapping(data, CUSTOM_AIRPORT_MAPPING)
            if custom_icao:
                print(f"[DEBUG] [CUSTOM MATCH] ICAO forcé par mapping: {custom_icao}")
                found_icao = custom_icao
                name = data.get("title", "")
            else:
                print(
                    f"[DEBUG] Aucun match mapping custom pour creator={data['creator']} / title={data['title']}"
                )
        else:
            print(
                "[DEBUG] Champ 'creator' ou 'title' manquant dans le manifest, mapping custom ignoré."
            )

    # 3. Fallback: Pattern ICAO dans le nom de fichier (ex: "airport-XXXX")
    if not found_icao:
        import re

        # pattern: airport-XXXX ou fs24-microsoft-airport-XXXX-...
        base_name = os.path.basename(os.path.dirname(manifest_path))
        matches = re.findall(
            r"(?:airport\-|^)([A-Z0-9]{4})(?:\-|$)", base_name, re.IGNORECASE
        )
        for candidate in matches:
            if candidate.upper() in icao_official:
                found_icao = candidate.upper()
                print(
                    f"[DEBUG] ICAO extrait via pattern 'airport-XXXX' ou nom dossier : {found_icao}"
                )
                name = data.get("title", "") or base_name
                break

    # 4. Fallback: Nom du dossier = ICAO
    if not found_icao:
        base_name = os.path.basename(os.path.dirname(manifest_path))
        if len(base_name) == 4 and base_name.upper() in icao_official:
            found_icao = base_name.upper()
            print(f"[DEBUG] ICAO trouvé via nom de dossier simple : {found_icao}")
            name = data.get("title", "") or base_name

    if found_icao:
        print(f"[DEBUG] ICAO FINAL retenu : {found_icao} pour {manifest_path}")

    return found_icao, name

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

def match_custom_mapping(data, mapping_list):
    creator = str(data.get("creator", "")).strip().lower()
    title = str(data.get("title", "")).strip().lower()
    print(f"[CUSTOM MATCH] manifest: creator='{creator}', title='{title}'")
    for entry in mapping_list:
        map_creator = entry.get("creator", "").strip().lower()
        map_title = entry.get("title", "").strip().lower()
        map_icao = entry.get("icao", "").strip().upper()
        print(
            f"[CUSTOM MATCH TEST] Est-ce que '{map_creator}' in '{creator}' AND '{map_title}' in '{title}' ?"
        )
        if map_creator in creator and map_title in title:
            print(
                f"[CUSTOM MATCH] -> Match trouvé pour ICAO {map_icao} ({map_creator}/{map_title})"
            )
            return map_icao
    return None

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
            # PATCH anti-multicode
            if not found_icao:
                for field in possible_fields:
                    codes = [c.strip() for c in str(field).upper().split("|")]
                    if len(codes) > 1:
                        print(f"[DEBUG] Multicode détecté dans {manifest_path}: {codes}")
                    # Priorité 1 : ICAO présent dans la base officielle
                    valid_icaos = [c for c in codes if c in icao_official]
                    if valid_icaos:
                        found_icao = valid_icaos[0]
                        break
                    # Priorité 2 : code à 4 lettres (si base officielle non passée)
                    codes4 = [c for c in codes if len(c) == 4 and c.isalnum()]
                    if codes4:
                        found_icao = codes4[0]
                        break
            if found_icao and name:
                return found_icao, name
            if found_icao:
                return found_icao, found_icao
            if not found_icao and "creator" in data and "title" in data:
                custom_icao = match_custom_mapping(data, CUSTOM_AIRPORT_MAPPING)
                if custom_icao:
                    found_icao = custom_icao
            if found_icao and name:
                return found_icao, name
            if found_icao:
                return found_icao, found_icao

    except Exception:
        pass
    return None, None

def find_icao_in_bgl(folder, icao_official, max_depth=3):
    import os
    import re

    # RegEx pour détecter toute séquence de 4 lettres/numéros majuscules
    icao_pattern = re.compile(rb"([A-Z0-9]{4})")

    def scan_dir(current_folder, depth):
        if depth < 0:
            return None
        for root, dirs, files in os.walk(current_folder):
            for file in files:
                if file.lower().endswith(".bgl"):
                    bgl_path = os.path.join(root, file)
                    try:
                        with open(bgl_path, "rb") as f:
                            data = f.read()
                            for match in icao_pattern.finditer(data):
                                possible_icao = match.group(1).decode(
                                    "ascii", errors="ignore"
                                )
                                if possible_icao in icao_official:
                                    print(
                                        f"[BGL SCAN] ICAO détecté dans {bgl_path}: {possible_icao}"
                                    )
                                    return possible_icao
                    except Exception as e:
                        print(f"[BGL SCAN] Erreur lecture {bgl_path}: {e}")
            # Ne pas descendre plus profond que max_depth
            if depth > 0:
                for subdir in dirs:
                    subdir_path = os.path.join(root, subdir)
                    found = scan_dir(subdir_path, depth - 1)
                    if found:
                        return found
        return None

    return scan_dir(folder, max_depth)

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
    import json

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

                # PATCH : PRIORITÉ ContentInfo/ContentHistory pour Community et AddonLinker
                contentinfo_icao = None
                contentinfo_path = os.path.join(item_path, "ContentInfo")
                if os.path.isdir(contentinfo_path):
                    for root, dirs, files in os.walk(contentinfo_path):
                        for file in files:
                            if file.lower() in [
                                "contenthistory.json",
                                "content-info.json",
                            ]:
                                contentinfo_file = os.path.join(root, file)
                                try:
                                    with open(contentinfo_file, encoding="utf-8") as f:
                                        data = json.load(f)
                                        # 1. MSFS2024 PAYWARE/Community: "items" list d’objets (type "airport")
                                        if "items" in data and isinstance(
                                            data["items"], list
                                        ):
                                            for entry in data["items"]:
                                                if (
                                                    entry.get("type", "").lower()
                                                    == "airport"
                                                    and "content" in entry
                                                ):
                                                    ci_icao = (
                                                        entry["content"].strip().upper()
                                                    )
                                                    if (
                                                        ci_icao
                                                        and ci_icao in icao_official
                                                    ):
                                                        contentinfo_icao = ci_icao
                                                        break
                                        # 2. Certains ContentInfo.json => champ direct "content"
                                        elif "content" in data:
                                            ci_icao = (
                                                str(data["content"]).strip().upper()
                                            )
                                            if ci_icao and ci_icao in icao_official:
                                                contentinfo_icao = ci_icao
                                except Exception as e:
                                    print(
                                        f"[DEBUG] Erreur lecture ContentInfo: {contentinfo_file}: {e}"
                                    )
                        if contentinfo_icao:
                            break
                if contentinfo_icao:
                    found_icao = contentinfo_icao
                    display_name = item

                # Sinon, recherche ICAO dans manifest (fallback)
                if not found_icao:
                    for manifest_path in manifest_paths:
                        icao, name = extract_airport_info(manifest_path, icao_official)
                        if icao and icao.upper() in icao_official:
                            found_icao = icao.upper()
                            display_name = name
                            break

                # Fallback : pattern "airport-xxxx"
                if not found_icao:
                    found_icao = extract_icao_from_folder_or_name(item)
                    if found_icao and found_icao.upper() in icao_official:
                        print(
                            f"[SCAN] ICAO extrait via pattern airport- : {found_icao}"
                        )
                        display_name = item

                # Fallback ContentHistory/Info JSON récursif (pour Official/Streamed)
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

                # Final check et ajout à la liste si tout est bon
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
                    print(
                        f"\n[DEBUG] AUCUN ICAO trouvé pour le dossier : {item} (manifest(s) = {manifest_paths})\n"
                    )
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
