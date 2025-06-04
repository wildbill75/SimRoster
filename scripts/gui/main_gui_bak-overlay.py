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
    QListWidgetItem,
    QListWidget,
    QStackedWidget,
    QStackedLayout
)
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtWebEngineWidgets import QWebEngineView

def format_aircraft_label(ac):
    """Affichage court pour la liste."""
    return f"{ac.get('manufacturer','')} {ac.get('model','')} | {ac.get('name','')} | {ac.get('company','')} | {ac.get('registration','')}"

def format_aircraft_tooltip(ac):
    """Tooltip détaillé multi-lignes (HTML pour un affichage propre)."""
    return (
        f"<b>Model:</b> {ac.get('model','')}<br>"
        f"<b>Manufacturer:</b> {ac.get('manufacturer','')}<br>"
        f"<b>Name:</b> {ac.get('name','')}<br>"
        f"<b>Type:</b> {ac.get('type','')}<br>"
        f"<b>Variant:</b> {ac.get('variant','')}<br>"
        f"<b>Engine:</b> {ac.get('engine','')}<br>"
        f"<b>Company:</b> {ac.get('company','')}<br>"
        f"<b>Registration:</b> {ac.get('registration','')}<br>"
        f"<b>Owner type:</b> {ac.get('owner_type','')}<br>"
        f"<b>ICAO:</b> {ac.get('icao','')}<br>"
        f"<b>IATA:</b> {ac.get('iata','')}<br>"
        f"<b>Callsign:</b> {ac.get('callsign','')}<br>"
        f"<b>Radio:</b> {ac.get('radio','')}<br>"
        f"<b>MSFS ID:</b> {ac.get('msfs_id','')}<br>"
        f"<b>Remark:</b> {ac.get('remark','')}"
    )

def normalize_aircraft_dict(ac):
    """S'assure que tous les champs existent dans le dict avion."""
    defaults = {
        "manufacturer": "",
        "model": "",
        "name": "",
        "type": "",
        "variant": "",
        "engine": "",
        "company": "",
        "registration": "",
        "owner_type": "",
        "icao": "",
        "iata": "",
        "callsign": "",
        "radio": "",
        "msfs_id": "",
        "remark": "",
    }
    # Règle pour fallback : model ← name ← type
    ac["model"] = ac.get("model") or ac.get("name") or ac.get("type") or "Unknown"
    for k, v in defaults.items():
        if k not in ac:
            ac[k] = v
    return ac

def add_list_item(listwidget, obj, display_func, tooltip_func=None):
    """Ajoute un objet normalisé dans un QListWidget, avec affichage et tooltip."""

    # Normalise si avion (présence du champ 'model' ou 'manufacturer')
    if "model" in obj or "manufacturer" in obj:
        obj = normalize_aircraft_dict(obj)
    item = QListWidgetItem(display_func(obj))
    if tooltip_func:
        item.setToolTip(tooltip_func(obj))
    item.setData(1000, obj)
    listwidget.addItem(item)

def display_aircraft(ac):
    return f"{ac.get('name','?')} ({ac.get('type','')})"

def display_airport(ap):
    return f"{ap.get('icao','???')} | {ap.get('name','')}"

    return f"{ap.get('icao','???')} | {ap.get('name','')}"

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

    def add_list_item(listwidget, obj, display_func, tooltip_func=None):
        from PyQt5.QtWidgets import QListWidgetItem

        item = QListWidgetItem(display_func(obj))
        if tooltip_func:
            item.setToolTip(tooltip_func(obj))
        item.setData(1000, obj)
        listwidget.addItem(item)

class MainWindow(QMainWindow):

    def populate_aircraft_list(self, aircraft_json_path, listwidget):
        """Charge et affiche la liste des avions avec labels et tooltips dans un QListWidget."""
        import json

        # 1. Lecture du JSON
        try:
            with open(aircraft_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"[ERREUR] Chargement aircraft: {e}")
            data = []

        for ac in data:
            ac = normalize_aircraft_dict(ac)
            item = QListWidgetItem(format_aircraft_label(ac))
            item.setToolTip(format_aircraft_tooltip(ac))
            item.setData(Qt.UserRole, ac)
            listwidget.addItem(item)  

    def __init__(self):
        super().__init__()
        # === 1. Internationalisation / Chemins ===
        self.translator = Translator("en")
        self.setWindowTitle(self.translator.t("main_window_title"))
        self.setGeometry(100, 100, 1200, 800)
        self.base_dir = BASE_DIR
        self.results_dir = RESULTS_DIR
        self.data_dir = DATA_DIR
        self.map_dir = MAP_DIR

        # === 2. Sélecteur de langue ===
        self.language_selector = QComboBox()
        self.language_selector.addItem("English", "en")
        self.language_selector.addItem("Français", "fr")
        self.language_selector.addItem("Deutsch", "de")
        self.language_selector.addItem("Español", "es")
        self.language_selector.setCurrentIndex(0)
        self.language_selector.currentIndexChanged.connect(
            lambda _: self.change_language(self.language_selector.currentData())
        )

        # === 3. Barre de navigation (onglets du haut) ===
        nav_bar = QHBoxLayout()
        self.btn_dashboard = QPushButton("Dashboard")
        self.btn_fleet = QPushButton("Fleet & Airport Manager")
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

        # === 4. Panels contextuels (tous les écrans, QStackedWidget) ===
        self.dashboard_panel = self.build_dashboard_panel()
        self.fleet_panel = self.build_fleet_panel()
        self.flightsetup_panel = self.build_flightsetup_panel()
        self.flightops_panel = self.build_flightops_panel()
        self.settings_panel = self.build_settings_panel()
        self.profile_panel = self.build_profile_panel()
        self.devbuild_panel = self.build_devbuild_panel()
        self.panel_container = QStackedWidget()
        self.panel_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.panel_container.addWidget(self.dashboard_panel)  # 0
        self.panel_container.addWidget(self.fleet_panel)  # 1
        self.panel_container.addWidget(self.flightsetup_panel)  # 2
        self.panel_container.addWidget(self.flightops_panel)  # 3
        self.panel_container.addWidget(self.settings_panel)  # 4
        self.panel_container.addWidget(self.profile_panel)  # 5
        self.panel_container.addWidget(self.devbuild_panel)  # 6
        self.panel_container.setCurrentIndex(0)

        # === 5. Carte en fond, toujours affichée ===
        self.map_view = QWebEngineView()
        self.map_view.setMinimumHeight(500)
        self.map_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.refresh_map()  # Charge la carte (méthode à part)

        # === 6. Overlay principal (carte + panels superposés) ===
        # On veut : carte en fond + panel contextuel centré en bas
        self.overlay_widget = QWidget()
        self.overlay_layout = QStackedLayout(self.overlay_widget)
        self.overlay_layout.setStackingMode(QStackedLayout.StackAll)  # tout empilé

        # -- Carte ajoutée TOUT AU FOND --
        self.overlay_layout.addWidget(self.map_view)

        # -- Container qui centre le panel contextuel EN BAS (overlay flottant) --
        panel_overlay_container = QWidget()
        panel_overlay_container.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        panel_overlay_container.setStyleSheet("background: transparent;")
        panel_overlay_vlayout = QVBoxLayout(panel_overlay_container)
        panel_overlay_vlayout.setContentsMargins(0, 0, 0, 0)
        panel_overlay_vlayout.setSpacing(0)
        panel_overlay_vlayout.addStretch(1)  # pousse le panel vers le bas

        # -- Centre horizontalement le panel, le colle en bas avec marge --
        h_center_layout = QHBoxLayout()
        h_center_layout.setContentsMargins(0, 0, 0, 0)
        h_center_layout.addStretch(1)
        h_center_layout.addWidget(self.panel_container, alignment=Qt.AlignHCenter)
        h_center_layout.addStretch(1)
        panel_overlay_vlayout.addLayout(h_center_layout)
        panel_overlay_vlayout.addSpacing(32)  # espace en bas
        self.overlay_layout.addWidget(panel_overlay_container)

        # === 7. Widget central & Layout principal (vertical) ===
        self.central = QWidget()
        self.setCentralWidget(self.central)
        self.main_layout = QVBoxLayout(self.central)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.main_layout.addWidget(self.language_selector)
        self.main_layout.addWidget(nav_bar_widget)
        self.main_layout.addWidget(self.overlay_widget, stretch=10)

        # === 8. Connexions des boutons de navigation (onglets) ===
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
        # Décoche tous les boutons sauf le bon
        for i, b in enumerate(self.menu_buttons):
            b.setChecked(i == idx)
        # Change le panel affiché dans l'overlay
        self.panel_container.setCurrentIndex(idx)

    def build_dashboard_panel(self):
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
        label = QLabel("Dashboard panel (à remplir)")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 18px; color: #3b4252; margin-top: 80px;")
        layout.addWidget(label)
        return panel

    def build_fleet_panel(self):
        panel = QWidget()
        panel.setMinimumHeight(500)
        panel.setMaximumWidth(520)
        panel.setStyleSheet(
            """
            background: #fff;
            border-radius: 22px;
            border: 1.5px solid #dde;
            box-shadow: 0 8px 40px 0 rgba(80,90,110,0.10);
        """
        )
        main_layout = QVBoxLayout(panel)
        main_layout.setContentsMargins(32, 24, 32, 28)
        main_layout.setSpacing(16)

        title = QLabel("Fleet & Airport Manager")
        title.setStyleSheet(
            "font-size: 20px; font-weight:600; color:#233; margin-bottom:10px;"
        )
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        # ------ AIRCRAFT SECTION ------
        aircraft_layout = QHBoxLayout()
        aircraft_layout.setSpacing(8)

        aircraft_left = QVBoxLayout()
        label_left = QLabel("Available Aircraft")
        label_left.setStyleSheet("font-size:15px; margin-bottom:6px;")
        self.list_aircraft_available = QListWidget()
        self.list_aircraft_available.setSelectionMode(QListWidget.MultiSelection)
        self.list_aircraft_available.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding
        )
        aircraft_left.addWidget(label_left)
        aircraft_left.addWidget(self.list_aircraft_available)

        aircraft_buttons = QVBoxLayout()
        btn_aircraft_add = QPushButton("→")
        btn_aircraft_remove = QPushButton("←")
        btn_aircraft_add.setFixedWidth(36)
        btn_aircraft_remove.setFixedWidth(36)
        btn_aircraft_add.setToolTip("Add selected aircraft")
        btn_aircraft_remove.setToolTip("Remove selected aircraft")
        aircraft_buttons.addStretch(1)
        aircraft_buttons.addWidget(btn_aircraft_add)
        aircraft_buttons.addWidget(btn_aircraft_remove)
        aircraft_buttons.addStretch(1)

        aircraft_right = QVBoxLayout()
        label_right = QLabel("Selected Aircraft")
        label_right.setStyleSheet("font-size:15px; margin-bottom:6px;")
        self.list_aircraft_selected = QListWidget()
        self.list_aircraft_selected.setSelectionMode(QListWidget.MultiSelection)
        self.list_aircraft_selected.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding
        )
        aircraft_right.addWidget(label_right)
        aircraft_right.addWidget(self.list_aircraft_selected)

        aircraft_layout.addLayout(aircraft_left, 3)
        aircraft_layout.addLayout(aircraft_buttons, 1)
        aircraft_layout.addLayout(aircraft_right, 3)
        main_layout.addLayout(aircraft_layout)
        main_layout.addSpacing(20)

        # ------ AIRPORT SECTION ------
        airport_layout = QHBoxLayout()
        airport_layout.setSpacing(8)

        airport_left = QVBoxLayout()
        label_left_ap = QLabel("Available Airports")
        label_left_ap.setStyleSheet("font-size:15px; margin-bottom:6px;")
        self.list_airport_available = QListWidget()
        self.list_airport_available.setSelectionMode(QListWidget.MultiSelection)
        self.list_airport_available.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding
        )
        airport_left.addWidget(label_left_ap)
        airport_left.addWidget(self.list_airport_available)

        airport_buttons = QVBoxLayout()
        btn_airport_add = QPushButton("→")
        btn_airport_remove = QPushButton("←")
        btn_airport_add.setFixedWidth(36)
        btn_airport_remove.setFixedWidth(36)
        btn_airport_add.setToolTip("Add selected airports")
        btn_airport_remove.setToolTip("Remove selected airports")
        airport_buttons.addStretch(1)
        airport_buttons.addWidget(btn_airport_add)
        airport_buttons.addWidget(btn_airport_remove)
        airport_buttons.addStretch(1)

        airport_right = QVBoxLayout()
        label_right_ap = QLabel("Selected Airports")
        label_right_ap.setStyleSheet("font-size:15px; margin-bottom:6px;")
        self.list_airport_selected = QListWidget()
        self.list_airport_selected.setSelectionMode(QListWidget.MultiSelection)
        self.list_airport_selected.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding
        )
        airport_right.addWidget(label_right_ap)
        airport_right.addWidget(self.list_airport_selected)

        airport_layout.addLayout(airport_left, 3)
        airport_layout.addLayout(airport_buttons, 1)
        airport_layout.addLayout(airport_right, 3)
        main_layout.addLayout(airport_layout)
        main_layout.addSpacing(14)

        btn_save = QPushButton("OK / Save Selection")
        btn_save.setFixedWidth(200)
        btn_save.setStyleSheet(
            """
            QPushButton {
                background-color: #f4f6fa;
                border: 1.3px solid #a8b6c8;
                border-radius: 7px;
                padding: 10px 22px;
                font-size: 16px;
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
        """
        )
        btn_save.setCursor(Qt.PointingHandCursor)
        main_layout.addWidget(btn_save, alignment=Qt.AlignCenter)

        # ------ CONNEXIONS ------
        btn_aircraft_add.clicked.connect(
            lambda: self.transfer_selected(
                self.list_aircraft_available, self.list_aircraft_selected, display_aircraft
            )
        )
        btn_aircraft_remove.clicked.connect(
            lambda: self.transfer_back(
                self.list_aircraft_selected, self.list_aircraft_available, display_aircraft
            )
        )
        btn_airport_add.clicked.connect(
            lambda: self.transfer_selected(
                self.list_airport_available, self.list_airport_selected, display_airport
            )
        )
        btn_airport_remove.clicked.connect(
            lambda: self.transfer_back(
                self.list_airport_selected, self.list_airport_available, display_airport
            )
        )
        btn_save.clicked.connect(self.save_selection)

        label_test = QLabel("TEST PANEL FLEET - DOIT ÊTRE ORANGE ET VISIBLE")
        label_test.setStyleSheet("background: orange; color: black; font-size: 38px; padding: 50px;")
        label_test.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(label_test)  # <-- AJOUT

        self.fill_lists()
        return panel

    def fill_lists(self):
        # Mock data, remplace par ton vrai scan ou JSON plus tard !
        aircraft_avail = [
            {
                "name": "Fenix A319",
                "type": "A319",
                "manufacturer": "Airbus",
                "company": "Air France",
                "registration": "F-HXKB",
            },
            {
                "name": "TBM930",
                "type": "TBM930",
                "manufacturer": "Daher",
                "company": "Private",
                "registration": "F-HHHH",
            },
        ]
        aircraft_sel = [
            {
                "name": "Fenix A319",
                "type": "A319",
                "manufacturer": "Airbus",
                "company": "Air France",
                "registration": "F-HXKB",
            },
        ]
        airport_avail = [
            {"icao": "LFPO", "name": "Paris Orly"},
            {"icao": "LFMN", "name": "Nice Côte d'Azur"},
        ]
        airport_sel = [
            {"icao": "LFPO", "name": "Paris Orly"},
        ]

        # ---- AIRCRAFT LISTS ----
        self.list_aircraft_available.clear()
        self.list_aircraft_selected.clear()
        for ac in aircraft_avail:
            if ac not in aircraft_sel:
                add_list_item(
                    self.list_aircraft_available,
                    ac,
                    display_aircraft,
                    format_aircraft_tooltip,
                )
        for ac in aircraft_sel:
            add_list_item(
                self.list_aircraft_selected, ac, display_aircraft, format_aircraft_tooltip
            )

        # ---- AIRPORT LISTS ----
        self.list_airport_available.clear()
        self.list_airport_selected.clear()
        for ap in airport_avail:
            if ap not in airport_sel:
                add_list_item(self.list_airport_available, ap, display_airport)
        for ap in airport_sel:
            add_list_item(self.list_airport_selected, ap, display_airport)

    def transfer_selected(self, src_list, dst_list, display_func, tooltip_func=None):
        """Transfère les items sélectionnés du source_list vers le target_list."""
        selected_items = src_list.selectedItems()
        for item in selected_items:
            obj = item.data(1000)
            add_list_item(dst_list, obj, display_func, tooltip_func)
            src_list.takeItem(src_list.row(item))

    def transfer_back(self, src_list, dst_list, display_func, tooltip_func=None):
        """Transfert dans l'autre sens."""
        selected_items = src_list.selectedItems()
        for item in selected_items:
            obj = item.data(1000)
            add_list_item(dst_list, obj, display_func, tooltip_func)
            src_list.takeItem(src_list.row(item))

    def save_selection(self):
        import json
        aircraft_selected = [
            self.list_aircraft_selected.item(i).data(1000)
            for i in range(self.list_aircraft_selected.count())
        ]
        airports_selected = [
            self.list_airport_selected.item(i).data(1000)
            for i in range(self.list_airport_selected.count())
        ]
        try:
            with open("results/selected_aircraft.json", "w", encoding="utf-8") as f:
                json.dump(aircraft_selected, f, indent=2, ensure_ascii=False)
            with open("results/selected_airports.json", "w", encoding="utf-8") as f:
                json.dump(airports_selected, f, indent=2, ensure_ascii=False)
            QMessageBox.information(self, "Saved", "Selections saved to JSON files.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not save files: {e}")

    def display_airport(ap):
        # Adapte selon tes besoins
        return f"{ap.get('icao','???')} | {ap.get('name','')}"

        selected_items = source_list.selectedItems()
        for item in selected_items:
            obj = item.data(1000)
            add_list_item(target_list, obj, display_func, format_aircraft_tooltip if 'model' in obj else None)
            source_list.takeItem(source_list.row(item))

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

        # --- Chargement des JSON AVEC MIGRATION ---
        if os.path.exists(ap_path):
            try:
                with open(ap_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # MIGRATION AUTO : si ancienne liste de strings
                    if data and isinstance(data[0], str):
                        print(
                            "[INFO] Migration auto: ancienne sélection d'aéroports détectée, conversion en dict minimal."
                        )
                        data = [{"icao": icao, "name": ""} for icao in data]
                    # Correction de compatibilité pour dicts au mauvais format
                    for idx, ap in enumerate(data):
                        if "icao" not in ap:
                            ap["icao"] = ap.get("name", "UNK")
                        if "name" not in ap:
                            ap["name"] = ""
                    self.selected_airports = data
            except Exception as e:
                print(f"[ERREUR] Chargement selected_airports.json : {e}")
                self.selected_airports = []

        if os.path.exists(ac_path):
            try:
                with open(ac_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # MIGRATION AUTO : si ancienne liste de strings
                    if data and isinstance(data[0], str):
                        print(
                            "[INFO] Migration auto: ancienne sélection d'avions détectée, conversion en dict minimal."
                        )
                        data = [
                            {"model": name, "company": "", "registration": ""} for name in data
                        ]
                    # Correction de compatibilité pour dicts au mauvais format
                    for idx, ac in enumerate(data):
                        if "model" not in ac:
                            if "name" in ac:
                                ac["model"] = ac["name"]
                            else:
                                ac["model"] = "Unknown"
                        if "company" not in ac:
                            ac["company"] = ""
                        if "registration" not in ac:
                            ac["registration"] = ""
                    self.selected_aircraft = data
            except Exception as e:
                print(f"[ERREUR] Chargement selected_aircraft.json : {e}")
                self.selected_aircraft = []

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
                label = f"{ac['model']} | {ac.get('company', '')} | {ac.get('registration', '')}"
                self.combo_aircraft.addItem(label, ac)
        else:
            self.combo_aircraft.addItem("No aircraft found")

        # DEBUG : affiche dans la console le résultat
        print(
            "[DEBUG] load_selected_data :",
            "airports:",
            self.combo_departure.count(),
            "aircraft:",
            self.combo_aircraft.count(),
        )

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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    #qt_material.apply_stylesheet(app, theme='light_blue.xml')
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
