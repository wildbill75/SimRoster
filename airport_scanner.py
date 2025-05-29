import os
import json
import argparse

# Aéroports connus — dictionnaire ICAO → nom + source
HARDCODED_AIRPORTS = {
    "LFPO": {
        "name": "Paris-Orly",
        "source": "community",
        "path": "C:/Users/Bertrand/AppData/Local/Packages/Microsoft.Limitless_8wekyb3d8bbwe/LocalCache/Packages/Community/LFPO"
    },
    "LFMN": {
        "name": "Nice-Côte d'Azur",
        "source": "official",
        "path": "C:/Users/Bertrand/AppData/Local/Packages/Microsoft.Limitless_8wekyb3d8bbwe/LocalCache/Packages/StreamedPackages/fs24-microsoft-airport-lfmn-nice"
    }
}

def scan_airports(verbose=False):
    results = []
    for icao, info in HARDCODED_AIRPORTS.items():
        if os.path.exists(info["path"]):
            result = {
                "icao": icao,
                "name": info["name"],
                "path": info["path"],
                "source": info["source"]
            }
            results.append(result)
            if verbose:
                print(f"→ {icao} | {info['name']}")
        else:
            if verbose:
                print(f"[WARNING] Dossier introuvable pour {icao} : {info['path']}")
    return results

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    if args.verbose:
        print("[Scanner] Lancement du scanner d'aéroports...")

    results = scan_airports(verbose=args.verbose)

    with open("airport_scanresults.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)

    if args.verbose:
        print("[Scanner] Fichier JSON généré avec succès : airport_scanresults.json")

if __name__ == "__main__":
    main()
