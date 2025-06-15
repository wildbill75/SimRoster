import sys
import os
import csv
import json
import subprocess
import threading
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
    QSizePolicy,
    QSplashScreen,
    QProgressBar,
    QDialog,
    QMessageBox,
)
from PyQt5.QtCore import Qt, QUrl, QObject, pyqtSlot, QMetaObject
from PyQt5.QtGui import QFont
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtGui import QPixmap
import time


CONFIG_PATH = "data/settings_paths.json"


def run_airport_scan(progress_callback=None):
    # -- Lancement SYNCHRONE du scanner (bloque jusqu’à la fin)
    script_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../cli/airport_scanner.py")
    )
    import sys
    import subprocess

    print("[BOOT] Lancement du scanner automatique...")
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            check=True,
        )
        print("[BOOT] Scanner output:\n", result.stdout)
        if result.stderr.strip():
            print("[BOOT] Scanner errors:\n", result.stderr)
    except subprocess.CalledProcessError as e:
        print("[ERROR][BOOT] Scanner failed:", e)
        print("[ERROR][BOOT] Output:", e.stdout)
        print("[ERROR][BOOT] Stderr:", e.stderr)

class AirportDataBridge(QObject):
    def __init__(self, airports, selected_icaos):
        super().__init__()
        self._airports = airports
        self._selected_icaos = selected_icaos

    @pyqtSlot(result="QVariant")
    def get_airports(self):
        print(
            "[BRIDGE] get_airports called. Airports sent (count):", len(self._airports)
        )
        if self._airports:
            print("[BRIDGE] Sample airport:", self._airports[0])
        else:
            print("[BRIDGE] No airports available")
        return self._airports

    @pyqtSlot(result="QVariant")
    def get_selected_icaos(self):
        print(
            "[BRIDGE] get_selected_icaos called. ICAOs (count):",
            len(self._selected_icaos),
        )
        print("[BRIDGE] ICAOs list:", self._selected_icaos)
        return self._selected_icaos

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

# --- À placer tel quel dans main_gui.py, après les imports, EN REMPLAÇANT l'existante ---
def safe_float(val):
    try:
        return float(val)
    except Exception:
        return None

def load_airports_from_json_or_csv():
    airports = []
    results_path = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__), "../../results/airport_scanresults.json"
        )
    )
    csv_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../data/airports.csv")
    )

    # Index CSV pour enrichissement rapide par ICAO
    icao_to_csv = {}
    try:
        with open(csv_path, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("icao", ""):
                    icao_to_csv[row["icao"].upper()] = row
    except Exception as e:
        print("Erreur création index CSV :", e)

    if os.path.exists(results_path):
        try:
            with open(results_path, encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list) and data:
                    for entry in data:
                        icao = entry.get("icao", "").upper()
                        csv_row = icao_to_csv.get(icao, {})
                        if (
                            "icao" in entry
                            and "name" in entry
                            and "latitude" in csv_row
                            and "longitude" in csv_row
                        ):
                            airports.append(
                                {
                                    "icao": entry["icao"],
                                    "name": entry["name"],
                                    "city": csv_row.get("city", ""),
                                    "country": csv_row.get("country", ""),
                                    "latitude": safe_float(csv_row.get("latitude", "")),
                                    "longitude": safe_float(
                                        csv_row.get("longitude", "")
                                    ),
                                    "type": csv_row.get("type", ""),
                                }
                            )
            print(
                f"[INFO] {len(airports)} aéroports enrichis depuis {results_path} + {csv_path}"
            )
            return airports
        except Exception as e:
            print("[WARN] Erreur lecture du JSON scan results :", e)

    # Fallback : charge tout le CSV (si JSON absent ou invalide)
    try:
        with open(csv_path, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("icao", "") and row.get("name", ""):
                    airports.append(
                        {
                            "icao": row["icao"],
                            "name": row["name"],
                            "city": row.get("city", ""),
                            "country": row.get("country", ""),
                            "latitude": safe_float(row.get("latitude", "")),
                            "longitude": safe_float(row.get("longitude", "")),
                            "type": row.get("type", ""),
                        }
                    )

        print(f"[INFO] {len(airports)} aéroports chargés depuis {csv_path}")
    except Exception as e:
        print("Erreur chargement CSV aéroports (fallback) :", e)
    return airports

def load_aircraft_from_json_or_csv():
    """
    Charge la liste complète des avions détectés.
    (Tu dois avoir un fichier aircraft_scanresults.json dans results/)
    """
    path = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__), "../../results/aircraft_scanresults.json"
        )
    )
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
                # Normalise si besoin : {'registration': ..., 'model': ...}
                cleaned = []
                for ac in data:
                    if "registration" in ac and "model" in ac:
                        cleaned.append(ac)
                    elif "reg" in ac and "model" in ac:
                        cleaned.append(
                            {"registration": ac["reg"], "model": ac["model"]}
                        )
                return cleaned
        except Exception as e:
            print("[DEBUG] Erreur ouverture aircraft_scanresults.json :", e)
    return []  # Fallback : vide

class SplashScanDialog(QDialog):
    def __init__(self, text="Scanning your add-on folders...", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Please wait")
        self.setFixedSize(360, 120)
        self.setWindowFlags(
            self.windowFlags() | Qt.CustomizeWindowHint | Qt.WindowStaysOnTopHint
        )
        self.label = QLabel(text)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # Marque indéterminée
        layout = QVBoxLayout(self)
        layout.addWidget(self.label)
        layout.addWidget(self.progress)
        self.setLayout(layout)
        self.setStyleSheet(
            """
            QDialog { background: #23242a; color: #fff; border-radius: 10px; }
            QLabel { font-size: 16px; }
            QProgressBar { min-height: 16px; border-radius: 8px; background: #222; }
        """
        )

    def set_progress(self, value):
        pass  # Plus tard tu pourras mettre à jour une vraie barre de progression ici

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
        # --- Enregistre les chemins dans data/settings_paths.json ---
        paths = {
            "community": self.edit_community.text(),
            "streamed": self.edit_streamed.text(),
            "onestore": self.edit_onestore.text(),
        }
        save_paths(paths)
        self.paths = paths
        QMessageBox.information(self, "Information",
        "Paths saved.\nRestart the application to apply changes.")        
        print("[SETTINGS] Paths saved to config:", paths)

# ==================== FLEET MANAGER PANEL ====================
class FleetManagerPanel(QWidget):
    AIRPORTS_SELECTION_PATH = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../results/selected_airports.json")
    )
    AIRCRAFT_SELECTION_PATH = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../results/selected_aircraft.json")
    )

    def __init__(
        self,
        available_aircraft=None,
        selected_aircraft=None,
        available_airports=None,
        selected_airports=None,
        webview=None,
        parent=None,
    ):
        super().__init__(parent)
        # Données
        self.available_aircraft = available_aircraft or []
        self.selected_aircraft = selected_aircraft or []
        self.available_airports = available_airports or []
        self.selected_airports = selected_airports or []
        self.webview = webview
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

    def clean_aircraft_label(self, registration, model):
        """
        Retourne un label unique pour un avion, de type REG – Modèle.
        Si le modèle commence déjà par la REG, ne le double pas.
        """
        if model.strip().upper().startswith(registration):
            return model.strip()
        else:
            return f"{registration} – {model.strip()}"

    def _refresh_aircraft_list(self):
        self.list_aircraft_available.clear()
        for ac in self.available_aircraft:
            label = self.clean_aircraft_label(ac["registration"], ac["model"])
            item = QListWidgetItem(label)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.list_aircraft_available.addItem(item)

    def _refresh_selected_aircraft_list(self):
        self.list_aircraft_selected.clear()
        for ac in self.selected_aircraft:
            label = self.clean_aircraft_label(ac["registration"], ac["model"])
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
                    ref_label = self.clean_aircraft_label(
                        ac["registration"], ac["model"]
                    )
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
                    ref_label = self.clean_aircraft_label(
                        ac["registration"], ac["model"]
                    )
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
        try:
            to_add = []
            for i in range(self.list_airport_available.count()):
                item = self.list_airport_available.item(i)
                if item.checkState() == Qt.Checked:
                    label = item.text()
                    for ap in self.available_airports:
                        if self.clean_airport_label(ap["icao"], ap["name"]) == label:
                            to_add.append(ap)
                            break
            for ap in to_add:
                if ap not in self.selected_airports:
                    self.selected_airports.append(ap)
                if ap in self.available_airports:
                    self.available_airports.remove(ap)
            self.save_selection()
            self._refresh_airport_list()
            self._refresh_selected_airport_list()

            # PATCH FINAL : MAJ carte via QWebChannel sans reload
            try:
                print("[DEBUG] MAJ JS via QWebChannel (refreshMap())")
                if (
                    self.webview
                    and hasattr(self.webview, "page")
                    and callable(self.webview.page().runJavaScript)
                ):
                    self.webview.page().runJavaScript("if(window.refreshMap) refreshMap();")
                else:
                    print("[WARN] webview.page() ou runJavaScript indisponible")
            except Exception as e:
                import traceback

                print("[ERROR] Exception lors de l'appel refreshMap JS:", e)
                print(traceback.format_exc())
        except Exception as e:
            import traceback

            print("[CRITICAL] Crash dans add_airport():", e)
            print(traceback.format_exc())
            from PyQt5.QtWidgets import QMessageBox

            QMessageBox.critical(self, "Erreur critique", f"Crash dans add_airport():\n{e}")

    def remove_airport(self):
        try:
            to_remove = []
            for i in range(self.list_airport_selected.count()):
                item = self.list_airport_selected.item(i)
                if item.checkState() == Qt.Checked:
                    label = item.text()
                    for ap in self.selected_airports:
                        if self.clean_airport_label(ap["icao"], ap["name"]) == label:
                            to_remove.append(ap)
                            break
            for ap in to_remove:
                if ap in self.selected_airports:
                    self.selected_airports.remove(ap)
                # (Optionnel) On le remet dans la liste disponible s'il n'y est pas déjà
                if ap not in self.available_airports:
                    self.available_airports.append(ap)
            self._refresh_airport_list()
            self._refresh_selected_airport_list()

            # PATCH FINAL : MAJ carte via QWebChannel sans reload
            try:
                print("[DEBUG] MAJ JS via QWebChannel (refreshMap())")
                if (
                    self.webview
                    and hasattr(self.webview, "page")
                    and callable(self.webview.page().runJavaScript)
                ):
                    self.webview.page().runJavaScript("if(window.refreshMap) refreshMap();")
                else:
                    print("[WARN] webview.page() ou runJavaScript indisponible")
            except Exception as e:
                import traceback

                print("[ERROR] Exception lors de l'appel refreshMap JS:", e)
                print(traceback.format_exc())
        except Exception as e:
            import traceback

            print("[CRITICAL] Crash dans remove_airport():", e)
            print(traceback.format_exc())
            from PyQt5.QtWidgets import QMessageBox

            QMessageBox.critical(
                self, "Erreur critique", f"Crash dans remove_airport():\n{e}"
            )

    def reset_all(self):
        # Recharge la VRAIE liste à partir du JSON/CSV (propre !)
        self.available_airports = load_airports_from_json_or_csv()
        self.selected_airports.clear()
        self.available_aircraft = load_aircraft_from_json_or_csv()
        self.selected_aircraft.clear()
        self.save_selection()
        self._refresh_aircraft_list()
        self._refresh_selected_aircraft_list()
        self._refresh_airport_list()
        self._refresh_selected_airport_list()

    def filter_aircraft(self, text):
        """
        Filtre la liste des avions disponibles en conservant les cases à cocher,
        conserve les ticks sur les items déjà cochés même après filtrage.
        """
        checked_regs = set()
        for i in range(self.list_aircraft_available.count()):
            item = self.list_aircraft_available.item(i)
            if item.checkState() == Qt.Checked:
                reg = item.text().split(" - ")[0]
                checked_regs.add(reg)

        self.list_aircraft_available.clear()
        for ac in self.available_aircraft:
            if (
                text.lower() in ac["registration"].lower()
                or text.lower() in ac["model"].lower()
            ):
                label = self.clean_aircraft_label(ac["registration"], ac["model"])
                item = QListWidgetItem(label)
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                if ac["registration"] in checked_regs:
                    item.setCheckState(Qt.Checked)
                else:
                    item.setCheckState(Qt.Unchecked)
                self.list_aircraft_available.addItem(item)

    def filter_airports(self, text):
        """
        Filtre la liste des aéroports disponibles en conservant les cases à cocher,
        conserve les ticks sur les items déjà cochés même après filtrage.
        """
        # Mémorise les items cochés (via ICAO)
        checked_icaos = set()
        for i in range(self.list_airport_available.count()):
            item = self.list_airport_available.item(i)
            if item.checkState() == Qt.Checked:
                # On retrouve l'ICAO du label propre
                icao = item.text().split(" - ")[0]
                checked_icaos.add(icao)

        self.list_airport_available.clear()
        for ap in self.available_airports:
            if text.lower() in ap["icao"].lower() or text.lower() in ap["name"].lower():
                label = self.clean_airport_label(ap["icao"], ap["name"])
                item = QListWidgetItem(label)
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                # Restaure le check si déjà coché avant filtrage
                if ap["icao"] in checked_icaos:
                    item.setCheckState(Qt.Checked)
                else:
                    item.setCheckState(Qt.Unchecked)
                self.list_airport_available.addItem(item)

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
                valid_regs = {a["registration"] for a in self.available_aircraft}
                self.selected_aircraft = [
                    a for a in saved if a["registration"] in valid_regs
                ]
                self.available_aircraft = [
                    a
                    for a in self.available_aircraft
                    if a["registration"]
                    not in {b["registration"] for b in self.selected_aircraft}
                ]
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
        Charge la liste complète des aéroports détectés avec toutes les infos utiles
        (ICAO, name, city, country, latitude, longitude, type), en enrichissant le JSON
        avec le CSV s'il manque des champs.
        """
        return load_airports_from_json_or_csv()


# ==================== MAIN WINDOW ====================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SimRoster")
        self.resize(1440, 900)
        self.showMaximized()

        # --- NAVIGATION LATÉRALE ---
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

        # --- LAYOUT PRINCIPAL ---
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(nav_widget)

        # --- CARTE UNIQUE ---
        self.web_view = QWebEngineView()
        map_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../results/map_dashboard.html")
        )
        self.web_view.load(QUrl.fromLocalFile(map_path))
        self.web_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # --- BRIDGE UNIQUE POUR LA CARTE ---
        try:
            with open(
                os.path.join(
                    os.path.dirname(__file__), "../../results/airport_scanresults.json"
                ),
                "r",
                encoding="utf-8",
            ) as f:
                map_data = json.load(f)
        except Exception as e:
            print("[DEBUG] Erreur ouverture airport_scanresults.json :", e)
            map_data = []
        try:
            with open(
                os.path.join(
                    os.path.dirname(__file__), "../../results/selected_airports.json"
                ),
                "r",
                encoding="utf-8",
            ) as f:
                selected_icaos = [a["icao"] for a in json.load(f)]
        except Exception as e:
            print("[DEBUG] Erreur ouverture selected_airports.json :", e)
            selected_icaos = []

        self.bridge = AirportDataBridge(map_data, selected_icaos)
        self.channel = QWebChannel()
        self.channel.registerObject("airportBridgeDashboard", self.bridge)

        def attach_dashboard_bridge():
            self.web_view.page().setWebChannel(self.channel)
            print("[DEBUG] QWebChannel attaché à la carte principale (fond)")

        self.web_view.loadFinished.connect(attach_dashboard_bridge)

        # --- PANELS OVERLAY ---
        self.overlay_stack = QStackedWidget()
        self.overlay_stack.setStyleSheet("background: transparent;")

        # DASHBOARD PANEL (vide, juste titre, à étoffer selon besoin)
        dashboard_panel = QWidget()
        dashboard_layout = QVBoxLayout(dashboard_panel)
        dashboard_layout.setContentsMargins(0, 0, 0, 0)
        dashboard_layout.setSpacing(0)
        dashboard_title = QLabel("Dashboard")
        dashboard_title.setStyleSheet(
            "font-size: 22px; font-weight: 600; color: #ffffff; background: none; margin-top:30px; margin-bottom:20px;"
        )
        dashboard_title.setAlignment(Qt.AlignCenter)
        dashboard_layout.addWidget(dashboard_title)
        dashboard_layout.addStretch(1)

        # FLEET MANAGER PANEL
        aircraft_init = load_aircraft_from_json_or_csv()
        airports_init = load_airports_from_json_or_csv()
        fleet_panel = FleetManagerPanel(
            available_aircraft=aircraft_init,
            selected_aircraft=[],
            available_airports=airports_init,
            selected_airports=[],
            webview=self.web_view,
        )

        # SETTINGS PANEL
        settings_panel = SettingsPanel(self)

        # Ajoute les panels à la stack (ordre: Dashboard=0, Fleet=1, Settings=2)
        self.overlay_stack.addWidget(dashboard_panel)
        self.overlay_stack.addWidget(fleet_panel)
        self.overlay_stack.addWidget(settings_panel)

        # --- CONTAINER GLOBAL : Disposition horizontale, panel overlay à droite ---
        right_container = QWidget()
        right_layout = QHBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # La carte (expanding, prend toute la place dispo)
        right_layout.addWidget(self.web_view, stretch=1)

        # PANEL OVERLAY À DROITE (Fleet, Dashboard, Settings) -- largeur fixe
        self.overlay_stack.setFixedWidth(int(self.width() * 0.38))  # Ajuste selon le besoin
        self.overlay_stack.setStyleSheet("background: #23242a; border-radius: 0px;")

        right_layout.addWidget(self.overlay_stack, stretch=0)

        main_layout.addWidget(right_container)

        self.setCentralWidget(main_widget)

        # --- NAVIGATION ---
        self.btn_dashboard.clicked.connect(lambda: self.set_panel(0))
        self.btn_fleetmanager.clicked.connect(lambda: self.set_panel(1))
        self.btn_settings.clicked.connect(lambda: self.set_panel(2))
        self.btn_quit.clicked.connect(self.close)

        self.set_panel(0)

    def set_panel(self, index):
        # Gère l'état "checked" des boutons (menu actif)
        for btn, idx in zip(
            [self.btn_dashboard, self.btn_fleetmanager, self.btn_settings], [0, 1, 2]
        ):
            btn.setChecked(idx == index)
        self.overlay_stack.setCurrentIndex(index)

    def show_test_minimal(self):
        from PyQt5.QtWebEngineWidgets import QWebEngineView
        from PyQt5.QtWebChannel import QWebChannel
        from PyQt5.QtCore import QUrl, QObject, pyqtSlot

        class Bridge(QObject):
            @pyqtSlot(result=str)
            def ping(self):
                print("[BRIDGE] ping called")
                return "pong"

        HTML = """
<!DOCTYPE html>
<html lang="en">

<head>
  <meta charset="utf-8" />
  <title>SimRoster – Airport Map</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <script type="text/javascript" src="qrc:///qtwebchannel/qwebchannel.js"></script>
  <style>
    html,
    body,
    #map {
      height: 100%;
      width: 100vw;
      margin: 0;
      padding: 0;
      overflow: hidden;
    }

    #map {
      min-height: 400px;
      min-width: 400px;
    }
  </style>
  <!-- Leaflet -->
  <link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css" />
</head>

<body>
  <div id="map"></div>
  <!-- Leaflet JS -->
  <script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
  <!-- QWebChannel (PyQt) -->
  <script>
    console.log("DEBUG MAP.HTML : script exécuté, document.URL = " + document.URL);

    // Initialisation de la carte
    var map = L.map('map', {
      center: [12.609094496251984, 3.1436270680393745], // centre monde, zoom large
      zoom: 5,
      zoomControl: true,
      scrollWheelZoom: true
    });
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      attribution: '© OpenStreetMap, © CartoDB',
      maxZoom: 15,
      minZoom: 2
    }).addTo(map);

    // --- Bridge PyQt → JS, markers dynamiques ---
    function setupBridge() {
      // On vérifie que qt ET qt.webChannelTransport sont bien présents
      if (typeof qt === "undefined" || !qt.webChannelTransport) {
        console.warn("qt ou qt.webChannelTransport pas prêt, retry dans 100ms...");
        setTimeout(setupBridge, 100);
        return;
      }

      console.log("QWebChannel present, bridge ready to call Python...");
      new QWebChannel(qt.webChannelTransport, function (channel) {
        console.log("CALLBACK QWEBCHANNEL EXECUTED !!");
        // On expose le bridge globalement pour debug/dynamique
        window.airportBridge = channel.objects.airportBridge;
        console.log("window.airportBridge exposé =", typeof window.airportBridge);

        if (typeof window.airportBridge === "undefined") {
          console.error("window.airportBridge est toujours undefined juste après l'exposition !");
        } else {
          console.log("window.airportBridge EST OK !");
        }

        // -- Rendu des marqueurs dynamiques --
        window.airportBridge.get_airports(function (airports) {
          window.airportBridge.get_selected_icaos(function (selectedIcaos) {
            airports.forEach(function (ap) {
              if (!ap.latitude || !ap.longitude) return;
              var isSelected = selectedIcaos.includes(ap.icao);
              var color = isSelected ? "green" : "gray";
              var marker = L.circleMarker([ap.latitude, ap.longitude], {
                radius: 6,
                fillColor: color,
                color: color,
                weight: 1,
                opacity: 1,
                fillOpacity: 0.85
              }).addTo(map);

              var popup = "<b>" + ap.icao + "</b><br/>" + ap.name;
              if (ap.city) popup += "<br/>" + ap.city;
              if (ap.country) popup += "<br/>" + ap.country;
              marker.bindPopup(popup);
            });
          });
        });
      });
    }

    // Lance le setup du bridge avec sécurité "retry"
    document.addEventListener("DOMContentLoaded", setupBridge);
  </script>
</body>
</html>

        """

        win = QMainWindow(self)
        win.setWindowTitle("Test QWebChannel SimRoster")
        view = QWebEngineView(win)
        win.setCentralWidget(view)

        # QWebChannel setup
        channel = QWebChannel()
        bridge = Bridge()
        channel.registerObject("bridge", bridge)
        view.page().setWebChannel(channel)

        # Charge le HTML localement
        view.setHtml(HTML, QUrl("qrc:///"))

        win.resize(800, 600)
        win.show()


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)

    # --- SPLASH SCREEN DE SCAN ---
    splash = SplashScanDialog()
    splash.show()
    app.processEvents()  # S'assure que la fenêtre s'affiche AVANT le scan

    # LANCE LE SCAN AUTOMATIQUE
    try:
        airports = run_airport_scan(progress_callback=splash.set_progress)
        splash.set_progress(100)
        splash.close()
    except Exception as e:
        import traceback

        splash.close()
        from PyQt5.QtWidgets import QMessageBox

        QMessageBox.critical(
            None,
            "Erreur critique",
            f"Erreur lors du scan des aéroports :\n{e}\n\n{traceback.format_exc()}",
        )
        sys.exit(1)

    # --- LANCE L'INTERFACE GRAPHIQUE PRINCIPALE ---
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
