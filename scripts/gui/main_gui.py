import sys
import os
import csv
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
)
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QFont
from PyQt5.QtWebEngineWidgets import QWebEngineView


# ==================== FleetManagerPanel ====================
class FleetManagerPanel(QWidget):

    def __init__(
        self,
        available_aircraft=None,
        selected_aircraft=None,
        available_airports=None,
        selected_airports=None,
        parent=None,
    ):
        super().__init__(parent)
        self.available_aircraft = available_aircraft or []
        self.selected_aircraft = selected_aircraft or []
        self.available_airports = available_airports or []
        self.selected_airports = selected_airports or []

        self.setStyleSheet(
            """
            background: #fff;
            border-radius: 0px;
        """
        )

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(22, 22, 22, 18)
        main_layout.setSpacing(12)

        # Titre Fleet Manager
        title = QLabel("Fleet Manager")
        title.setStyleSheet(
            """
            font-size: 22px;
            font-weight: 600;
            color: #ffffff;
            background: none;
            """
        )
        title.setAlignment(Qt.AlignCenter)
        main_layout.addSpacing(-10)
        main_layout.addWidget(title)
        main_layout.addSpacing(50)

        # Bouton Scan Now sous le titre
        self.btn_scan = QPushButton("Scan Now")
        self.btn_scan.setStyleSheet(
            """
            background: #8d9099;
            color: #212226;
            border-radius: 0px;
            font-weight: bold;
            font-size: 15px;
            padding: 8px 22px;
            margin-bottom: 10px;
        """
        )
        main_layout.addWidget(self.btn_scan, alignment=Qt.AlignHCenter)

        # --- Aircraft section ---
        lbl_aircraft_avail = QLabel("Available Aircraft")
        lbl_aircraft_avail.setStyleSheet(
            "font-size: 15px; color: #fff; background: none; font-weight: bold;"
        )
        lbl_aircraft_avail.setContentsMargins(0, 10, 0, 0)
        main_layout.addWidget(lbl_aircraft_avail)

        # === Champ de recherche Aircraft stylisé, avec loupe blanche PNG et fond gris ===
        self.aircraft_search = QLineEdit()
        self.aircraft_search.setPlaceholderText("Search Aircraft...")

        self.aircraft_search.setStyleSheet(
            """
        QLineEdit {
            background-color: #343842;
            background-image: url(assets/search_white.png);
            background-repeat: no-repeat;
            background-position: 6px left center;
            color: #fff;
            font-size: 14px;
            padding-left: 32px;
            border-radius: 6px;
            border: 1px solid #444;
            margin-bottom: 8px;
            selection-background-color: #555;
        }
        QLineEdit:focus {
            border: 1.5px solid #bbb;
            outline: none;
        }
        QLineEdit::placeholder {
            color: #aaa;
        }
        """
        )

        main_layout.addWidget(self.aircraft_search)
        self.aircraft_search.textChanged.connect(self.filter_aircraft)

        self.list_aircraft_available = QListWidget()
        self.list_aircraft_available.setSelectionMode(QListWidget.MultiSelection)
        self.list_aircraft_available.setStyleSheet(
            "background: #343842; color: #fff; font-size: 14px; border: none; border-radius: 0;"
        )
        main_layout.addWidget(self.list_aircraft_available)

        aircraft_btns_layout = QHBoxLayout()
        self.btn_aircraft_add = QPushButton("↓ Add Aircraft")
        self.btn_aircraft_remove = QPushButton("↑ Remove Aircraft")
        for b in [self.btn_aircraft_add, self.btn_aircraft_remove]:
            b.setStyleSheet(
                """
                background: #8d9099;
                color: #222;
                border: none;
                border-radius: 0px;
                font-weight: 600;
                padding: 8px 10px;
                font-size: 13px;
            """
            )
        aircraft_btns_layout.addWidget(self.btn_aircraft_add)
        aircraft_btns_layout.addWidget(self.btn_aircraft_remove)
        main_layout.addLayout(aircraft_btns_layout)

        lbl_aircraft_sel = QLabel("Selected Aircraft")
        lbl_aircraft_sel.setStyleSheet(
            "font-size: 15px; color: #fff; background: none; font-weight: bold;"
        )
        main_layout.addWidget(lbl_aircraft_sel)

        self.list_aircraft_selected = QListWidget()
        self.list_aircraft_selected.setSelectionMode(QListWidget.MultiSelection)
        self.list_aircraft_selected.setStyleSheet(
            "background: #343842; color: #fff; font-size: 14px; border: none; border-radius: 0;"
        )
        main_layout.addWidget(self.list_aircraft_selected)

        # --- Airport section ---
        lbl_airport_avail = QLabel("Available Airports")
        lbl_airport_avail.setStyleSheet(
            "font-size: 15px; color: #fff; background: none; font-weight: bold;"
        )
        main_layout.addWidget(lbl_airport_avail)

        # === Champ de recherche aéroports ===
        self.airport_search = QLineEdit()
        self.airport_search.setPlaceholderText("Search ICAO or name...")

        loupe_svg = (
            "data:image/svg+xml;utf8,"
            "<svg width='16' height='16' viewBox='0 0 20 20' xmlns='http://www.w3.org/2000/svg'>"
            "<circle cx='9' cy='9' r='7' stroke='white' stroke-width='2' fill='none'/>"
            "<line x1='15' y1='15' x2='12.5' y2='12.5' stroke='white' stroke-width='2'/>"
            "</svg>"
        )

        self.airport_search.setStyleSheet(
            f"""
        QLineEdit {{
            background-color: #343842;
            background-image: url(assets/search_white.png);
            background-repeat: no-repeat;
            background-position: left center;
            color: #fff;
            font-size: 14px;
            padding-left: 32px;
            border-radius: 6px;
            border: 1px solid #444;
            margin-bottom: 8px;
            selection-background-color: #555;
        }}
        QLineEdit:focus {{
            border: 1.5px solid #bbb;
            outline: none;
        }}
        QLineEdit::placeholder {{
            color: #aaa;
        }}
        """
        )

        main_layout.addWidget(self.airport_search)
        self.airport_search.textChanged.connect(self.filter_airports)

        self.list_airport_available = QListWidget()
        self.list_airport_available.setSelectionMode(QListWidget.MultiSelection)
        self.list_airport_available.setStyleSheet(
            "background: #343842; color: #fff; font-size: 14px; border: none; border-radius: 0;"
        )
        main_layout.addWidget(self.list_airport_available)

        airport_btns_layout = QHBoxLayout()
        self.btn_airport_add = QPushButton("↓ Add Airport")
        self.btn_airport_remove = QPushButton("↑ Remove Airport")
        for b in [self.btn_airport_add, self.btn_airport_remove]:
            b.setStyleSheet(
                """
                background: #8d9099;
                color: #222;
                border: none;
                border-radius: 0px;
                font-weight: 600;
                padding: 8px 10px;
                font-size: 13px;
            """
            )
        airport_btns_layout.addWidget(self.btn_airport_add)
        airport_btns_layout.addWidget(self.btn_airport_remove)
        main_layout.addLayout(airport_btns_layout)

        lbl_airport_sel = QLabel("Selected Airports")
        lbl_airport_sel.setStyleSheet(
            "font-size: 15px; color: #fff; background: none; font-weight: bold;"
        )
        main_layout.addWidget(lbl_airport_sel)

        self.list_airport_selected = QListWidget()
        self.list_airport_selected.setSelectionMode(QListWidget.MultiSelection)
        self.list_airport_selected.setStyleSheet(
            "background: #343842; color: #fff; font-size: 14px; border: none; border-radius: 0;"
        )
        main_layout.addWidget(self.list_airport_selected)

        # --- Reset bouton ---
        self.btn_reset = QPushButton("Reset All")
        self.btn_reset.setStyleSheet(
            "margin-top: 14px; padding: 9px 26px; background: #8d9099; color: #222; border: none; border-radius: 0px; font-weight: bold;"
        )
        main_layout.addWidget(self.btn_reset, alignment=Qt.AlignCenter)

        # --- Connexions boutons
        self.btn_aircraft_add.clicked.connect(self.add_aircraft)
        self.btn_aircraft_remove.clicked.connect(self.remove_aircraft)
        self.btn_airport_add.clicked.connect(self.add_airport)
        self.btn_airport_remove.clicked.connect(self.remove_airport)
        self.btn_reset.clicked.connect(self.reset_all)
        self.btn_scan.clicked.connect(self.scan_airports)

        # --- Affichage initial ---
        self._refresh_aircraft_list()
        self._refresh_selected_aircraft_list()
        self._refresh_airport_list()
        self._refresh_selected_airport_list()

    # === Aircraft list helpers ===

    def _refresh_aircraft_list(self):
        self.list_aircraft_available.clear()
        for ac in self.available_aircraft:
            item = QListWidgetItem(f"{ac['reg']} – {ac['model']}")
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            item.setCheckState(Qt.Unchecked)
            self.list_aircraft_available.addItem(item)

    def _refresh_selected_aircraft_list(self):
        self.list_aircraft_selected.clear()
        for ac in self.selected_aircraft:
            item = QListWidgetItem(f"{ac['reg']} – {ac['model']}")
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            item.setCheckState(Qt.Unchecked)
            self.list_aircraft_selected.addItem(item)
    # === Airport list helpers ===

    def _refresh_airport_list(self):
        self.list_airport_available.clear()
        for ap in self.available_airports:
            item = QListWidgetItem(f"{ap['icao']} – {ap['name']}")
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            item.setCheckState(Qt.Unchecked)
            self.list_airport_available.addItem(item)

    def _refresh_selected_airport_list(self):
        self.list_airport_selected.clear()
        for ap in self.selected_airports:
            item = QListWidgetItem(f"{ap['icao']} – {ap['name']}")
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            item.setCheckState(Qt.Unchecked)
            self.list_airport_selected.addItem(item)

    # === Fonctions de déplacement
    def add_aircraft(self):
        to_move = []
        for i in range(self.list_aircraft_available.count()):
            item = self.list_aircraft_available.item(i)
            # Tickbox uniquement (checkstate) pour Aircraft
            if (
                item.flags() & Qt.ItemIsUserCheckable
                and item.checkState() == Qt.Checked
            ):
                ac_text = item.text()
                ac = next(
                    (
                        a
                        for a in self.available_aircraft
                        if f"{a['reg']} – {a['model']}" == ac_text
                    ),
                    None,
                )
                if ac:
                    self.selected_aircraft.append(ac)
                    to_move.append(ac)
        for ac in to_move:
            self.available_aircraft.remove(ac)
        self._refresh_aircraft_list()
        self._refresh_selected_aircraft_list()

    def remove_aircraft(self):
        to_move = []
        for i in range(self.list_aircraft_selected.count()):
            item = self.list_aircraft_selected.item(i)
            # Tickbox uniquement pour Aircraft sélectionnés
            if (
                item.flags() & Qt.ItemIsUserCheckable
                and item.checkState() == Qt.Checked
            ):
                ac_text = item.text()
                ac = next(
                    (
                        a
                        for a in self.selected_aircraft
                        if f"{a['reg']} – {a['model']}" == ac_text
                    ),
                    None,
                )
                if ac:
                    self.available_aircraft.append(ac)
                    to_move.append(ac)
        for ac in to_move:
            self.selected_aircraft.remove(ac)
        self._refresh_aircraft_list()
        self._refresh_selected_aircraft_list()

    def add_airport(self):
        to_move = []
        for i in range(self.list_airport_available.count()):
            item = self.list_airport_available.item(i)
            # Tickbox uniquement (checkstate)
            if (
                item.flags() & Qt.ItemIsUserCheckable
                and item.checkState() == Qt.Checked
            ):
                text = item.text()
                ap = next(
                    (
                        a
                        for a in self.available_airports
                        if f"{a['icao']} – {a['name']}" == text
                    ),
                    None,
                )
                if ap:
                    self.selected_airports.append(ap)
                    to_move.append(ap)
        for ap in to_move:
            self.available_airports.remove(ap)
        self._refresh_airport_list()
        self._refresh_selected_airport_list()

    def remove_airport(self):
        to_move = []
        for i in range(self.list_airport_selected.count()):
            item = self.list_airport_selected.item(i)
            # Tickbox uniquement (checkstate)
            if item.flags() & Qt.ItemIsUserCheckable and item.checkState() == Qt.Checked:
                text = item.text()
                ap = next(
                    (a for a in self.selected_airports if f"{a['icao']} – {a['name']}" == text),
                    None,
                )
                if ap:
                    self.available_airports.append(ap)
                    to_move.append(ap)
        for ap in to_move:
            self.selected_airports.remove(ap)
        self._refresh_airport_list()
        self._refresh_selected_airport_list()

    def reset_all(self):
        self.available_aircraft += self.selected_aircraft
        self.selected_aircraft = []
        self.available_airports += self.selected_airports
        self.selected_airports = []
        self._refresh_aircraft_list()
        self._refresh_selected_aircraft_list()
        self._refresh_airport_list()
        self._refresh_selected_airport_list()

    # === SCAN depuis le CSV (airports.csv dans "data/") ===
    def scan_airports(self):
        airports = []
        path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../data/airports.csv")
        )
        try:
            with open(path, encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get("icao", "") and row.get("name", ""):
                        airports.append({"icao": row["icao"], "name": row["name"]})
        except Exception as e:
            print("Erreur chargement CSV aéroports :", e)
            airports = []

        self.available_airports = airports
        self.selected_airports = []
        self._refresh_airport_list()
        self._refresh_selected_airport_list()
        print(f"[INFO] {len(airports)} aéroports chargés depuis {path}")

    # === FILTRE DE RECHERCHE (Search) ===
    def filter_airports(self, text):
        self.list_airport_available.clear()
        if not text.strip():
            for ap in self.available_airports:
                self.list_airport_available.addItem(f"{ap['icao']} – {ap['name']}")
        else:
            txt = text.lower().strip()
            for ap in self.available_airports:
                if txt in ap["icao"].lower() or txt in ap["name"].lower():
                    self.list_airport_available.addItem(f"{ap['icao']} – {ap['name']}")

    def filter_aircraft(self, text):
        self.list_aircraft_available.clear()
        if not text.strip():
            for ac in self.available_aircraft:
                item = QListWidgetItem(f"{ac['reg']} – {ac['model']}")
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                item.setCheckState(Qt.Unchecked)
                self.list_aircraft_available.addItem(item)
        else:
            txt = text.lower().strip()
            for ac in self.available_aircraft:
                if txt in ac["reg"].lower() or txt in ac["model"].lower():
                    item = QListWidgetItem(f"{ac['reg']} – {ac['model']}")
                    item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                    item.setCheckState(Qt.Unchecked)
                    self.list_aircraft_available.addItem(item)

            # Aircraft
            all_sel_ac = []
            while self.list_aircraft_selected.count():
                all_sel_ac.append(self.list_aircraft_selected.takeItem(0).text())
            self.list_aircraft_available.addItems(all_sel_ac)
            # Airports
            all_sel_ap = []
            while self.list_airport_selected.count():
                all_sel_ap.append(self.list_airport_selected.takeItem(0).text())
            self.list_airport_available.addItems(all_sel_ap)


# ==================== MAIN WINDOW ====================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SimRoster")
        self.resize(1440, 900)
        self.showMaximized()  # Plein écran au lancement

        # === Sidebar (gauche) ===
        nav_widget = QWidget()
        nav_layout = QVBoxLayout(nav_widget)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(0)
        nav_widget.setStyleSheet("background: #181818;")

        # Logo ou nom appli
        title = QLabel("SimRoster")
        title.setStyleSheet(
            "font-size: 24px; font-weight: bold; color: #ffffff; padding: 24px 8px 24px 16px; letter-spacing: 2px;"
        )
        nav_layout.addWidget(title, alignment=Qt.AlignTop)

        # Boutons de navigation
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

        # === Zone centrale (QStackedWidget) ===
        self.central_stack = QStackedWidget()

        # ================= DASHBOARD : Carte interactive plein écran =================
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
        # ================= END DASHBOARD ============================================

        # =================== FLEET MANAGER : Panel vertical à gauche + carte ===================
        fleet_panel_container = QWidget()
        fleet_panel_layout = QHBoxLayout(fleet_panel_container)
        fleet_panel_layout.setContentsMargins(0, 0, 0, 0)
        fleet_panel_layout.setSpacing(0)

        # -- Panel vertical gauche, 46% largeur, carré, fond blanc
        fleet_panel_widget = QWidget()
        fleet_panel_widget.setFixedWidth(int(self.width() * 0.46))  # 46% de la fenêtre
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

        # -- FleetManagerPanel avec Scan Now en haut --

        def load_airports_from_csv():
            airports = []
            path = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "../../data/airports.csv")
            )
            print(f"[DEBUG] CSV path: {path}")
            print("[DEBUG] CSV exists?", os.path.exists(path))
            try:
                with open(path, encoding="utf-8-sig") as f:   # <--- LA différence CLEF
                    lines = f.readlines()
                    print(f"[DEBUG] Nb lignes dans CSV: {len(lines)}")
                    f.seek(0)
                    reader = csv.DictReader(lines)
                    for row in reader:
                        print("[DEBUG] Première ligne CSV:", row)
                        if row.get("icao", "") and row.get("name", ""):
                            airports.append({"icao": row["icao"], "name": row["name"]})
            except Exception as e:
                print("Erreur chargement CSV aéroports (init FleetManager):", e)
            return airports

        def load_aircraft_sample():
            # Remplace par ton scan réel d'avions dès que prêt !
            return [
                {"reg": "F-HBJB", "model": "A320neo Air France"},
                {"reg": "D-AIZC", "model": "A320 Lufthansa"},
            ]

        aircraft_init = load_aircraft_sample()
        airports_init = load_airports_from_csv()
        fleet_manager_core = FleetManagerPanel(
            available_aircraft=aircraft_init,
            selected_aircraft=[],
            available_airports=airports_init,
            selected_airports=[],
        )

        vbox.addWidget(fleet_manager_core)
        vbox.addStretch(1)


        # -- Carte à droite du panel --
        fleet_map_view = QWebEngineView()
        fleet_map_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../results/map.html")
        )
        fleet_map_view.load(QUrl.fromLocalFile(fleet_map_path))
        fleet_map_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        fleet_panel_layout.addWidget(fleet_panel_widget)
        fleet_panel_layout.addWidget(fleet_map_view)

        self.central_stack.addWidget(fleet_panel_container)
        # ================= END FLEET MANAGER =========================================

        # ================= SETTINGS PANEL =====================
        settings_panel = QWidget()
        settings_layout = QVBoxLayout(settings_panel)
        settings_label = QLabel("Settings (à venir)")
        settings_label.setStyleSheet("font-size: 24px; color: #bbb;")
        settings_layout.addWidget(settings_label, alignment=Qt.AlignCenter)
        self.central_stack.addWidget(settings_panel)
        # ================= END SETTINGS =======================

        # === Layout principal ===
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(nav_widget)
        main_layout.addWidget(self.central_stack)
        self.setCentralWidget(main_widget)

        # === Connexions navigation ===
        self.btn_dashboard.clicked.connect(
            lambda: self.central_stack.setCurrentIndex(0)
        )
        self.btn_fleetmanager.clicked.connect(
            lambda: self.central_stack.setCurrentIndex(1)
        )
        self.btn_settings.clicked.connect(lambda: self.central_stack.setCurrentIndex(2))
        self.btn_quit.clicked.connect(self.close)

        # Dashboard par défaut
        self.btn_dashboard.setChecked(True)
        self.central_stack.setCurrentIndex(0)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    font = QFont("Roboto", 12)
    app.setFont(font)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
