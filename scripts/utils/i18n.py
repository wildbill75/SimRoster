import os
import json

class Translator:
    def __init__(self, language="en"):
        self.language = language
        self.translations = {}
        self.load_translations()

    def set_language(self, language):
        self.language = language
        self.load_translations()

    def load_translations(self):
        # ✅ Accès au dossier 'translations' à la racine du projet
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "translations"))
        lang_file = os.path.join(base_path, f"{self.language}.json")

        try:
            with open(lang_file, "r", encoding="utf-8") as f:
                self.translations = json.load(f)
            print(f"[INFO] Traductions chargées depuis {lang_file}")
        except FileNotFoundError:
            print(f"[ERREUR] Fichier de traduction introuvable : {lang_file}")
            self.translations = {}
        except json.JSONDecodeError as e:
            print(f"[ERREUR] Problème JSON dans {lang_file} : {e}")
            self.translations = {}

    def t(self, key):
        return self.translations.get(key, f"[{key}]")
