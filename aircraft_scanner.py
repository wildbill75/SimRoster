import os
import json
import argparse
import configparser


def parse_aircraft_cfg(cfg_path):
    config = configparser.ConfigParser(strict=False)
    config.read(cfg_path, encoding='utf-8')
    section = 'FLTSIM.0'
    return {
        'registration': config.get(section, 'atc_id', fallback='').strip(),
        'company': config.get(section, 'atc_airline', fallback='').strip(),
        'icao': config.get(section, 'icao_airline', fallback='').strip()
    }


def scan_fenix_aircraft(community_path, verbose=False):
    models = {
        'fnx-aircraft-319-liveries': 'A319',
        'fnx-aircraft-320-liveries': 'A320',
        'fnx-aircraft-321-liveries': 'A321'
    }

    aircraft_list = []
    for folder in os.listdir(community_path):
        if folder not in models:
            continue

        model = models[folder]
        liveries_root = os.path.join(community_path, folder, 'SimObjects', 'Airplanes')
        if not os.path.isdir(liveries_root):
            continue

        for livery_folder in os.listdir(liveries_root):
            full_path = os.path.join(liveries_root, livery_folder)
            cfg_path = os.path.join(full_path, 'aircraft.cfg')
            if not os.path.isfile(cfg_path):
                continue

            cfg_data = parse_aircraft_cfg(cfg_path)
            if not cfg_data['registration']:
                continue  # skip if no valid registration

            aircraft = {
                'model': model,
                'registration': cfg_data['registration'],
                'company': cfg_data['company'],
                'icao': cfg_data['icao']
            }

            aircraft_list.append(aircraft)
            if verbose:
                print(f"→ {model} | {aircraft['company']} | {aircraft['registration']}")

    return aircraft_list


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--verbose', action='store_true')
    args = parser.parse_args()

    print("[DEBUG] aircraft_scanner.py lancé")

    community_path = os.path.expandvars(
        "C:/Users/Bertrand/AppData/Local/Packages/Microsoft.Limitless_8wekyb3d8bbwe/LocalCache/Packages/Community"
    )
    print(f"[Scanner] Community = {community_path}")

    aircraft_list = scan_fenix_aircraft(community_path, verbose=args.verbose)

    output_file = os.path.join(os.getcwd(), "aircraft_scanresults.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(aircraft_list, f, indent=4, ensure_ascii=False)

    print(f"[Scanner] Nombre d'avions Fenix détectés : {len(aircraft_list)}")
    print(f"[Scanner] Fichier JSON généré avec succès : {os.path.basename(output_file)}")


if __name__ == "__main__":
    main()
