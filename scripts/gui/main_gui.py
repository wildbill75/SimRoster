import sys
import os
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu"
import json
import webbrowser
# import qt_material

from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QCheckBox,
    QScrollArea,
    QGroupBox,
    QMessageBox,
    QSizePolicy,
    QFormLayout,
    QStyle,
 
)
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtWebEngineWidgets import QWebEngineView

# === Chemins (à adapter si besoin) ===
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RESULTS_DIR = os.path.join(BASE_DIR, "results")
DATA_DIR = os.path.join(BASE_DIR, "scripts", "data")
MAP_DIR = os.path.join(BASE_DIR, "map")
MAP_HTML_PATH = os.path.join(MAP_DIR, "map.html")

try:
    from scripts.utils.i18n import Translator
except ImportError:
    from ..utils.i18n import Translator

try:
    from scripts.utils.generate_map import (
        generate_airports_map_data,
        generate_airports_map_html,
    )
except ImportError:
    from ..utils.generate_map import (
        generate_airports_map_data,
        generate_airports_map_html,
    )

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.translator = Translator("en")
        self.setWindowTitle(self.translator.t("main_window_title"))
        self.setGeometry(100, 100, 1200, 800)

        # CHEMINS (ajoute ces lignes pour avoir accès partout dans la classe)
        self.base_dir = BASE_DIR
        self.results_dir = RESULTS_DIR
        self.data_dir = DATA_DIR
        self.map_dir = MAP_DIR
        ...

        # Sélecteur de langue
        self.language_selector = QComboBox()
        self.language_selector.addItem("English", "en")
        self.language_selector.addItem("Français", "fr")
        self.language_selector.addItem("Deutsch", "de")
        self.language_selector.addItem("Español", "es")
        self.language_selector.setCurrentIndex(0)
        self.language_selector.currentIndexChanged.connect(
            lambda _: self.change_language(self.language_selector.currentData())
        )

        # --- Barre de navigation ---
        nav_bar = QHBoxLayout()
        self.btn_dashboard = QPushButton("Dashboard")
        self.btn_fleet = QPushButton("Fleet & Airports")
        self.btn_setup = QPushButton("Flight Setup")
        self.btn_ops = QPushButton("Flight Ops")
        self.btn_settings = QPushButton("Settings")
        self.btn_profile = QPushButton("Profile")
        self.btn_devbuild = QPushButton("DevBuild")

        self.menu_buttons = [
            self.btn_dashboard,
            self.btn_fleet,
            self.btn_setup,
            self.btn_ops,
            self.btn_settings,
            self.btn_profile,
            self.btn_devbuild,
        ]
        for btn in self.menu_buttons:
            btn.setCheckable(True)
            btn.setStyleSheet("padding:10px 18px; font-size:1em;")
            nav_bar.addWidget(btn)
        nav_bar.addStretch()

        nav_bar_widget = QWidget()
        nav_bar_widget.setLayout(nav_bar)
        nav_bar_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # --- Carte centrale ---
        self.map_view = QWebEngineView()
        self.map_view.setMinimumHeight(500)
        self.refresh_map()

        # --- Panels contextuels ---
        self.panels = [
            self.build_dashboard_panel(),
            self.build_fleet_panel(),
            None, # Flight Setup overlay géré à part
            self.build_flightops_panel(),
            self.build_settings_panel(),
            self.build_profile_panel(),
            self.build_devbuild_panel(),
        ]

        # --- Layout principal ---
        self.main_layout = QVBoxLayout()
        self.main_layout.addWidget(self.language_selector)
        self.main_layout.addWidget(nav_bar_widget)
        self.main_layout.addWidget(self.map_view, stretch=10)
        # Pas d'ajout du context_panel ici : voir switch_panel()

        self.panel_container = QWidget()
        self.panel_layout = QVBoxLayout(self.panel_container)
        self.panel_layout.setContentsMargins(0, 0, 0, 0)
        self.panel_layout.setSpacing(0)
        self.panel_layout.addWidget(self.panels[0])  # Par défaut, dashboard (invisible)

        self.central = QWidget()
        self.central.setLayout(self.main_layout)
        self.setCentralWidget(self.central)

        self.flightsetup_overlay = self.build_flightsetup_panel()  # Panel overlay flottant
        self.flightsetup_overlay.setVisible(False)
        self.flightsetup_overlay.setParent(self.central)  # parent = central widget pour overlay

        self.dashboard_overlay = self.build_dashboard_panel()
        self.dashboard_overlay.setVisible(False)
        self.dashboard_overlay.setParent(self.central)

        self.fleet_overlay = self.build_fleet_panel()
        self.fleet_overlay.setVisible(False)
        self.fleet_overlay.setParent(self.central)

        self.airport_overlay = self.build_airport_panel()
        self.airport_overlay.setVisible(False)
        self.airport_overlay.setParent(self.central)

        self.flightops_overlay = self.build_flightops_panel()
        self.flightops_overlay.setVisible(False)
        self.flightops_overlay.setParent(self.central)

        self.settings_overlay = self.build_settings_panel()
        self.settings_overlay.setVisible(False)
        self.settings_overlay.setParent(self.central)

        self.profile_overlay = self.build_profile_panel()
        self.profile_overlay.setVisible(False)
        self.profile_overlay.setParent(self.central)

        self.devbuild_overlay = self.build_devbuild_panel()
        self.devbuild_overlay.setVisible(False)
        self.devbuild_overlay.setParent(self.central)

        # --- Connexions des boutons ---
        self.btn_dashboard.clicked.connect(lambda: self.switch_panel(0))
        self.btn_fleet.clicked.connect(lambda: self.switch_panel(1))
        self.btn_setup.clicked.connect(lambda: self.switch_panel(2))
        self.btn_ops.clicked.connect(lambda: self.switch_panel(3))
        self.btn_settings.clicked.connect(lambda: self.switch_panel(4))
        self.btn_profile.clicked.connect(lambda: self.switch_panel(5))
        self.btn_devbuild.clicked.connect(lambda: self.switch_panel(6))

        self.btn_dashboard.setChecked(True)
        self.switch_panel(0)

    def switch_panel(self, idx):
        # Masque tous les overlays
        overlays = [
            self.dashboard_overlay,
            self.fleet_overlay,
            self.flightsetup_overlay,
            self.flightops_overlay,
            self.settings_overlay,
            self.profile_overlay,
            self.devbuild_overlay,
            self.airport_overlay,
        ]
        for panel in overlays:
            panel.setVisible(False)

        # Retire le panel classique du layout s'il est là
        if self.main_layout.indexOf(self.panel_container) != -1:
            self.main_layout.removeWidget(self.panel_container)
            self.panel_container.setParent(None)

        # Affiche l'overlay correspondant à l'onglet actif (par convention, même ordre que tes boutons)
        if 0 <= idx < len(overlays):
            self.position_overlay(overlays[idx])
            overlays[idx].setVisible(True)

        # Met à jour l'état visuel des boutons
        for i, btn in enumerate(self.menu_buttons):
            btn.setChecked(i == idx)

    def build_dashboard_panel(self):
        panel = QWidget()
        panel.setMinimumHeight(320)
        panel.setMaximumWidth(520)
        panel.setStyleSheet("""
            background: #fff;
            border-radius: 18px;
            border: 1.5px solid #dde;
        """)
        layout = QVBoxLayout(panel)
        label = QLabel("Dashboard panel (à remplir)")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 18px; color: #3b4252; margin-top: 80px;")
        layout.addWidget(label)
        return panel

    def build_fleet_panel(self):
        panel = QWidget()
        panel.setMinimumHeight(320)
        panel.setMaximumWidth(520)
        panel.setStyleSheet("""
            background: #fff;
            border-radius: 18px;
            border: 1.5px solid #dde;
        """)
        layout = QVBoxLayout(panel)
        label = QLabel("Fleet panel (à remplir)")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 18px; color: #3b4252; margin-top: 80px;")
        layout.addWidget(label)

        aircraft_group = QGroupBox("Detected Aircraft")
        aircraft_layout = QVBoxLayout()
        self.scroll_aircraft = QScrollArea()
        self.scroll_aircraft.setWidgetResizable(True)
        self.container_aircraft = QWidget()
        self.container_aircraft.setLayout(aircraft_layout)
        self.scroll_aircraft.setWidget(self.container_aircraft)
        aircraft_group.setLayout(QVBoxLayout())
        aircraft_group.layout().addWidget(self.scroll_aircraft)

        airport_group = QGroupBox("Detected Airports")
        airport_layout = QVBoxLayout()
        self.scroll_airport = QScrollArea()
        self.scroll_airport.setWidgetResizable(True)
        self.container_airport = QWidget()
        self.container_airport.setLayout(airport_layout)
        self.scroll_airport.setWidget(self.container_airport)
        airport_group.setLayout(QVBoxLayout())
        airport_group.layout().addWidget(self.scroll_airport)

        btn_save_aircraft = QPushButton("Save selected aircraft")
        btn_save_airports = QPushButton("Save selected airports")
        btn_save_aircraft.clicked.connect(self.save_aircraft_selection)
        btn_save_airports.clicked.connect(self.save_airport_selection)

        layout.addWidget(aircraft_group)
        layout.addWidget(btn_save_aircraft)
        layout.addSpacing(20)
        layout.addWidget(airport_group)
        layout.addWidget(btn_save_airports)

        panel.setLayout(layout)
        # Chargement initial
        self.load_aircraft_list()
        self.load_airport_list()
        return panel

    def build_flightsetup_panel(self):
        # --- PANEL CENTRAL (overlay, pas dans layout !) ---
        panel = QWidget()
        panel.setMinimumHeight(370)
        panel.setMaximumWidth(720)
        panel.setStyleSheet("""
            background: #fff;
            border-radius: 22px;
            border: 1.5px solid #dde;
            box-shadow: 0 8px 40px 0 rgba(80,90,110,0.10);
        """)

        form_layout = QFormLayout(panel)
        form_layout.setContentsMargins(42, 38, 42, 34)
        form_layout.setSpacing(18)

        btn_reload = QPushButton("Reload aircraft/airport selection")
        btn_reload.setFixedWidth(400)
        btn_reload.setStyleSheet("""
            QPushButton {
                background-color: #f4f6fa;
                border: 1.3px solid #a8b6c8;
                border-radius: 7px;
                padding: 8px 20px;
                font-size: 15px;
                font-weight: 500;
                color: #4a5568;
            }
            QPushButton:hover {
                background-color: #e7f1ff;
                border-color: #406fd1;
                color: #223466;
            }
            QPushButton:pressed {
                background-color: #d7e9ff;
                border-color: #2856a1;
                color: #1a2332;
            }
        """)
        btn_reload.clicked.connect(self.load_selected_data)

        self.combo_departure = QComboBox()
        self.combo_arrival = QComboBox()
        self.combo_aircraft = QComboBox()

        for combo in [self.combo_departure, self.combo_arrival, self.combo_aircraft]:
            combo.setMinimumWidth(420)
            combo.setMaximumWidth(660)

        label_style = "color: #233; font-size: 13px; font-weight:500; min-width:120px;"

        lbl_departure = QLabel("Departure airport")
        lbl_departure.setStyleSheet(label_style)
        lbl_arrival = QLabel("Arrival airport")
        lbl_arrival.setStyleSheet(label_style)
        lbl_aircraft = QLabel("Aircraft used")
        lbl_aircraft.setStyleSheet(label_style)

        self.label_summary = QLabel("Flight summary")
        self.label_summary.setStyleSheet("""
            background: #f4f6fa;
            border: 1.3px solid #a8b6c8;
            border-radius: 8px;   /* <- beaucoup moins arrondi */
            padding: 10px 18px;
            margin-top: 8px;
            color: #444;
            font-size: 12px;
        """)

        btn_save = QPushButton("Save flight plan")
        btn_save.setFixedWidth(220)
        btn_save.setStyleSheet(btn_reload.styleSheet())
        btn_save.clicked.connect(self.save_flightplan)

        form_layout.addRow("", btn_reload)
        form_layout.addRow(lbl_departure, self.combo_departure)
        form_layout.addRow(lbl_arrival, self.combo_arrival)
        form_layout.addRow(lbl_aircraft, self.combo_aircraft)
        form_layout.addRow("", btn_save)
        form_layout.addRow("", self.label_summary)

        # --- Chargement initial & connexions ---
        self.load_selected_data()
        self.combo_departure.currentIndexChanged.connect(self.update_summary)
        self.combo_arrival.currentIndexChanged.connect(self.update_summary)
        self.combo_aircraft.currentIndexChanged.connect(self.update_summary)

        return panel

    def build_flightops_panel(self):
        panel = QWidget()
        panel.setMinimumHeight(320)
        panel.setMaximumWidth(520)
        panel.setStyleSheet(
            """
            background: #fff;
            border-radius: 18px;
            border: 1.5px solid #dde;
        """
        )
        layout = QVBoxLayout(panel)
        label = QLabel("Flight Ops panel (à remplir)")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 18px; color: #3b4252; margin-top: 80px;")
        layout.addWidget(label)

        # Exemple de bouton à titre de placeholder
        btn_save = QPushButton("Save this flight (placeholder)")
        # Ne connecte rien pour l’instant (tu pourras ajouter la connexion plus tard)
        layout.addWidget(btn_save)

        # Placeholder ComboBox, non connecté (à compléter plus tard si besoin)
        self.combo_realflights = QComboBox()
        self.combo_realflights.addItem("No real flights available yet")
        layout.addWidget(self.combo_realflights)
        # Pas de connexion .currentIndexChanged ici pour éviter les erreurs

        # Placeholder SimBrief (désactivé)
        self.btn_simbrief = QPushButton("Generate in SimBrief (placeholder)")
        self.btn_simbrief.setEnabled(False)
        layout.addWidget(self.btn_simbrief)

        panel.setLayout(layout)
        return panel

    def build_settings_panel(self):
        panel = QWidget()
        panel.setMinimumHeight(320)
        panel.setMaximumWidth(520)
        panel.setStyleSheet("""
            background: #fff;
            border-radius: 18px;
            border: 1.5px solid #dde;
    """)
        layout = QVBoxLayout(panel)
        label = QLabel("Settings panel (à remplir)")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 18px; color: #3b4252; margin-top: 80px;")
        layout.addWidget(label)

        lang_label = QLabel(self.translator.t("select_language"))
        self.lang_combo = QComboBox()
        self.lang_combo.addItem("English", "en")
        self.lang_combo.addItem("Français", "fr")
        self.lang_combo.addItem("Deutsch", "de")
        self.lang_combo.addItem("Español", "es")
        current_lang_index = self.lang_combo.findData(self.translator.language)
        if current_lang_index != -1:
            self.lang_combo.setCurrentIndex(current_lang_index)
        self.lang_combo.currentTextChanged.connect(self.on_language_selected)
        layout.addWidget(lang_label)
        layout.addWidget(self.lang_combo)
        panel.setLayout(layout)
        return panel

    def build_profile_panel(self):
        panel = QWidget()
        panel.setMinimumHeight(320)
        panel.setMaximumWidth(520)
        panel.setStyleSheet("""
            background: #fff;
            border-radius: 18px;
            border: 1.5px solid #dde;
    """)
        layout = QVBoxLayout(panel)
        label = QLabel("Profile panel (à remplir)")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 18px; color: #3b4252; margin-top: 80px;")
        layout.addWidget(label)
        return panel

    def build_devbuild_panel(self):
        panel = QWidget()
        panel.setMinimumHeight(320)
        panel.setMaximumWidth(520)
        panel.setStyleSheet("""
            background: #fff;
            border-radius: 18px;
            border: 1.5px solid #dde;
    """)
        layout = QVBoxLayout(panel)
        label = QLabel("DevBuild panel (à remplir)")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 18px; color: #3b4252; margin-top: 80px;")
        layout.addWidget(label)

        btn_generate_html = QPushButton("Regenerate map HTML")
        btn_generate_html.clicked.connect(generate_airports_map_html)
        layout.addWidget(btn_generate_html)
        layout.addStretch()
        panel.setLayout(layout)
        return panel

    def build_airport_panel(self):
        panel = QWidget()
        panel.setMinimumHeight(320)
        panel.setMaximumWidth(520)
        panel.setStyleSheet("""
            background: #fff;
            border-radius: 18px;
            border: 1.5px solid #dde;
        """)
        layout = QVBoxLayout(panel)
        label = QLabel("Airports panel (à remplir)")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 18px; color: #3b4252; margin-top: 80px;")
        layout.addWidget(label)
        return panel 
    # ---------- LOGIQUE METIER : inchangée ----------
    def refresh_map(self):
        map_path = os.path.abspath(os.path.join(self.map_dir, "map.html"))
        print("[DEBUG] refresh_map path:", map_path)
        self.map_view.load(QUrl.fromLocalFile(map_path))

    def refresh_fleet_panel(self):
        self.load_airport_list()
        self.load_aircraft_list()

    def load_aircraft_list(self):
        self.aircraft_checkboxes = []
        layout = self.container_aircraft.layout()
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        path = os.path.join(RESULTS_DIR, "aircraft_scanresults.json")
        try:
            with open(path, "r", encoding="utf-8") as f:
                self.aircraft_data = json.load(f)
            for aircraft in self.aircraft_data:
                label = f"{aircraft.get('model', 'Unknown')} - {aircraft.get('company', '')} ({aircraft.get('registration', '')})"
                cb = QCheckBox(label)
                cb.setChecked(True)
                self.aircraft_checkboxes.append(cb)
                layout.addWidget(cb)
        except Exception as e:
            print(f"[ERREUR] Chargement des avions : {e}")

    def load_airport_list(self):
        self.airport_checkboxes = []
        layout = self.container_airport.layout()
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        path = os.path.join(RESULTS_DIR, "airport_scanresults.json")
        try:
            with open(path, "r", encoding="utf-8") as f:
                self.airport_data = json.load(f)
            for airport in self.airport_data:
                label = f"{airport.get('icao', '???')} - {airport.get('name', 'Nom inconnu')}"
                cb = QCheckBox(label)
                cb.setChecked(True)
                self.airport_checkboxes.append(cb)
                layout.addWidget(cb)
        except Exception as e:
            print(f"[ERREUR] Chargement des aéroports : {e}")

    def save_aircraft_selection(self):
        selected = []
        for cb, data in zip(self.aircraft_checkboxes, self.aircraft_data):
            if cb.isChecked():
                selected.append(data)
        path = os.path.join(RESULTS_DIR, "selected_aircraft.json")
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(selected, f, indent=4, ensure_ascii=False)
            QMessageBox.information(self, "Success", f"{len(selected)} aircraft saved!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Aircraft save error: {e}")

    def save_airport_selection(self):
        selected = []
        for cb, data in zip(self.airport_checkboxes, self.airport_data):
            if cb.isChecked():
                selected.append(data)
        path = os.path.join(RESULTS_DIR, "selected_airports.json")
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(selected, f, indent=4, ensure_ascii=False)
            QMessageBox.information(self, "Success", f"{len(selected)} airports saved!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Airport save error: {e}")

    def load_selected_data(self):
        """Remplit les combos avec la sélection JSON, ou fallback test si vide."""
        self.selected_airports = []
        self.selected_aircraft = []
        ap_path = os.path.join(self.results_dir, "selected_airports.json")
        ac_path = os.path.join(self.results_dir, "selected_aircraft.json")

        # --- Chargement des JSON ---
        if os.path.exists(ap_path):
            with open(ap_path, "r", encoding="utf-8") as f:
                self.selected_airports = json.load(f)
        if os.path.exists(ac_path):
            with open(ac_path, "r", encoding="utf-8") as f:
                self.selected_aircraft = json.load(f)

        # --- Remplir les combos ---
        self.combo_departure.clear()
        self.combo_arrival.clear()
        self.combo_aircraft.clear()

        # Remplir seulement si data, sinon valeur test
        if self.selected_airports:
            for ap in self.selected_airports:
                label = f"{ap['icao']} | {ap['name']}"
                self.combo_departure.addItem(label, ap)
                self.combo_arrival.addItem(label, ap)
        else:
            self.combo_departure.addItem("No airport found")
            self.combo_arrival.addItem("No airport found")
        if self.selected_aircraft:
            for ac in self.selected_aircraft:
                label = f"{ac['model']} | {ac['company']} | {ac['registration']}"
                self.combo_aircraft.addItem(label, ac)
        else:
            self.combo_aircraft.addItem("No aircraft found")

        # DEBUG : affiche dans la console le résultat
        print("[DEBUG] load_selected_data :", 
            "airports:", self.combo_departure.count(), 
            "aircraft:", self.combo_aircraft.count())

        self.update_summary()

    def update_summary(self):
        if (
            self.combo_departure.count() < 1
            or self.combo_arrival.count() < 1
            or self.combo_aircraft.count() < 1
        ):
            self.label_summary.setText("Load at least 2 airports and 1 aircraft.")
            return

        dep = self.combo_departure.currentData()
        arr = self.combo_arrival.currentData()
        ac = self.combo_aircraft.currentData()

        if dep["icao"] == arr["icao"]:
            self.label_summary.setText("Departure and arrival must be different.")
            return

        # ------- Remplace ici la ligne suivante -------
        self.label_summary.setText(
            f"<span style='font-size:12px;'>"
            f"<b>Departure:</b> {dep['icao']} ({dep['name']})<br>"
            f"<b>Arrival:</b> {arr['icao']} ({arr['name']})<br>"
            f"<b>Aircraft:</b> {ac['model']} {ac['company']} ({ac['registration']})"
            f"</span>"
        )

    def save_flightplan(self):
        dep = self.combo_departure.currentData()
        arr = self.combo_arrival.currentData()
        ac = self.combo_aircraft.currentData()

        if dep["icao"] == arr["icao"]:
            QMessageBox.warning(
                self, "Error", "Departure and arrival must be different."
            )
            return

        plan = {"departure": dep, "arrival": arr, "aircraft": ac}
        outpath = os.path.join(RESULTS_DIR, "selected_flight_plan.json")
        with open(outpath, "w", encoding="utf-8") as f:
            json.dump(plan, f, indent=4, ensure_ascii=False)
        QMessageBox.information(self, "Plan saved", f"Saved to:\n{outpath}")

    def load_mock_flights(self):
        path = os.path.join(RESULTS_DIR, "mock_fr24_flights.json")
        if not os.path.exists(path):
            QMessageBox.critical(self, "Error", f"File not found:\n{path}")
            return
        with open(path, "r", encoding="utf-8") as f:
            flights = json.load(f)
        self.combo_realflights.clear()
        for f in flights:
            label = f"{f['flight_number']} | {f['airline']} | {f['departure_icao']} -> {f['arrival_icao']}"
            self.combo_realflights.addItem(label, f)

    def update_flightinfo(self):
        idx = self.combo_realflights.currentIndex()
        if idx < 0:
            self.label_flightinfo.setText("No flight selected.")
            self.btn_simbrief.setEnabled(False)
            return
        flight = self.combo_realflights.itemData(idx)
        self.label_flightinfo.setText(
            f"<b>{flight['flight_number']}</b><br>"
            f"From {flight['departure_icao']} to {flight['arrival_icao']}<br>"
            f"Scheduled departure: {flight['scheduled_departure']}<br>"
            f"Scheduled arrival: {flight['scheduled_arrival']}<br>"
            f"Aircraft: {flight['aircraft_model']} ({flight['registration']})"
        )
        fields = [
            "aircraft_model",
            "registration",
            "departure_icao",
            "arrival_icao",
            "icao",
        ]
        is_valid = all(flight.get(field) for field in fields)
        self.btn_simbrief.setEnabled(is_valid)

    def save_selected_realflight(self):
        idx = self.combo_realflights.currentIndex()
        if idx < 0:
            QMessageBox.warning(self, "Error", "No flight selected.")
            return
        f = self.combo_realflights.itemData(idx)
        path = os.path.join(RESULTS_DIR, "selected_fr24_flight.json")
        with open(path, "w", encoding="utf-8") as out:
            json.dump(f, out, indent=4, ensure_ascii=False)
        QMessageBox.information(self, "Flight saved", f"Saved in:\n{path}")

    def launch_simbrief(self):
        idx = self.combo_realflights.currentIndex()
        if idx < 0:
            QMessageBox.warning(self, "Error", "No flight selected.")
            return
        flight = self.combo_realflights.itemData(idx)
        simbrief_userid = "25756"
        url = (
            f"https://www.simbrief.com/system/dispatch.php?"
            f"userid={simbrief_userid}"
            f"&type={flight['aircraft_model']}"
            f"&airline={flight['icao']}"
            f"&fltnum={flight['flight_number'].replace(' ', '')}"
            f"&reg={flight['registration']}"
            f"&orig={flight['departure_icao']}"
            f"&dest={flight['arrival_icao']}"
        )
        webbrowser.open(url)

    def change_language(self, lang_code):
        self.translator.set_language(lang_code)
        self.setWindowTitle(self.translator.t("main_window_title"))
        idx = [btn.isChecked() for btn in self.menu_buttons].index(True)
        self.switch_panel(idx)

    def on_language_selected(self, text):
        code = self.lang_combo.currentData()
        if code:
            self.change_language(code)

    # === OVERLAY POSITIONNEMENT ===

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Pour chaque overlay, s'il est visible, on le repositionne
        for panel in [
            self.dashboard_overlay,
            self.fleet_overlay,
            self.flightsetup_overlay,
            self.flightops_overlay,
            self.settings_overlay,
            self.profile_overlay,
            self.devbuild_overlay,
            self.airport_overlay,
        ]:
            if panel.isVisible():
                self.position_overlay(panel)

    def position_overlay(self, panel):
        if panel is not None:
            W = panel.sizeHint().width()
            H = panel.sizeHint().height()
            parentW = self.central.width()
            parentH = self.central.height()
            margin_bottom = 32
            x = max((parentW - W) // 2, 8)
            y = max(parentH - H - margin_bottom, 8)
            panel.setGeometry(
                x, y, min(W, parentW - 16), min(H, parentH - margin_bottom - 8)
            )

if __name__ == "__main__":
    app = QApplication(sys.argv)
    #qt_material.apply_stylesheet(app, theme='light_blue.xml')
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
