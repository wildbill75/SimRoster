import sys
import os
import csv
import json
import subprocess
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QPushButton,
    QLabel,
    QListWidget,
    QVBoxLayout,
    QHBoxLayout,
    QStackedWidget,
    QFrame,
    QSizePolicy,
    QLineEdit,
    QListWidgetItem,
    QToolButton,
    QFileDialog,
)
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QFont
from PyQt5.QtWebEngineWidgets import QWebEngineView

CONFIG_PATH = "data/settings_paths.json"


def get_default_paths():
    home = os.path.expanduser("~")
    return {
        "community": os.path.join(
            home,
            "AppData/Local/Packages/Microsoft.FlightSimulator_8wekyb3d8bbwe/LocalCache/Packages/Community",
        ),
        "streamed": os.path.join(
            home,
            "AppData/Local/Packages/Microsoft.FlightSimulator_8wekyb3d8bbwe/LocalCache/Packages/StreamedPackages",
        ),
        "onestore": os.path.join(
            home,
            "AppData/Local/Packages/Microsoft.FlightSimulator_8wekyb3d8bbwe/LocalCache/Packages/Official/OneStore",
        ),
    }

def load_paths():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return get_default_paths()

def save_paths(paths):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(paths, f, indent=2, ensure_ascii=False)

def load_airports_from_json_or_csv():
    airports = []
    results_path = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__), "../../results/airport_scanresults.json"
        )
    )
    if os.path.exists(results_path):
        try:
            with open(results_path, encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list) and data:
                    for entry in data:
                        if "icao" in entry and "name" in entry:
                            airports.append(
                                {"icao": entry["icao"], "name": entry["name"]}
                            )
            print(f"[INFO] {len(airports)} aéroports chargés depuis {results_path}")
            return airports
        except Exception as e:
            print("[WARN] Erreur lecture du JSON scan results :", e)

    csv_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../data/airports.csv")
    )
    try:
        with open(csv_path, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("icao", "") and row.get("name", ""):
                    airports.append({"icao": row["icao"], "name": row["name"]})
        print(f"[INFO] {len(airports)} aéroports chargés depuis {csv_path}")
    except Exception as e:
        print("Erreur chargement CSV aéroports (fallback) :", e)
    return airports

# ================= SETTINGS PANEL =====================
class SettingsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: #23242a; border-radius: 8px; color: #fff;")
        vbox = QVBoxLayout(self)
        vbox.setContentsMargins(30, 28, 30, 28)
        vbox.setSpacing(28)

        label_style = """
            font-size: 14px;
            color: #fff;
            font-weight: bold;
            background: none;
            padding: 0;
            min-width: 190px;
            max-width: 250px;
        """
        field_style = """
            background: #343842;
            color: #fff;
            font-size: 14px;
            border: 1px solid #444;
            border-radius: 0px;
            padding: 5px 8px;
            min-width: 250px; max-width: 390px;
            selection-background-color: #555;
        """
        btn_style = """
            background: #8d9099;
            color: #222;
            font-size: 15px;
            border: none;
            border-radius: 6px;
            font-weight: bold;
            margin: 0;
            padding: 0;
            min-width: 24px; min-height: 24px; max-width: 24px; max-height: 24px;
        """

        self.paths = load_paths()

        def make_row(label_text, lineedit, browse_func):
            row = QHBoxLayout()
            row.setSpacing(8)
            lbl = QLabel(label_text)
            lbl.setStyleSheet(label_style)
            lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            lbl.setFixedWidth(210)
            row.addWidget(lbl, 0)

            lineedit.setStyleSheet(field_style)
            lineedit.setMinimumHeight(24)
            lineedit.setMaximumHeight(24)
            lineedit.setMaximumWidth(390)
            lineedit.setAlignment(Qt.AlignLeft)
            row.addWidget(lineedit, 1)

            btn = QToolButton()
            btn.setText("⋯")
            btn.setStyleSheet(btn_style)
            btn.setFixedSize(24, 24)
            btn.clicked.connect(lambda: browse_func(lineedit))
            row.addWidget(btn, 0)

            return row

        self.edit_community = QLineEdit(self.paths["community"])
        vbox.addLayout(
            make_row("Community Folder:", self.edit_community, self.select_folder)
        )

        self.edit_streamed = QLineEdit(self.paths["streamed"])
        vbox.addLayout(
            make_row("StreamedPackages Folder:", self.edit_streamed, self.select_folder)
        )

        self.edit_onestore = QLineEdit(self.paths["onestore"])
        vbox.addLayout(
            make_row(
                "Official\\OneStore Folder:", self.edit_onestore, self.select_folder
            )
        )

        btns_row = QHBoxLayout()
        btns_row.setSpacing(20)

        self.btn_save = QToolButton()
        self.btn_save.setText("Save")
        self.btn_save.setStyleSheet(
            """
            background: #8d9099;
            color: #222;
            border: none;
            border-radius: 0px;
            font-weight: bold;
            font-size: 15px;
            padding: 8px 32px;
            min-width: 80px;
            min-height: 26px;
        """
        )
        self.btn_save.clicked.connect(self.save_paths)
        btns_row.addWidget(self.btn_save)

        self.btn_scan = QToolButton()
        self.btn_scan.setText("Scan")
        self.btn_scan.setStyleSheet(
            """
            background: #55bb77;
            color: #fff;
            border: none;
            border-radius: 0px;
            font-weight: bold;
            font-size: 15px;
            padding: 8px 32px;
            min-width: 80px;
            min-height: 26px;
        """
        )
        self.btn_scan.clicked.connect(self.scan_now)
        btns_row.addWidget(self.btn_scan)

        vbox.addSpacing(14)
        vbox.addLayout(btns_row)
        vbox.addStretch(1)

    def select_folder(self, lineedit):
        folder = QFileDialog.getExistingDirectory(
            self, "Choose Folder", lineedit.text()
        )
        if folder:
            lineedit.setText(folder)

    def save_paths(self):
        paths = {
            "community": self.edit_community.text(),
            "streamed": self.edit_streamed.text(),
            "onestore": self.edit_onestore.text(),
        }
        save_paths(paths)
        self.paths = paths

    def scan_now(self):
        import sys
        import subprocess  # <== à ajouter si absent en haut du fichier

        # 1. Importe le vrai helper de config, pas de gestion maison !
        from scripts.utils.config_helper import load_config, save_config

        # 2. Récupère les valeurs des chemins depuis les widgets
        community = self.edit_community.text()
        streamed = self.edit_streamed.text()
        onestore = self.edit_onestore.text()

        # 3. Charge l'ancienne config (si existante)
        config = load_config()
        config["community_dir"] = community
        config["official_onestore_dir"] = onestore
        config["streamedpackages_dir"] = streamed
        save_config(config)
        print(
            f"[INFO] Config saved at (unique): {__import__('os').path.abspath(__import__('os').path.join(__import__('os').path.dirname(__file__), '../../config/paths.json'))}"
        )

        # 4. Lance le scanner normalement (ne change rien ici)
        script_path = __import__("os").path.abspath(
            __import__("os").path.join(
                __import__("os").path.dirname(__file__), "../cli/airport_scanner.py"
            )
        )
        print(f"[INFO] Running scanner: {script_path}")
        try:
            result = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                text=True,
                check=True,
            )
            print("[SCAN] Scanner output:\n", result.stdout)
            if result.stderr.strip():
                print("[SCAN] Scanner errors:\n", result.stderr)
        except subprocess.CalledProcessError as e:
            print("[ERROR] Scanner failed:", e)
            print("[ERROR] Output:", e.stdout)
            print("[ERROR] Stderr:", e.stderr)

# ==================== FLEET MANAGER PANEL ====================
class FleetManagerPanel(QWidget):
    AIRPORTS_SELECTION_PATH = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../data/selected_airports.json")
    )
    AIRCRAFT_SELECTION_PATH = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../data/selected_aircraft.json")
    )

    def __init__(
        self,
        available_aircraft=None,
        selected_aircraft=None,
        available_airports=None,
        selected_airports=None,
        parent=None,
    ):
        super().__init__(parent)
        # Données
        self.available_aircraft = available_aircraft or []
        self.selected_aircraft = selected_aircraft or []
        self.available_airports = available_airports or []
        self.selected_airports = selected_airports or []
        self.restore_selection()  # Persistance

        # =========== Layout principal ===========
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(38, 26, 38, 26)
        main_layout.setSpacing(16)

        # ---------- Titre ----------
        title = QLabel("Fleet Manager")
        title.setStyleSheet(
            "font-size: 22px; font-weight: 600; color: #ffffff; background: none;"
        )
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        # ---------- Scan Now ----------
        self.btn_scan = QPushButton("Scan Now")
        self.btn_scan.setStyleSheet(
            "background: #8d9099; color: #222; font-weight: bold; border-radius: 0px; font-size: 14px; padding: 8px 32px; min-width: 120px;"
        )
        main_layout.addWidget(self.btn_scan, alignment=Qt.AlignCenter)
        self.btn_scan.clicked.connect(self.scan_and_reload)

        # ---------- Available Aircraft ----------
        lbl_aircraft = QLabel("Available Aircraft")
        lbl_aircraft.setStyleSheet("font-size: 15px; color: #fff; font-weight: bold;")
        main_layout.addWidget(lbl_aircraft)
        # Search aircraft
        self.aircraft_search = QLineEdit()
        self.aircraft_search.setPlaceholderText("Search Aircraft...")
        self.aircraft_search.setStyleSheet(
            "background: #343842; color: #fff; font-size: 14px; border-radius: 0; border: none; margin-bottom: 4px; padding: 6px 8px;"
        )
        self.aircraft_search.textChanged.connect(self.filter_aircraft)
        main_layout.addWidget(self.aircraft_search)
        self.list_aircraft_available = QListWidget()
        self.list_aircraft_available.setSelectionMode(QListWidget.MultiSelection)
        self.list_aircraft_available.setStyleSheet(
            "background: #343842; color: #fff; font-size: 14px; border: none;"
        )
        main_layout.addWidget(self.list_aircraft_available)
        aircraft_btns_layout = QHBoxLayout()
        self.btn_aircraft_add = QPushButton("↓ Add Aircraft")
        self.btn_aircraft_remove = QPushButton("↑ Remove Aircraft")
        for b in [self.btn_aircraft_add, self.btn_aircraft_remove]:
            b.setStyleSheet(
                "background: #8d9099; color: #222; border: none; border-radius: 0px; font-weight: 600; padding: 8px 10px; font-size: 13px;"
            )
        aircraft_btns_layout.addWidget(self.btn_aircraft_add)
        aircraft_btns_layout.addWidget(self.btn_aircraft_remove)
        main_layout.addLayout(aircraft_btns_layout)
        self.btn_aircraft_add.clicked.connect(self.add_aircraft)
        self.btn_aircraft_remove.clicked.connect(self.remove_aircraft)

        lbl_aircraft_sel = QLabel("Selected Aircraft")
        lbl_aircraft_sel.setStyleSheet(
            "font-size: 15px; color: #fff; font-weight: bold;"
        )
        main_layout.addWidget(lbl_aircraft_sel)
        self.list_aircraft_selected = QListWidget()
        self.list_aircraft_selected.setStyleSheet(
            "background: #343842; color: #fff; font-size: 14px; border: none;"
        )
        main_layout.addWidget(self.list_aircraft_selected)

        # ---------- Available Airports ----------
        lbl_airport = QLabel("Available Airports")
        lbl_airport.setStyleSheet("font-size: 15px; color: #fff; font-weight: bold;")
        main_layout.addWidget(lbl_airport)
        self.airport_search = QLineEdit()
        self.airport_search.setPlaceholderText("Search ICAO or name...")
        self.airport_search.setStyleSheet(
            "background: #343842; color: #fff; font-size: 14px; border-radius: 0; border: none; margin-bottom: 4px; padding: 6px 8px;"
        )
        self.airport_search.textChanged.connect(self.filter_airports)
        main_layout.addWidget(self.airport_search)
        self.list_airport_available = QListWidget()
        self.list_airport_available.setSelectionMode(QListWidget.MultiSelection)
        self.list_airport_available.setStyleSheet(
            "background: #343842; color: #fff; font-size: 14px; border: none;"
        )
        main_layout.addWidget(self.list_airport_available)
        airport_btns_layout = QHBoxLayout()
        self.btn_airport_add = QPushButton("↓ Add Airport")
        self.btn_airport_remove = QPushButton("↑ Remove Airport")
        for b in [self.btn_airport_add, self.btn_airport_remove]:
            b.setStyleSheet(
                "background: #8d9099; color: #222; border: none; border-radius: 0px; font-weight: 600; padding: 8px 10px; font-size: 13px;"
            )
        airport_btns_layout.addWidget(self.btn_airport_add)
        airport_btns_layout.addWidget(self.btn_airport_remove)
        main_layout.addLayout(airport_btns_layout)
        self.btn_airport_add.clicked.connect(self.add_airport)
        self.btn_airport_remove.clicked.connect(self.remove_airport)

        lbl_airport_sel = QLabel("Selected Airports")
        lbl_airport_sel.setStyleSheet(
            "font-size: 15px; color: #fff; font-weight: bold;"
        )
        main_layout.addWidget(lbl_airport_sel)
        self.list_airport_selected = QListWidget()
        self.list_airport_selected.setStyleSheet(
            "background: #343842; color: #fff; font-size: 14px; border: none;"
        )
        main_layout.addWidget(self.list_airport_selected)

        # ---------- Reset All ----------
        self.btn_reset_all = QPushButton("Reset All")
        self.btn_reset_all.setStyleSheet(
            "background: #8d9099; color: #222; border: none; border-radius: 0px; font-weight: bold; font-size: 14px; margin-top: 8px; min-width: 80px;"
        )
        main_layout.addWidget(self.btn_reset_all, alignment=Qt.AlignCenter)
        self.btn_reset_all.clicked.connect(self.reset_all)

        # Affichage initial
        self._refresh_aircraft_list()
        self._refresh_selected_aircraft_list()
        self._refresh_airport_list()
        self._refresh_selected_airport_list()

        # --- PATCH anti-double ICAO ---

    def clean_airport_label(self, icao, name):
        """
        Retourne un label unique de type ICAO – Nom.
        Si le nom commence déjà par l’ICAO, ne le double pas.
        """
        if name.strip().upper().startswith(icao):
            return name.strip()
        else:
            return f"{icao} – {name.strip()}"

    def clean_aircraft_label(self, reg, model):
        """
        Retourne un label unique pour un avion, de type REG – Modèle.
        Si le modèle commence déjà par la REG, ne le double pas.
        """
        if model.strip().upper().startswith(reg):
            return model.strip()
        else:
            return f"{reg} – {model.strip()}"

    def _refresh_aircraft_list(self):
        self.list_aircraft_available.clear()
        for ac in self.available_aircraft:
            label = self.clean_aircraft_label(ac["reg"], ac["model"])
            item = QListWidgetItem(label)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.list_aircraft_available.addItem(item)

    def _refresh_selected_aircraft_list(self):
        self.list_aircraft_selected.clear()
        for ac in self.selected_aircraft:
            label = self.clean_aircraft_label(ac["reg"], ac["model"])
            item = QListWidgetItem(label)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.list_aircraft_selected.addItem(item)

    def _refresh_airport_list(self):
        self.list_airport_available.clear()
        for ap in self.available_airports:
            label = self.clean_airport_label(ap["icao"], ap["name"])
            item = QListWidgetItem(label)
            # Active la case à cocher (checked = non coché par défaut)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.list_airport_available.addItem(item)

    def _refresh_selected_airport_list(self):
        self.list_airport_selected.clear()
        for ap in self.selected_airports:
            label = self.clean_airport_label(ap["icao"], ap["name"])
            item = QListWidgetItem(label)
            # Ajoute la case à cocher pour chaque aéroport sélectionné
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.list_airport_selected.addItem(item)

    def add_aircraft(self):
        to_add = []
        for i in range(self.list_aircraft_available.count()):
            item = self.list_aircraft_available.item(i)
            if item.checkState() == Qt.Checked:
                label = item.text()
                for ac in self.available_aircraft:
                    ref_label = self.clean_aircraft_label(ac["reg"], ac["model"])
                    if ref_label == label:
                        to_add.append(ac)
                        break
        for ac in to_add:
            if ac not in self.selected_aircraft:
                self.selected_aircraft.append(ac)
            if ac in self.available_aircraft:
                self.available_aircraft.remove(ac)
        self._refresh_aircraft_list()
        self._refresh_selected_aircraft_list()

    def remove_aircraft(self):
        to_remove = []
        for i in range(self.list_aircraft_selected.count()):
            item = self.list_aircraft_selected.item(i)
            if item.checkState() == Qt.Checked:
                label = item.text()
                for ac in self.selected_aircraft:
                    ref_label = self.clean_aircraft_label(ac["reg"], ac["model"])
                    if ref_label == label:
                        to_remove.append(ac)
                        break
        for ac in to_remove:
            if ac in self.selected_aircraft:
                self.selected_aircraft.remove(ac)
            if ac not in self.available_aircraft:
                self.available_aircraft.append(ac)
        self._refresh_aircraft_list()
        self._refresh_selected_aircraft_list()

    def add_airport(self):
        for idx in reversed(range(self.list_airport_available.count())):
            if self.list_airport_available.item(idx).isSelected():
                ap = self.available_airports.pop(idx)
                self.selected_airports.append(ap)
        self.save_selection()
        self._refresh_airport_list()
        self._refresh_selected_airport_list()

    def remove_airport(self):

        to_remove = []
        for i in range(self.list_airport_selected.count()):
            item = self.list_airport_selected.item(i)
            if item.checkState() == Qt.Checked:
                label = item.text()
                for ap in self.selected_airports:
                    if self.clean_airport_label(ap["icao"], ap["name"]) == label:
                        to_remove.append(ap)
                        break
        # Retire tous les aéroports cochés de la sélection
        for ap in to_remove:
            if ap in self.selected_airports:
                self.selected_airports.remove(ap)
            # (Optionnel) On le remet dans la liste disponible s'il n'y est pas déjà
            if ap not in self.available_airports:
                self.available_airports.append(ap)
        self._refresh_airport_list()
        self._refresh_selected_airport_list()

    def reset_all(self):
        self.available_aircraft += self.selected_aircraft
        self.selected_aircraft.clear()
        self.available_airports += self.selected_airports
        self.selected_airports.clear()
        self.save_selection()
        self._refresh_aircraft_list()
        self._refresh_selected_aircraft_list()
        self._refresh_airport_list()
        self._refresh_selected_airport_list()

    def filter_aircraft(self, text):
        self.list_aircraft_available.clear()
        for ac in self.available_aircraft:
            if text.lower() in ac["reg"].lower() or text.lower() in ac["model"].lower():
                self.list_aircraft_available.addItem(f"{ac['reg']} – {ac['model']}")

    def filter_airports(self, text):
        self.list_airport_available.clear()
        for ap in self.available_airports:
            if text.lower() in ap["icao"].lower() or text.lower() in ap["name"].lower():
                self.list_airport_available.addItem(f"{ap['icao']} – {ap['name']}")

    def save_selection(self):
        os.makedirs(os.path.dirname(self.AIRPORTS_SELECTION_PATH), exist_ok=True)
        os.makedirs(os.path.dirname(self.AIRCRAFT_SELECTION_PATH), exist_ok=True)
        with open(self.AIRPORTS_SELECTION_PATH, "w", encoding="utf-8") as f:
            json.dump(self.selected_airports, f, indent=2, ensure_ascii=False)
        with open(self.AIRCRAFT_SELECTION_PATH, "w", encoding="utf-8") as f:
            json.dump(self.selected_aircraft, f, indent=2, ensure_ascii=False)

    def restore_selection(self):
        # Airports
        try:
            with open(self.AIRPORTS_SELECTION_PATH, encoding="utf-8") as f:
                saved = json.load(f)
                valid_icaos = {a["icao"] for a in self.available_airports}
                self.selected_airports = [a for a in saved if a["icao"] in valid_icaos]
                self.available_airports = [
                    a
                    for a in self.available_airports
                    if a["icao"] not in {b["icao"] for b in self.selected_airports}
                ]
        except Exception:
            self.selected_airports = []
        # Aircraft
        try:
            with open(self.AIRCRAFT_SELECTION_PATH, encoding="utf-8") as f:
                saved = json.load(f)
                valid_regs = {a["reg"] for a in self.available_aircraft}
                self.selected_aircraft = [a for a in saved if a["reg"] in valid_regs]
                self.available_aircraft = [
                    a
                    for a in self.available_aircraft
                    if a["reg"] not in {b["reg"] for b in self.selected_aircraft}
                ]
        except Exception:
            self.selected_aircraft = []

    def scan_and_reload(self):
        print("[DEBUG] Scan lancé. Rafraîchir la liste après le scan réel.")
        self.available_airports = self.load_real_airports()
        # Supprime tout ce qui n’est plus dispo dans la sélection actuelle
        valid_icaos = {a["icao"] for a in self.available_airports}
        self.selected_airports = [
            a for a in self.selected_airports if a["icao"] in valid_icaos
        ]
        # Et réactualise la liste visuelle
        self._refresh_airport_list()
        self._refresh_selected_airport_list()
        # Optionnel : sauvegarde la sélection automatiquement
        self.save_selection()

    def save_selection(self):
        os.makedirs(os.path.dirname(self.AIRPORTS_SELECTION_PATH), exist_ok=True)
        os.makedirs(os.path.dirname(self.AIRCRAFT_SELECTION_PATH), exist_ok=True)
        with open(self.AIRPORTS_SELECTION_PATH, "w", encoding="utf-8") as f:
            json.dump(self.selected_airports, f, indent=2, ensure_ascii=False)
        with open(self.AIRCRAFT_SELECTION_PATH, "w", encoding="utf-8") as f:
            json.dump(self.selected_aircraft, f, indent=2, ensure_ascii=False)

    def restore_selection(self):
        # Airports
        try:
            with open(self.AIRPORTS_SELECTION_PATH, encoding="utf-8") as f:
                saved = json.load(f)
                valid_icaos = {a["icao"] for a in self.available_airports}
                self.selected_airports = [a for a in saved if a["icao"] in valid_icaos]
                self.available_airports = [a for a in self.available_airports if a["icao"] not in {b["icao"] for b in self.selected_airports}]
        except Exception:
            self.selected_airports = []
        # Aircraft
        try:
            with open(self.AIRCRAFT_SELECTION_PATH, encoding="utf-8") as f:
                saved = json.load(f)
                valid_regs = {a["reg"] for a in self.available_aircraft}
                self.selected_aircraft = [a for a in saved if a["reg"] in valid_regs]
                self.available_aircraft = [a for a in self.available_aircraft if a["reg"] not in {b["reg"] for b in self.selected_aircraft}]
        except Exception:
            self.selected_aircraft = []

    def validate_airport_selection(self):
        selected = []
        for i in range(self.list_airport_available.count()):
            item = self.list_airport_available.item(i)
            if item.checkState() == Qt.Checked:
                label = item.text()
                for ap in self.available_airports:
                    if self.clean_airport_label(ap["icao"], ap["name"]) == label:
                        selected.append(ap)
                        break
        self.selected_airports = selected
        self._refresh_selected_airport_list()

    def load_real_airports(self):
        """
            Charge la liste des aéroports réellement détectés lors du scan,
            à partir du fichier results/airport_scanresults.json.
            Retourne une liste de dicts {"icao": ..., "name": ...}
            """
        path = os.path.abspath(
                os.path.join(
                    os.path.dirname(__file__), "../../results/airport_scanresults.json"
                )
            )
        if not os.path.exists(path):
            print("[ERREUR] Fichier airport_scanresults.json introuvable :", path)
            return []
        with open(path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                # Garde uniquement les champs ICAO et Name, ignore les doublons
                seen = set()
                airports = []
                for ap in data:
                    icao = ap.get("icao")
                    name = ap.get("name", "")
                    if icao and icao not in seen:
                        seen.add(icao)
                        airports.append({"icao": icao, "name": name})
                return airports
            except Exception as e:
                print("[ERREUR] Problème lecture airport_scanresults.json:", e)
                return []


# ==================== MAIN WINDOW ====================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SimRoster")
        self.resize(1440, 900)
        self.showMaximized()  # Plein écran au lancement

        nav_widget = QWidget()
        nav_layout = QVBoxLayout(nav_widget)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(0)
        nav_widget.setStyleSheet("background: #181818;")

        title = QLabel("SimRoster")
        title.setStyleSheet(
            "font-size: 24px; font-weight: bold; color: #ffffff; padding: 24px 8px 24px 16px; letter-spacing: 2px;"
        )
        nav_layout.addWidget(title, alignment=Qt.AlignTop)

        self.btn_dashboard = QPushButton("Dashboard")
        self.btn_fleetmanager = QPushButton("Fleet Manager")
        self.btn_settings = QPushButton("Settings")
        self.btn_quit = QPushButton("Quit")

        for btn in [
            self.btn_dashboard,
            self.btn_fleetmanager,
            self.btn_settings,
            self.btn_quit,
        ]:
            btn.setCheckable(True)
            btn.setStyleSheet(
                """
                QPushButton {
                    color: #ffffff; font-size: 17px; padding: 14px 18px; background: none; border: none; text-align: left;
                }
                QPushButton:checked, QPushButton:pressed {
                    color: #ffffff;
                }
                QPushButton:hover {
                    color: #ffffff;
                    border: none;   
                    border-radius: 0px;         
                    background: #2f2f2f;
                }
            """
            )
            nav_layout.addWidget(btn)

        nav_layout.addStretch(1)
        nav_widget.setFixedWidth(210)

        self.central_stack = QStackedWidget()

        dashboard_panel = QWidget()
        dashboard_layout = QVBoxLayout(dashboard_panel)
        dashboard_layout.setContentsMargins(0, 0, 0, 0)
        dashboard_layout.setSpacing(0)

        self.web_view = QWebEngineView()
        map_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../results/map.html")
        )
        self.web_view.load(QUrl.fromLocalFile(map_path))
        self.web_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        dashboard_layout.addWidget(self.web_view)
        self.central_stack.addWidget(dashboard_panel)

        fleet_panel_container = QWidget()
        fleet_panel_layout = QHBoxLayout(fleet_panel_container)
        fleet_panel_layout.setContentsMargins(0, 0, 0, 0)
        fleet_panel_layout.setSpacing(0)

        fleet_panel_widget = QWidget()
        fleet_panel_widget.setFixedWidth(int(self.width() * 0.46))
        fleet_panel_widget.setStyleSheet(
            """
            background: #212121;
            border-radius: 0px;
            box-shadow: 0 4px 24px 0 rgba(16,18,23,0.08);
        """
        )
        vbox = QVBoxLayout(fleet_panel_widget)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)

        def load_aircraft_sample():
            return [
                {"reg": "F-HBJB", "model": "A320neo Air France"},
                {"reg": "D-AIZC", "model": "A320 Lufthansa"},
            ]

        aircraft_init = load_aircraft_sample()
        airports_init = load_airports_from_json_or_csv()
        fleet_manager_core = FleetManagerPanel(
            available_aircraft=aircraft_init,
            selected_aircraft=[],
            available_airports=airports_init,
            selected_airports=[],
        )

        vbox.addWidget(fleet_manager_core)
        vbox.addStretch(1)

        fleet_map_view = QWebEngineView()
        fleet_map_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../results/map.html")
        )
        fleet_map_view.load(QUrl.fromLocalFile(fleet_map_path))
        fleet_map_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        fleet_panel_layout.addWidget(fleet_panel_widget)
        fleet_panel_layout.addWidget(fleet_map_view)

        self.central_stack.addWidget(fleet_panel_container)

        settings_panel_container = QWidget()
        settings_panel_layout = QHBoxLayout(settings_panel_container)
        settings_panel_layout.setContentsMargins(0, 0, 0, 0)
        settings_panel_layout.setSpacing(0)

        settings_panel_widget = QWidget()
        settings_panel_widget.setFixedWidth(int(self.width() * 0.46))
        settings_panel_widget.setStyleSheet(
            """
            background: #212121;
            border-radius: 0px;
            box-shadow: 0 4px 24px 0 rgba(16,18,23,0.08);
            """
        )
        vbox_settings = QVBoxLayout(settings_panel_widget)
        vbox_settings.setContentsMargins(0, 0, 0, 0)
        vbox_settings.setSpacing(0)

        title = QLabel("Settings")
        title.setStyleSheet(
            """
            font-size: 22px;
            font-weight: 600;
            color: #ffffff;
            background: none;
            """
        )
        title.setAlignment(Qt.AlignCenter)
        vbox_settings.addSpacing(18)
        vbox_settings.addWidget(title)
        vbox_settings.addSpacing(20)

        settings_core = SettingsPanel(self)
        settings_core.setStyleSheet(
            """
            background: #23242a;
            border-radius: 8px;
            padding: 18px 20px 22px 20px;
            color: #fff;
            """
        )
        vbox_settings.addWidget(settings_core)
        vbox_settings.addStretch(1)

        settings_map_view = QWebEngineView()
        settings_map_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../results/map.html")
        )
        settings_map_view.load(QUrl.fromLocalFile(settings_map_path))
        settings_map_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        settings_panel_layout.addWidget(settings_panel_widget)
        settings_panel_layout.addWidget(settings_map_view)

        self.central_stack.addWidget(settings_panel_container)

        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(nav_widget)
        main_layout.addWidget(self.central_stack)
        self.setCentralWidget(main_widget)

        self.btn_dashboard.clicked.connect(
            lambda: self.central_stack.setCurrentIndex(0)
        )
        self.btn_fleetmanager.clicked.connect(
            lambda: self.central_stack.setCurrentIndex(1)
        )
        self.btn_settings.clicked.connect(lambda: self.central_stack.setCurrentIndex(2))
        self.btn_quit.clicked.connect(self.close)

        self.btn_dashboard.setChecked(True)
        self.central_stack.setCurrentIndex(0)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    font = QFont("Roboto", 12)
    app.setFont(font)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
