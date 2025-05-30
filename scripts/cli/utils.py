# scripts/utils.py

import os
import json

def get_absolute_path(relative_path):
    """Retourne le chemin absolu à partir d'un chemin relatif au projet."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.abspath(os.path.join(base_dir, relative_path))

def read_json_file(relative_path):
    """
    Lis un fichier JSON à partir d'un chemin relatif à la racine du projet.
    Retourne les données ou None en cas d'erreur.
    """
    full_path = get_absolute_path(relative_path)
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[Erreur] Impossible de lire {full_path} : {e}")
        return None

def write_json_file(data, relative_path):
    """
    Écrit un fichier JSON avec indent=4 et UTF-8.
    Le chemin est relatif à la racine du projet.
    """
    full_path = get_absolute_path(relative_path)
    try:
        with open(full_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"[OK] Fichier JSON généré : {full_path}")
    except Exception as e:
        print(f"[Erreur] Impossible d'écrire {full_path} : {e}")
