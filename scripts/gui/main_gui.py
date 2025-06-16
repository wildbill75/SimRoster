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
    QInputDialog,
    QComboBox,
)
from PyQt5.QtCore import Qt, QUrl, QObject, pyqtSlot, QMetaObject
from PyQt5.QtGui import QFont
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtGui import QPixmap
import time


CONFIG_PATH = "data/settings_paths.json"
DIALOG_STYLESHEET = """
QDialog {
    background: #23242b;
}
QLabel {
    color: #fff;
    font-size: 17px;
}
QLineEdit, QComboBox {
    background: #343842;
    color: #fff;
    font-size: 16px;
    border: 1px solid #404040;
    border-radius: 6px;
    padding: 7px 10px;
}
QComboBox QAbstractItemView {
    background: #343842;
    color: #fff;
    selection-background-color: #3b3f4b;
    selection-color: #fff;
    border-radius: 6px;
    font-size: 16px;
}
QPushButton {
    font-size: 15px;
}
"""
PANEL_STYLESHEET = """
    QWidget {
        background: #23242a;
        color: #fff;
        font-size: 14px;
    }
    QLabel {
        color: #fff;
    }
    QComboBox, QLineEdit {
        background: #343842;
        color: #fff;
        border-radius: 6px;
        font-size: 14px;
    }
    QListWidget {
        background: #343842;
        color: #fff;
        border: none;
        font-size: 14px;
    }
    QPushButton {
        background: #8d9099;
        color: #222;
        border: none;
        border-radius: 6px;
        font-weight: 600;
        padding: 8px 18px;
        font-size: 13px;
        min-width: 120px;
    }
    QPushButton#ManualAddButton {
        background: #88C070;
        color: #111;
        font-weight: 600;
        border: none;
        border-radius: 6px;
        padding: 8px 18px;
        font-size: 13px;
        min-width: 120px;
    }
"""


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
    def __init__(self, get_airports_func, get_selected_icaos_func):
        super().__init__()
        self._get_airports_func = get_airports_func
        self._get_selected_icaos_func = get_selected_icaos_func

    @pyqtSlot(result="QVariant")
    def get_airports(self):
        airports = self._get_airports_func()
        print("[BRIDGE] get_airports called. Airports sent (count):", len(airports))
        if airports:
            print("[BRIDGE] Sample airport:", airports[0])
        else:
            print("[BRIDGE] No airports available")
        return airports

    @pyqtSlot(result="QVariant")
    def get_selected_icaos(self):
        selected_icaos = self._get_selected_icaos_func()
        print(
            "[BRIDGE] get_selected_icaos called. ICAOs (count):",
            len(selected_icaos),
        )
        print("[BRIDGE] ICAOs list:", selected_icaos)
        return selected_icaos

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
        self.setStyleSheet(PANEL_STYLESHEET)
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
        title = QLabel("FLEET MANAGER")
        title.setStyleSheet(
            "font-size: 22px; font-weight: 600; color: #ffffff; background: none;"
        )
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        # ---------- Available Aircraft ----------
        lbl_aircraft = QLabel("Available Aircraft")
        main_layout.addWidget(lbl_aircraft)

        self.aircraft_search = QLineEdit()
        self.aircraft_search.setPlaceholderText("Search Aircraft...")
    
        self.aircraft_search.textChanged.connect(self.filter_aircraft)
        main_layout.addWidget(self.aircraft_search)

        self.list_aircraft_available = QListWidget()
        self.list_aircraft_available.setSelectionMode(QListWidget.NoSelection)
        main_layout.addWidget(self.list_aircraft_available)

        # --- Aircraft buttons (↓ Add, ↑ Remove, + Manual Add à droite) ---
        aircraft_btns_layout = QHBoxLayout()
        aircraft_btns_layout.setSpacing(12)
        self.btn_aircraft_add = QPushButton("↓ Add Aircraft") 
        aircraft_btns_layout.addWidget(self.btn_aircraft_add)
        self.btn_aircraft_remove = QPushButton("↑ Remove Aircraft")
        aircraft_btns_layout.addWidget(self.btn_aircraft_remove)
        aircraft_btns_layout.addStretch(1)
        self.btn_add_manual_aircraft = QPushButton("+ Manual Add")
        self.btn_add_manual_aircraft.setObjectName("ManualAddButton")
        aircraft_btns_layout.addWidget(self.btn_add_manual_aircraft)

        self.btn_add_manual_aircraft.clicked.connect(self.open_manual_add_aircraft_dialog)
        main_layout.addLayout(aircraft_btns_layout)
        main_layout.addSpacing(18)

        self.btn_aircraft_add.clicked.connect(self.add_aircraft)
        self.btn_aircraft_remove.clicked.connect(self.remove_aircraft)

        # ---------- Selected Aircraft ----------
        lbl_aircraft_sel = QLabel("Selected Aircraft")
        main_layout.addWidget(lbl_aircraft_sel)

        self.list_aircraft_selected = QListWidget()
        self.list_aircraft_selected.setSelectionMode(QListWidget.NoSelection)
        main_layout.addWidget(self.list_aircraft_selected)

        # ---------- Available Airports ----------
        lbl_airport = QLabel("Available Airports")
        main_layout.addWidget(lbl_airport)
        self.airport_search = QLineEdit()
        self.airport_search.setPlaceholderText("Search ICAO or name...")
        self.airport_search.textChanged.connect(self.filter_airports)
        main_layout.addWidget(self.airport_search)
        self.list_airport_available = QListWidget()
        self.list_airport_available.setSelectionMode(QListWidget.NoSelection)
        main_layout.addWidget(self.list_airport_available)

        # --- Airport buttons (↓ Add, ↑ Remove, + Manual Add à droite) ---
        # ---------- Boutons Airport (alignés comme Aircraft) ----------
        airport_btns_layout = QHBoxLayout()
        airport_btns_layout.setSpacing(12)

        self.btn_airport_add = QPushButton("↓ Add Airport")
        airport_btns_layout.addWidget(self.btn_airport_add)

        self.btn_airport_remove = QPushButton("↑ Remove Airport")
        airport_btns_layout.addWidget(self.btn_airport_remove)

        airport_btns_layout.addStretch()  # <-- SANS VALEUR, juste comme ça

        self.btn_add_manual_airport = QPushButton("+ Manual Add")
        self.btn_add_manual_airport.setObjectName("ManualAddButton")
        airport_btns_layout.addWidget(self.btn_add_manual_airport)

        main_layout.addLayout(airport_btns_layout)
        main_layout.addSpacing(18)


        # Connexions
        self.btn_airport_add.clicked.connect(self.add_airport)
        self.btn_airport_remove.clicked.connect(self.remove_airport)
        self.btn_add_manual_airport.clicked.connect(self.add_manual_airport_dialog)

        lbl_airport_sel = QLabel("Selected Airports")
        main_layout.addWidget(lbl_airport_sel)
        self.list_airport_selected = QListWidget()
        self.list_airport_selected.setSelectionMode(QListWidget.NoSelection)
        main_layout.addWidget(self.list_airport_selected)

        # ---------- Reset All ----------
        self.btn_reset_all = QPushButton("Reset All")
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

    def clean_aircraft_label(self, registration, model, company=None, engine=None):
        """
        Retourne un label enrichi : REG – MODELE – COMPAGNIE – ENGINE (si dispo)
        """
        label = f"{registration} – {model}"
        if company:
            label += f" – {company}"
        if engine:
            label += f" – {engine}"
        return label

    def _refresh_aircraft_list(self):
        self.list_aircraft_available.clear()
        for ac in self.available_aircraft:
            label = self.clean_aircraft_label(
                ac.get("registration", ""),
                ac.get("model", ""),
                ac.get("company", ""),
                ac.get("engine", ""),
            )
            item = QListWidgetItem(label)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.list_aircraft_available.addItem(item)

    def _refresh_selected_aircraft_list(self):
        self.list_aircraft_selected.clear()
        for ac in self.selected_aircraft:
            label = self.clean_aircraft_label(
                ac.get("registration", ""),
                ac.get("model", ""),
                ac.get("company", ""),
                ac.get("engine", ""),
            )
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
        """Déplace les avions cochés d'Available vers Selected (sans supprimer du JSON)."""
        to_add = []
        for i in range(self.list_aircraft_available.count()):
            item = self.list_aircraft_available.item(i)
            if item.checkState() == Qt.Checked:
                label = item.text()
                for ac in self.available_aircraft:
                    ref_label = self.clean_aircraft_label(
                        ac.get("registration", ""),
                        ac.get("model", ""),
                        ac.get("company", ""),
                        ac.get("engine", ""),
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
        self.save_selection()

    def remove_aircraft(self):
        """Déplace les avions cochés de Selected vers Available (sans supprimer du JSON)."""
        to_remove = []
        for i in range(self.list_aircraft_selected.count()):
            item = self.list_aircraft_selected.item(i)
            if item.checkState() == Qt.Checked:
                label = item.text()
                for ac in self.selected_aircraft:
                    ref_label = self.clean_aircraft_label(
                        ac.get("registration", ""),
                        ac.get("model", ""),
                        ac.get("company", ""),
                        ac.get("engine", ""),
                    )
                    if ref_label == label:
                        to_remove.append(ac)
                        break
        for ac in to_remove:
            if ac not in self.available_aircraft:
                self.available_aircraft.append(ac)
            if ac in self.selected_aircraft:
                self.selected_aircraft.remove(ac)
        self._refresh_aircraft_list()
        self._refresh_selected_aircraft_list()
        self.save_selection()

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

            # --- Refresh dynamique de la carte ---
            if hasattr(self, 'webview') and self.webview:
                self.webview.page().runJavaScript("window.refreshMap && window.refreshMap();")

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
                if ap not in self.available_airports:
                    self.available_airports.append(ap)
            self._refresh_airport_list()
            self._refresh_selected_airport_list()

            self.save_selection()  # <<< AJOUT OBLIGATOIRE ICI ! <<<

            # --- Refresh dynamique de la carte ---
            if hasattr(self, "webview") and self.webview:
                self.webview.page().runJavaScript(
                    "window.refreshMap && window.refreshMap();"
                )

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

    def add_manual_airport_dialog(self):
        from PyQt5.QtWidgets import (
            QDialog,
            QVBoxLayout,
            QHBoxLayout,
            QLabel,
            QLineEdit,
            QPushButton,
            QMessageBox,
        )
        import os, json

        dlg = QDialog(self)
        dlg.setWindowTitle("Manual Add Airport")
        dlg.setFixedSize(700, 360)
        dlg.setStyleSheet(DIALOG_STYLESHEET)

        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(28, 22, 28, 22)
        layout.setSpacing(24)

        # --- ICAO
        icao_layout = QHBoxLayout()
        lbl_icao = QLabel("ICAO*")
        icao_edit = QLineEdit()
        icao_edit.setPlaceholderText("ex: LFPG")
        icao_layout.addWidget(lbl_icao)
        icao_layout.addWidget(icao_edit)
        layout.addLayout(icao_layout)

        # --- Name
        name_layout = QHBoxLayout()
        lbl_name = QLabel("Airport Name*")
        name_edit = QLineEdit()
        name_edit.setPlaceholderText("ex: Paris Charles de Gaulle")
        name_layout.addWidget(lbl_name)
        name_layout.addWidget(name_edit)
        layout.addLayout(name_layout)

        # --- Latitude
        lat_layout = QHBoxLayout()
        lbl_lat = QLabel("Latitude*")
        lat_edit = QLineEdit()
        lat_edit.setPlaceholderText("ex: 48.7262")
        lat_layout.addWidget(lbl_lat)
        lat_layout.addWidget(lat_edit)
        layout.addLayout(lat_layout)

        # --- Longitude
        lon_layout = QHBoxLayout()
        lbl_lon = QLabel("Longitude*")
        lon_edit = QLineEdit()
        lon_edit.setPlaceholderText("ex: 2.3652")
        lon_layout.addWidget(lbl_lon)
        lon_layout.addWidget(lon_edit)
        layout.addLayout(lon_layout)

        # --- Dossier scenery
        folder_layout = QHBoxLayout()
        lbl_folder = QLabel("Scenery Folder*")
        folder_edit = QLineEdit()
        folder_edit.setMinimumWidth(160)
        btn_browse = QPushButton("Browse")
        btn_browse.setStyleSheet(
            "background: #8d9099; color: #fff; border: none; border-radius: 6px; "
            "font-weight: 600; padding: 8px 26px; font-size: 15px; min-width: 90px;"
        )
        btn_browse.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        def browse_folder():
            from PyQt5.QtWidgets import QFileDialog
            folder = QFileDialog.getExistingDirectory(dlg, "Select Airport Folder")
            if folder:
                folder_edit.setText(folder)
        btn_browse.clicked.connect(browse_folder)
        folder_layout.addWidget(lbl_folder)
        folder_layout.addWidget(folder_edit)
        folder_layout.addWidget(btn_browse)
        layout.addLayout(folder_layout)

        # --- Boutons Add / Cancel
        btns_layout = QHBoxLayout()
        btns_layout.addStretch(1)
        btn_add = QPushButton("Add")
        btn_cancel = QPushButton("Cancel")
        btn_add.setStyleSheet(
            "background: #88C070; color: #111; border: none; border-radius: 6px; "
            "font-weight: 600; padding: 8px 26px; font-size: 15px; min-width: 120px;"
        )
        btn_cancel.setStyleSheet(
            "background: #8d9099; color: #fff; border: none; border-radius: 6px; "
            "font-weight: 600; padding: 8px 26px; font-size: 15px; min-width: 120px;"
        )
        btns_layout.addWidget(btn_add)
        btns_layout.addWidget(btn_cancel)
        layout.addLayout(btns_layout)

        btn_cancel.clicked.connect(dlg.reject)

        def try_add_airport():
            icao = icao_edit.text().strip().upper()
            name = name_edit.text().strip()
            lat_str = lat_edit.text().strip()
            lon_str = lon_edit.text().strip()
            folder = folder_edit.text().strip()
            if not icao or len(icao) != 4:
                QMessageBox.warning(dlg, "Error", "ICAO code is required (4 letters).")
                return
            if not name:
                QMessageBox.warning(dlg, "Error", "Airport name is required.")
                return
            try:
                lat = float(lat_str)
                lon = float(lon_str)
            except Exception:
                QMessageBox.warning(dlg, "Error", "Latitude and longitude must be numbers.")
                return
            if not folder or not os.path.exists(folder):
                QMessageBox.warning(dlg, "Error", "Valid folder is required.")
                return
            airport_entry = {
                "icao": icao,
                "name": name,
                "path": folder,
                "latitude": lat,
                "longitude": lon,
            }
            self.available_airports.append(airport_entry)
            self.available_airports = sorted(
                self.available_airports, key=lambda a: a["icao"]
            )
            # Update JSON
            results_path = os.path.abspath(
                os.path.join(
                    os.path.dirname(__file__), "../../results/airport_scanresults.json"
                )
            )
            try:
                if os.path.exists(results_path):
                    with open(results_path, encoding="utf-8") as f:
                        json_data = json.load(f)
                        if not isinstance(json_data, list):
                            json_data = []
                else:
                    json_data = []
                json_data = [a for a in json_data if a.get("icao", "").upper() != icao]
                json_data.append(airport_entry)
                json_data = sorted(json_data, key=lambda a: a["icao"])
                with open(results_path, "w", encoding="utf-8") as f:
                    json.dump(json_data, f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"[ERROR][MANUAL ADD] Failed to update airport_scanresults.json: {e}")

            self._refresh_airport_list()
            if hasattr(self, "webview") and self.webview:
                self.webview.page().runJavaScript(
                    "window.refreshMap && window.refreshMap();"
                )
            QMessageBox.information(
                self, "Airport added", f"Manual airport {icao} added to the available list."
            )
            dlg.accept()

        btn_add.clicked.connect(try_add_airport)
        dlg.exec_()

    def lookup_airport_csv(self, icao):
        """Cherche un ICAO dans airports.csv, retourne un dict (name, lat, lon) ou None si non trouvé."""
        icao = icao.strip().upper()
        csv_path = self.airports_csv_path  # Adapte ici si variable différente !
        if not os.path.isfile(csv_path):
            return None
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("icao", "").strip().upper() == icao:
                    # Les clés exactes dépendent de ton CSV, adapte si besoin.
                    name = row.get("name", "")
                    try:
                        lat = float(row.get("latitude", ""))
                        lon = float(row.get("longitude", ""))
                    except ValueError:
                        lat = lon = None
                    return {
                        "name": name,
                        "latitude": lat,
                        "longitude": lon,
                    }
        return None

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
        # --- Refresh dynamique de la carte ---
        if hasattr(self, "webview") and self.webview:
            self.webview.page().runJavaScript("window.refreshMap && window.refreshMap();")

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

    def open_manual_add_aircraft_dialog(self):
        from PyQt5.QtWidgets import (
            QDialog,
            QVBoxLayout,
            QHBoxLayout,
            QLabel,
            QLineEdit,
            QPushButton,
            QComboBox,
            QMessageBox,
            QSizePolicy,
            QWidget,
        )
        from PyQt5.QtCore import Qt

        dlg = QDialog(self)
        dlg.setWindowTitle("Manual Add Aircraft")
        dlg.setFixedSize(440, 380)
        dlg.setStyleSheet(DIALOG_STYLESHEET)

        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(28, 22, 28, 22)
        layout.setSpacing(24)

        # --- Registration
        reg_layout = QHBoxLayout()
        lbl_reg = QLabel("Registration*")
        reg_edit = QLineEdit()
        reg_edit.setPlaceholderText("ex: F-HTYN")
        reg_edit.setMinimumWidth(180)
        reg_layout.addWidget(lbl_reg)
        reg_layout.addWidget(reg_edit)
        layout.addLayout(reg_layout)

        # --- Modèle
        model_layout = QHBoxLayout()
        lbl_model = QLabel("Model*")
        model_combo = QComboBox()
        model_combo.addItems(["A319", "A320", "A321"])
        model_combo.setMinimumWidth(120)
        model_layout.addWidget(lbl_model)
        model_layout.addWidget(model_combo)
        layout.addLayout(model_layout)

        # --- Compagnie
        company_layout = QHBoxLayout()
        lbl_company = QLabel("Company")
        company_edit = QLineEdit()
        company_edit.setPlaceholderText("ex: Air France")
        company_edit.setMinimumWidth(180)
        company_layout.addWidget(lbl_company)
        company_layout.addWidget(company_edit)
        layout.addLayout(company_layout)

        # --- Type moteur
        engine_layout = QHBoxLayout()
        lbl_engine = QLabel("Engine")
        engine_combo = QComboBox()
        engine_combo.addItems(["UNKNOWN", "CFM", "IAE"])
        engine_combo.setMinimumWidth(120)
        engine_layout.addWidget(lbl_engine)
        engine_layout.addWidget(engine_combo)
        layout.addLayout(engine_layout)

        # --- Boutons
        btns_layout = QHBoxLayout()
        btns_layout.addStretch(1)
        btn_add = QPushButton("Add")
        btn_cancel = QPushButton("Cancel")
        # Styles boutons comme Add/Remove Airport
        btn_style = (
            "background: #8d9099; color: #fff; border: none; border-radius: 6px; "
            "font-weight: 600; padding: 8px 26px; font-size: 15px; min-width: 120px;"
        )
        btn_add.setStyleSheet(
            "background: #88C070; color: #111; border: none; border-radius: 6px; "
            "font-weight: 600; padding: 8px 26px; font-size: 15px; min-width: 120px;"
        )
        btn_cancel.setStyleSheet(btn_style)
        btns_layout.addWidget(btn_add)
        btns_layout.addWidget(btn_cancel)
        layout.addLayout(btns_layout)

        btn_cancel.clicked.connect(dlg.reject)

        def try_add_aircraft():
            registration = reg_edit.text().strip().upper()
            if not registration or len(registration) < 3:
                QMessageBox.warning(dlg, "Error", "Registration is required (min 3 chars).")
                return
            if any(
                a["registration"].upper() == registration
                for a in self.available_aircraft + self.selected_aircraft
            ):
                QMessageBox.warning(
                    dlg, "Error", "This registration already exists in your lists."
                )
                return
            model = model_combo.currentText()
            company = company_edit.text().strip()
            engine = engine_combo.currentText()
            new_ac = {
                "registration": registration,
                "model": model,
                "company": company,
                "engine": engine,
            }
            self.available_aircraft.append(new_ac)
            self.save_aircraft_scanresults()
            self._refresh_aircraft_list()
            dlg.accept()
            QMessageBox.information(
                self,
                "Aircraft added",
                f"{registration} ({model}) added to the available aircraft.",
            )

        btn_add.clicked.connect(try_add_aircraft)
        dlg.exec_()

    def open_manual_add_airport_dialog(self):
        from PyQt5.QtWidgets import (
            QDialog,
            QVBoxLayout,
            QHBoxLayout,
            QLabel,
            QLineEdit,
            QPushButton,
            QMessageBox,
        )
        from PyQt5.QtCore import Qt
        import os, json

        dlg = QDialog(self)
        dlg.setWindowTitle("Manual Add Airport")
        dlg.setFixedSize(600, 360)
        dlg.setStyleSheet(DIALOG_STYLESHEET)

        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(28, 22, 28, 22)
        layout.setSpacing(24)

        # --- ICAO code
        icao_layout = QHBoxLayout()
        lbl_icao = QLabel("ICAO*")
        icao_edit = QLineEdit()
        icao_edit.setPlaceholderText("ex: LFPG")
        icao_layout.addWidget(lbl_icao)
        icao_layout.addWidget(icao_edit)
        layout.addLayout(icao_layout)

        # --- Name
        name_layout = QHBoxLayout()
        lbl_name = QLabel("Airport Name*")
        name_edit = QLineEdit()
        name_edit.setPlaceholderText("ex: Paris Charles de Gaulle")
        name_layout.addWidget(lbl_name)
        name_layout.addWidget(name_edit)
        layout.addLayout(name_layout)

        # --- Latitude
        lat_layout = QHBoxLayout()
        lbl_lat = QLabel("Latitude*")
        lat_edit = QLineEdit()
        lat_edit.setPlaceholderText("ex: 48.7262")
        lat_layout.addWidget(lbl_lat)
        lat_layout.addWidget(lat_edit)
        layout.addLayout(lat_layout)

        # --- Longitude
        lon_layout = QHBoxLayout()
        lbl_lon = QLabel("Longitude*")
        lon_edit = QLineEdit()
        lon_edit.setPlaceholderText("ex: 2.3652")
        lon_layout.addWidget(lbl_lon)
        lon_layout.addWidget(lon_edit)
        layout.addLayout(lon_layout)

        # --- Dossier
        folder_layout = QHBoxLayout()
        lbl_folder = QLabel("Scenery Folder*")
        folder_edit = QLineEdit()
        btn_browse = QPushButton("Browse")

        def browse_folder():
            from PyQt5.QtWidgets import QFileDialog

            folder = QFileDialog.getExistingDirectory(dlg, "Select Airport Folder")
            if folder:
                folder_edit.setText(folder)

        btn_browse.clicked.connect(browse_folder)
        folder_layout.addWidget(lbl_folder)
        folder_layout.addWidget(folder_edit)
        folder_layout.addWidget(btn_browse)
        layout.addLayout(folder_layout)

        # --- Boutons
        btns_layout = QHBoxLayout()
        btns_layout.addStretch(1)
        btn_add = QPushButton("Add")
        btn_cancel = QPushButton("Cancel")
        btn_add.setStyleSheet(
            "background: #88C070; color: #111; border: none; border-radius: 6px; "
            "font-weight: 600; padding: 8px 26px; font-size: 15px; min-width: 120px;"
        )
        btn_cancel.setStyleSheet(
            "background: #8d9099; color: #fff; border: none; border-radius: 6px; "
            "font-weight: 600; padding: 8px 26px; font-size: 15px; min-width: 120px;"
        )
        btns_layout.addWidget(btn_add)
        btns_layout.addWidget(btn_cancel)
        layout.addLayout(btns_layout)

        btn_cancel.clicked.connect(dlg.reject)

        def try_add_airport():
            icao = icao_edit.text().strip().upper()
            name = name_edit.text().strip()
            lat_str = lat_edit.text().strip()
            lon_str = lon_edit.text().strip()
            folder = folder_edit.text().strip()
            if not icao or len(icao) != 4:
                QMessageBox.warning(dlg, "Error", "ICAO code is required (4 letters).")
                return
            if not name:
                QMessageBox.warning(dlg, "Error", "Airport name is required.")
                return
            try:
                lat = float(lat_str)
                lon = float(lon_str)
            except Exception:
                QMessageBox.warning(dlg, "Error", "Latitude and longitude must be numbers.")
                return
            if not folder or not os.path.exists(folder):
                QMessageBox.warning(dlg, "Error", "Valid folder is required.")
                return
            # Construction de l'entrée aéroport
            airport_entry = {
                "icao": icao,
                "name": name,
                "path": folder,
                "latitude": lat,
                "longitude": lon,
            }
            self.available_airports.append(airport_entry)
            self.available_airports = sorted(
                self.available_airports, key=lambda a: a["icao"]
            )
            # Mise à jour du JSON
            results_path = os.path.abspath(
                os.path.join(
                    os.path.dirname(__file__), "../../results/airport_scanresults.json"
                )
            )
            try:
                if os.path.exists(results_path):
                    with open(results_path, encoding="utf-8") as f:
                        json_data = json.load(f)
                        if not isinstance(json_data, list):
                            json_data = []
                else:
                    json_data = []
                # Remove any previous ICAO entry
                json_data = [a for a in json_data if a.get("icao", "").upper() != icao]
                json_data.append(airport_entry)
                json_data = sorted(json_data, key=lambda a: a["icao"])
                with open(results_path, "w", encoding="utf-8") as f:
                    json.dump(json_data, f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"[ERROR][MANUAL ADD] Failed to update airport_scanresults.json: {e}")

            self._refresh_airport_list()
            if hasattr(self, "webview") and self.webview:
                self.webview.page().runJavaScript(
                    "window.refreshMap && window.refreshMap();"
                )
            QMessageBox.information(
                self, "Airport added", f"Manual airport {icao} added to the available list."
            )
            dlg.accept()

        btn_add.clicked.connect(try_add_airport)
        dlg.exec_()

    def save_aircraft_scanresults(self):
        import os, json

        results_path = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__), "../../results/aircraft_scanresults.json"
            )
        )
        # Recharge tout, ajoute l’avion si unique registration
        try:
            if os.path.exists(results_path):
                with open(results_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if not isinstance(data, list):
                    data = []
            else:
                data = []
            # Ajoute tous les avions uniques (pas de doublon REG)
            seen = set()
            all_ac = data + [ac for ac in self.available_aircraft if ac not in data]
            cleaned = []
            for ac in all_ac:
                reg = ac.get("registration", "").upper()
                if reg and reg not in seen:
                    cleaned.append(ac)
                    seen.add(reg)
            with open(results_path, "w", encoding="utf-8") as f:
                json.dump(cleaned, f, indent=2, ensure_ascii=False)
            print("[DEBUG][MANUAL ADD] aircraft_scanresults.json updated.")
        except Exception as e:
            print("[ERROR][MANUAL ADD] Failed to update aircraft_scanresults.json:", e)

# ==================== FLIGHT PLANNING PANEL ====================
class FlightPlanningPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)

        # Title
        title = QLabel("FLIGHT PLANNING")
        title.setStyleSheet(
            "font-size: 22px; font-weight: 600; color: #ffffff; background: none;"
        )
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # -- Row: Aircraft selection
        aircraft_row = QHBoxLayout()
        lbl_aircraft = QLabel("Aircraft")
        lbl_aircraft.setStyleSheet("font-size: 15px; color: #fff;")
        self.aircraft_combo = QComboBox()
        self.aircraft_combo.setMinimumWidth(220)
        self.aircraft_combo.setStyleSheet(
            "background: #23242a; color: #fff; font-size: 14px;"
        )
        aircraft_row.addWidget(lbl_aircraft)
        aircraft_row.addWidget(self.aircraft_combo)
        aircraft_row.addStretch(1)
        layout.addLayout(aircraft_row)

        # -- Row: Departure Airport
        dep_row = QHBoxLayout()
        lbl_dep = QLabel("Departure")
        lbl_dep.setStyleSheet("font-size: 15px; color: #fff;")
        self.dep_combo = QComboBox()
        self.dep_combo.setMinimumWidth(180)
        self.dep_combo.setStyleSheet(
            "background: #23242a; color: #fff; font-size: 14px;"
        )
        dep_row.addWidget(lbl_dep)
        dep_row.addWidget(self.dep_combo)
        dep_row.addStretch(1)
        layout.addLayout(dep_row)

        # -- Row: Arrival Airport
        arr_row = QHBoxLayout()
        lbl_arr = QLabel("Arrival")
        lbl_arr.setStyleSheet("font-size: 15px; color: #fff;")
        self.arr_combo = QComboBox()
        self.arr_combo.setMinimumWidth(180)
        self.arr_combo.setStyleSheet(
            "background: #23242a; color: #fff; font-size: 14px;"
        )
        arr_row.addWidget(lbl_arr)
        arr_row.addWidget(self.arr_combo)
        arr_row.addStretch(1)
        layout.addLayout(arr_row)

        # -- Row: Company filter (optional)
        company_row = QHBoxLayout()
        lbl_company = QLabel("Airline")
        lbl_company.setStyleSheet("font-size: 15px; color: #fff;")
        self.company_combo = QComboBox()
        self.company_combo.setMinimumWidth(180)
        self.company_combo.setStyleSheet(
            "background: #23242a; color: #fff; font-size: 14px;"
        )
        company_row.addWidget(lbl_company)
        company_row.addWidget(self.company_combo)
        company_row.addStretch(1)
        layout.addLayout(company_row)

        # -- Search Button
        btn_row = QHBoxLayout()
        self.btn_search = QPushButton("Search real flights")
        self.btn_search.setStyleSheet(
            "background: #88C070; color: #111; font-weight: 600; font-size: 15px; "
            "border-radius: 8px; padding: 12px 32px; min-width: 200px;"
        )
        btn_row.addStretch(1)
        btn_row.addWidget(self.btn_search)
        btn_row.addStretch(1)
        layout.addLayout(btn_row)

        # -- Results List
        results_label = QLabel("Matching Flights")
        results_label.setStyleSheet(
            "font-size: 15px; color: #fff; font-weight: bold; margin-top: 8px;"
        )
        layout.addWidget(results_label)

        self.flights_list = QListWidget()
        self.flights_list.setStyleSheet(
            "background: #343842; color: #fff; font-size: 14px; border: none;"
        )
        layout.addWidget(self.flights_list)

        # -- Populate combos with user selection (dummy at first)
        self.populate_combos()

        # -- Connect logic
        self.btn_search.clicked.connect(self.search_real_flights)
        self.aircraft_combo.currentIndexChanged.connect(self.sync_company_from_aircraft)

    def refresh_panel(self):
        """Reload les combos à partir des JSON de sélection."""
        self.populate_combos()
        # Tu pourrais aussi vider les résultats de recherche pour éviter les artefacts :
        self.flights_list.clear()

    def populate_combos(self):
        # --- Chemins JSON
        base_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../results")
        )
        aircraft_json = os.path.join(base_dir, "selected_aircraft.json")
        airport_json = os.path.join(base_dir, "selected_airports.json")

        # --- Avions sélectionnés
        self.aircraft_combo.clear()
        try:
            with open(aircraft_json, encoding="utf-8") as f:
                aircraft_list = json.load(f)
            if not aircraft_list:
                self.aircraft_combo.addItem("(No aircraft selected)")
            else:
                for ac in aircraft_list:
                    # Format affiché : F-GKXC | A320 | Air France
                    reg = ac.get("registration", "???")
                    model = ac.get("model", "???")
                    company = ac.get("company", "???")
                    label = f"{reg} | {model} | {company}"
                    self.aircraft_combo.addItem(label)
        except Exception as e:
            self.aircraft_combo.addItem("(No aircraft found)")
            print(f"[ERROR] Reading aircraft JSON: {e}")

        # --- Aéroports sélectionnés
        self.dep_combo.clear()
        self.arr_combo.clear()
        airport_names = []
        try:
            with open(airport_json, encoding="utf-8") as f:
                airport_list = json.load(f)
            if not airport_list:
                self.dep_combo.addItem("(No airport selected)")
                self.arr_combo.addItem("(No airport selected)")
            else:
                for ap in airport_list:
                    icao = ap.get("icao", "????")
                    name = ap.get("name", "")
                    label = f"{icao} - {name}" if name else icao
                    airport_names.append(label)
                    self.dep_combo.addItem(label)
                    self.arr_combo.addItem(label)
        except Exception as e:
            self.dep_combo.addItem("(No airports found)")
            self.arr_combo.addItem("(No airports found)")
            print(f"[ERROR] Reading airport JSON: {e}")

        # --- Airlines
        self.company_combo.clear()
        companies = set()
        try:
            with open(aircraft_json, encoding="utf-8") as f:
                aircraft_list = json.load(f)
            for ac in aircraft_list:
                company = ac.get("company", "").strip()
                if company:
                    companies.add(company)
            if companies:
                self.company_combo.addItem("All airlines")
                for c in sorted(companies):
                    self.company_combo.addItem(c)
            else:
                self.company_combo.addItem("(No airline)")
        except Exception:
            self.company_combo.addItem("(No airline)")

    def sync_company_from_aircraft(self):
        # Si l'utilisateur choisit un avion, synchronise la compagnie
        idx = self.aircraft_combo.currentIndex()
        if idx >= 0:
            label = self.aircraft_combo.currentText()
            # Ex : "F-HBNK | A320 | Air France"
            if "|" in label:
                parts = [x.strip() for x in label.split("|")]
                if len(parts) == 3:
                    company = parts[2]
                    # Met à jour la combo si ce n'est pas "All airlines"
                    idx_company = self.company_combo.findText(company)
                    if idx_company >= 0:
                        self.company_combo.setCurrentIndex(idx_company)

    def search_real_flights(self):
        # TODO: Intégrer la vraie logique FR24 mock + filtrage sur le pool sélectionné
        self.flights_list.clear()
        # Dummy result list
        self.flights_list.addItem("AF1234 | LFPO → LFMN | Dep 08:30 | Arr 09:55")
        self.flights_list.addItem("EZY8876 | LFPO → LFMN | Dep 10:40 | Arr 12:10")
        self.flights_list.addItem("VY5022 | LFMN → LFPO | Dep 13:05 | Arr 14:45")
        # Message box de debug, à retirer plus tard
        QMessageBox.information(
            self, "Results", "Dummy flight results populated. Replace with real data."
        )


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
        title = QLabel("SIMROSTER")
        title.setStyleSheet(
            "font-size: 24px; font-weight: bold; color: #ffffff; padding: 24px 8px 24px 16px; letter-spacing: 2px;"
        )
        nav_layout.addWidget(title, alignment=Qt.AlignTop)

        self.btn_dashboard = QPushButton("Dashboard")
        self.btn_fleetmanager = QPushButton("Fleet Manager")
        self.btn_flightplanning = QPushButton("Flight Planning")
        self.btn_settings = QPushButton("Settings")
        self.btn_quit = QPushButton("Quit")
        for btn in [
            self.btn_dashboard,
            self.btn_fleetmanager,
            self.btn_flightplanning,
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

        # --- BRIDGE UNIQUE POUR LA CARTE (DYNAMIQUE) ---
        import json

        airport_scanresults_path = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__), "../../results/airport_scanresults.json"
            )
        )
        selected_airports_path = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__), "../../results/selected_airports.json"
            )
        )

        def get_airports_live():
            try:
                with open(airport_scanresults_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return data
            except Exception as e:
                print("[DEBUG] get_airports_live() : erreur :", e)
                return []

        def get_selected_icaos_live():
            try:
                with open(selected_airports_path, "r", encoding="utf-8") as f:
                    icaos = [a["icao"] for a in json.load(f)]
                return icaos
            except Exception as e:
                print("[DEBUG] get_selected_icaos_live() : erreur :", e)
                return []

        self.bridge = AirportDataBridge(get_airports_live, get_selected_icaos_live)
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
        dashboard_title = QLabel("DASHBOARD")
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
        flight_planning_panel = FlightPlanningPanel(self)
        self.overlay_stack.addWidget(flight_planning_panel)
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
        self.btn_flightplanning.clicked.connect(lambda: self.set_panel(2))
        self.btn_settings.clicked.connect(lambda: self.set_panel(3))
        self.btn_quit.clicked.connect(self.close)

        self.set_panel(0)


    def set_panel(self, index):
        for btn, idx in zip(
            [
                self.btn_dashboard,
                self.btn_fleetmanager,
                self.btn_flightplanning,
                self.btn_settings,
            ],
            [0, 1, 2, 3],
        ):
            btn.setChecked(idx == index)
        self.overlay_stack.setCurrentIndex(index)

        # === Refresh dynamique du Flight Planning Panel ===
        if index == 2:  # 2 = Flight Planning (selon l’ordre d’ajout dans overlay_stack)
            panel = self.overlay_stack.widget(2)
            if hasattr(panel, "refresh_panel"):
                panel.refresh_panel()

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
