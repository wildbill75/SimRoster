import os
import re
import json

# === CHEMINS ABSOLUS — MODIFIE SI TU CHANGES DE PC/UTILISATEUR ===
MSFS_BASE = r"C:\Users\Bertrand\AppData\Local\Packages\Microsoft.Limitless_8wekyb3d8bbwe\LocalCache\Packages"
COMMUNITY = os.path.join(MSFS_BASE, "Community")
OFFICIAL = os.path.join(MSFS_BASE, "Official", "OneStore")
STREAMED = os.path.join(MSFS_BASE, "StreamedPackages")

# Dossier results dans ton repo projet
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RESULTS = os.path.join(BASE_DIR, "results")
os.makedirs(RESULTS, exist_ok=True)


def is_airport_folder(folder_name):
    # Reconnaît tous les dossiers avec un ICAO (4 lettres) et 'airport'
    # Ex: 'fs24-asobo-airport-klax-losangeles'
    m = re.search(r"(fs2[04]|fs20)?-?asobo-?airport-([a-z0-9]{4})", folder_name, re.I)
    if m:
        return m.group(2).upper()
    # Autre méthode: tout dossier contenant 'airport' + 4 lettres
    m = re.search(r"([a-z0-9]{4}).*airport", folder_name, re.I)
    if m:
        return m.group(1).upper()
    # Certains payware/freeware: juste ICAO au début
    m = re.match(r"^([a-z0-9]{4})", folder_name, re.I)
    if m:
        return m.group(1).upper()
    return None


def scan_dir(root, source):
    results = []
    if not os.path.exists(root):
        print(f"[INFO] Dossier introuvable : {root}")
        return results
    for folder in os.listdir(root):
        folder_path = os.path.join(root, folder)
        if not os.path.isdir(folder_path):
            continue
        icao = is_airport_folder(folder)
        if icao:
            results.append(
                {"icao": icao, "name": folder, "path": folder_path, "source": source}
            )
    return results


def main():
    airports = []
    airports += scan_dir(COMMUNITY, "community")
    airports += scan_dir(OFFICIAL, "official")
    airports += scan_dir(STREAMED, "streamed")

    # Filtre unique par ICAO (évite doublons si plusieurs sources)
    seen = set()
    uniq_airports = []
    for apt in airports:
        if apt["icao"] not in seen:
            uniq_airports.append(apt)
            seen.add(apt["icao"])

    out_json = os.path.join(RESULTS, "airport_scanresults.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(uniq_airports, f, ensure_ascii=False, indent=2)

    print(f"[OK] Scanné {len(uniq_airports)} aéroports.")
    print(f"[Scanner] Fichier JSON généré avec succès : {out_json}")


if __name__ == "__main__":
    main()
