import sys
import os

os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--enable-gpu"
import json
import webbrowser

from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QComboBox,
    QSizePolicy,
)
from PyQt5.QtCore import QUrl, Qt, pyqtSlot, QObject
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebChannel import QWebChannel


class Bridge(QObject):
    def __init__(self, results_dir):
        super().__init__()
        self.results_dir = results_dir

    @pyqtSlot("QVariant", "QVariant")
    def saveSelections(self, aircraft_list, airport_list):
        selected_aircraft_path = os.path.join(
            self.results_dir, "selected_aircraft.json"
        )
        selected_airport_path = os.path.join(self.results_dir, "selected_airports.json")
        try:
            with open(selected_aircraft_path, "w", encoding="utf-8") as f:
                json.dump(list(aircraft_list), f, ensure_ascii=False, indent=2)
            with open(selected_airport_path, "w", encoding="utf-8") as f:
                json.dump(list(airport_list), f, ensure_ascii=False, indent=2)
            print("[OK] Sélections enregistrées :", aircraft_list, airport_list)
        except Exception as e:
            print("[ERREUR] Sauvegarde sélections :", e)

    @pyqtSlot()
    def runScan(self):
        import subprocess
        import sys

        # Chemins relatifs depuis le projet
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        aircraft_cli = os.path.join(base_dir, "scripts", "cli", "aircraft_scanner.py")
        airport_cli = os.path.join(base_dir, "scripts", "cli", "airport_scanner.py")
        try:
            subprocess.run([sys.executable, aircraft_cli], check=True)
            subprocess.run([sys.executable, airport_cli], check=True)
            print("[OK] Scan terminé.")
        except Exception as e:
            print("[ERREUR] Scan échoué:", e)

    @pyqtSlot()
    def showFleetPanel(self):
        mw = QApplication.instance().activeWindow()
        if mw and hasattr(mw, "show_fleet_panel"):
            mw.show_fleet_panel()


# === Chemins (à adapter si besoin) ===
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_DIR = os.path.join(BASE_DIR, "scripts", "data")
MAP_DIR = os.path.join(BASE_DIR, "map")
MAP_HTML_PATH = os.path.join(MAP_DIR, "map.html")

try:
    from scripts.utils.i18n import Translator
except ImportError:
    from ..utils.i18n import Translator


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.translator = Translator("en")
        self.setWindowTitle("RealAirlinesPlanner")
        self.setGeometry(100, 100, 1200, 800)
        self.base_dir = BASE_DIR
        self.results_dir = os.path.join(self.base_dir, "results")  # ← mets bien cette ligne !
        self.data_dir = DATA_DIR
        self.map_dir = MAP_DIR

        # Crée le QWebChannel et le bridge
        self.channel = QWebChannel()
        self.bridge = Bridge(self.results_dir)
        self.channel.registerObject("bridge", self.bridge)

        # === 1. Barre de navigation (onglets du haut) ===
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
        btn_style = """
        QPushButton {
            background: transparent;
            color: #2b3147;
            border: none;
            font-size: 1.06em;
            padding: 10px 18px;
        }
        QPushButton:hover {
            background: #f2f6fc;
            color: #204ba7;
            border-radius: 8px;
        }
        QPushButton:pressed {
            background: #dde6fa;
        }
        QPushButton:checked {
            background: transparent;
            color: #2b3147;
        }
        """

        for btn in self.menu_buttons:
            btn.setCheckable(False)      # NE PAS garder le bouton "coché" après clic
            btn.setStyleSheet(btn_style) # Applique le style clean
            nav_bar.addWidget(btn)  # ← AJOUT OBLIGATOIRE POUR AFFICHER LES BOUTONS

        nav_bar.addStretch()
        nav_bar_widget = QWidget()
        nav_bar_widget.setLayout(nav_bar)
        nav_bar_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # === 2. Carte interactive (plein écran, Leaflet dans QWebEngineView) ===
        self.map_view = QWebEngineView()
        self.map_view.setMinimumHeight(500)
        self.map_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.refresh_map()

        # === 3. Layout principal vertical ===
        self.central = QWidget()
        self.setCentralWidget(self.central)
        central_layout = QVBoxLayout(self.central)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)
        central_layout.addWidget(nav_bar_widget)
        central_layout.addWidget(
            self.map_view, stretch=10
        )  # Seule la carte, pas de stack/overlay Qt

        # === 4. Connexions des boutons du menu => show_xxx_overlay
        self.btn_dashboard.clicked.connect(self.show_dashboard_panel)
        self.btn_fleet.clicked.connect(self.show_fleet_panel)
        self.btn_setup.clicked.connect(self.show_flightsetup_panel)
        self.btn_ops.clicked.connect(self.show_flightops_panel)
        self.btn_settings.clicked.connect(self.show_settings_panel)
        self.btn_profile.clicked.connect(self.show_profile_panel)
        self.btn_devbuild.clicked.connect(self.show_devbuild_panel)

        self.btn_dashboard.setChecked(True)      # Marquer le dashboard comme sélectionné au démarrage

        # === 5. Afficher le dashboard (APPEL FINAL, absolument dernier !) ===
        self.map_view.loadFinished.connect(self._on_map_loaded)

        # Connecte le QWebChannel à la page
        self.map_view.page().setWebChannel(self.channel)

    def _on_map_loaded(self):
        # Injection du QWebChannel JS après le chargement de la page
        self.map_view.page().runJavaScript(
            """
            if (!window.QWebChannel) {
            var script = document.createElement('script');
            script.src = 'qrc:///qtwebchannel/qwebchannel.js';
            document.head.appendChild(script);
            }
        """
        )
        # (puis le reste de ta méthode, comme avant)
        cleanup_script = """
        var toRemove = document.querySelectorAll('#fleet-airport-panel, #dashboard-panel');
        toRemove.forEach(e => e.parentNode.removeChild(e));
        """
        self.map_view.page().runJavaScript(cleanup_script)
        self.show_dashboard_panel()

    def show_overlay_panel(self, panel_id, inner_html):
        """
        Affiche un overlay unifié, en bas de la carte.
        - panel_id : id HTML unique (ex : 'dashboard-panel')
        - inner_html : HTML à injecter dans le cadre
        """
        style = """
        <style>
        #fleet-airport-overlay-bg { display: none !important; }
        .unified-panel {
            position: fixed;
            left: 50%;
            transform: translateX(-50%);
            bottom: 12px;
            z-index: 9999;
            min-width: 1050px;
            max-width: 98vw;
            background: #fff;
            border-radius: 20px;
            border: 1.5px solid #dde;
            box-shadow: 0 8px 32px 0 rgba(80,90,110,0.10);
            padding: 16px 22px 16px 22px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }
        </style>
        """
        html = f"""
        {style}
        <div id="{panel_id}" class="unified-panel">
        {inner_html}
        </div>
        """
        cleanup_script = """
        var toRemove = document.querySelectorAll('.unified-panel, #fleet-airport-panel, #dashboard-panel');
        toRemove.forEach(e => e.parentNode && e.parentNode.removeChild(e));
        """
        self.map_view.page().runJavaScript(cleanup_script)
        self.map_view.page().runJavaScript(
            f"document.body.insertAdjacentHTML('beforeend', `{html}`);"
        )

    # ============ INJECTION HTML/CSS OVERLAY DANS LA CARTE ============

    def show_dashboard_panel(self):
        inner_html = '''
        <div style="width: 100%; min-height: 82px; display: flex; align-items: center; justify-content: center;">
            <div style="font-size: 1.20rem; font-weight: 600; color: #263959; letter-spacing: 0.03em; text-align: center; width: 100%;">
            Dashboard
            </div>
        </div>
        '''
        self.show_overlay_panel("dashboard-panel", inner_html)

    def show_fleet_panel(self):
        """
        Affiche le Fleet & Airport Manager en pleine page, responsive, et injecte les handlers JS.
        Récupère dynamiquement les avions et aéroports depuis les JSON scannés.
        """

        import json

        aircraft_path = os.path.join(self.results_dir, "aircraft_scanresults.json")
        airport_path = os.path.join(self.results_dir, "airport_scanresults.json")
        available_aircraft = []
        available_airports = []

        # === 1. Lecture JSON, robustesse ===
        if os.path.exists(aircraft_path):
            with open(aircraft_path, encoding="utf-8") as f:
                try:
                    available_aircraft = json.load(f)
                except Exception as e:
                    print("[FleetPanel] Erreur de lecture aircraft_scanresults.json :", e)
        if os.path.exists(airport_path):
            with open(airport_path, encoding="utf-8") as f:
                try:
                    available_airports = json.load(f)
                except Exception as e:
                    print("[FleetPanel] Erreur de lecture airport_scanresults.json :", e)

        # === 2. Génération <option> dynamiques, labels humains ===
        def build_aircraft_option(ac):
            # Si ac est dict, utilise un label lisible, sinon juste str
            if isinstance(ac, dict):
                label = f"{ac.get('model', '')} {ac.get('registration', '')} {ac.get('company', '')}".strip()
                value = json.dumps(ac).replace('"', "&quot;")  # Pour usage futur
            else:
                label = str(ac)
                value = str(ac)
            return f'<option value="{value}">{label}</option>'

        def build_airport_option(ap):
            if isinstance(ap, dict):
                label = f"{ap.get('icao', '')} {ap.get('name', '')}".strip()
                value = json.dumps(ap).replace('"', "&quot;")
            else:
                label = str(ap)
                value = str(ap)
            return f'<option value="{value}">{label}</option>'

        aircraft_options = "\n".join(
            [build_aircraft_option(ac) for ac in available_aircraft]
        )
        airport_options = "\n".join([build_airport_option(ap) for ap in available_airports])

        # === 3. Génére le HTML du panel (responsive, full-screen) ===
        html = f"""
        <style>
        .unified-panel {{
            position: fixed;
            left: 50%;
            top: 50%;
            transform: translate(-50%, -50%);
            width: 96vw;
            height: 88vh;
            max-width: 1800px;
            max-height: 900px;
            background: #fff;
            border-radius: 20px;
            border: 1.5px solid #dde;
            box-shadow: 0 8px 32px 0 rgba(80,90,110,0.10);
            padding: 26px 38px 24px 38px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: flex-start;
            overflow: auto;
        }}
        .panel-title {{
            font-size: 2.2rem;
            font-weight: 700;
            margin-bottom: 18px;
            letter-spacing: 0.01em;
            color: #263959;
            text-align: center;
            width: 100%;
        }}
        .panel-row {{
            display: flex;
            align-items: flex-start;
            justify-content: center;
            gap: 26px;
            width: 100%;
            height: 60vh;
            max-height: 620px;
        }}
        .panel-group {{
            display: flex;
            flex-direction: column;
            align-items: center;
            min-width: 220px;
            width: 23vw;
            height: 100%;
        }}
        .panel-label {{
            font-size: 1.18rem;
            font-weight: 500;
            margin-bottom: 7px;
            color: #455;
            text-align: center;
        }}
        .panel-list {{
            width: 99%;
            height: 60vh;
            border-radius: 7px;
            border: 1px solid #ccd;
            background: #f9fafc;
            font-size: 1.12rem;
            padding: 4px;
            resize: none;
        }}
        .panel-transfer {{
            display: flex;
            flex-direction: column;
            gap: 16px;
            align-items: center;
            justify-content: center;
            height: 100%;
        }}
        .panel-transfer button {{
            width: 38px;
            height: 38px;
            font-size: 1.32rem;
            border-radius: 9px;
            border: 1.2px solid #bdd;
            background: #f2f4f7;
            cursor: pointer;
            margin-bottom: 3px;
            transition: background 0.15s;
        }}
        .panel-transfer button:hover {{
            background: #e7f1ff;
        }}
        .panel-action {{
            margin-top: 22px;
            display: flex;
            align-items: center;
            justify-content: center;
            width: 100%;
            gap: 38px;
        }}
        </style>
        <div id="fleet-airport-panel" class="unified-panel">
        <div class="panel-title">Fleet & Airport Manager</div>
        <div class="panel-row">
            <div class="panel-group">
            <div class="panel-label">Available Aircraft</div>
            <select multiple class="panel-list" id="available-aircraft">
                {aircraft_options}
            </select>
            </div>
            <div class="panel-transfer">
            <button id="add-aircraft" title="Ajouter Aircraft">→</button>
            <button id="remove-aircraft" title="Retirer Aircraft">←</button>
            </div>
            <div class="panel-group">
            <div class="panel-label">Selected Aircraft</div>
            <select multiple class="panel-list" id="selected-aircraft"></select>
            </div>
            <div class="panel-group">
            <div class="panel-label">Available Airports</div>
            <select multiple class="panel-list" id="available-airports">
                {airport_options}
            </select>
            </div>
            <div class="panel-transfer">
            <button id="add-airport" title="Ajouter Airport">→</button>
            <button id="remove-airport" title="Retirer Airport">←</button>
            </div>
            <div class="panel-group">
            <div class="panel-label">Selected Airports</div>
            <select multiple class="panel-list" id="selected-airports"></select>
            </div>
        </div>
        <div class="panel-action">
            <button id="save-selection-btn">Apply</button>
            <button id="scan-now-btn">Scan Now</button>
        </div>
        </div>
        """

        # === 4. Injection HTML dans le WebView ===
        cleanup_script = """
            var toRemove = document.querySelectorAll('.unified-panel, #fleet-airport-panel, #dashboard-panel');
            toRemove.forEach(e => e.parentNode && e.parentNode.removeChild(e));
        """
        self.map_view.page().runJavaScript(cleanup_script)
        self.map_view.page().runJavaScript(
            f"document.body.insertAdjacentHTML('beforeend', `{html}`);"
        )

        # === 5. Injection JS pour handlers QWebChannel et transferts ===
        js = """
        // QWebChannel auto-load
        if (typeof QWebChannel === "undefined") {
            var script = document.createElement("script");
            script.src = "qrc:///qtwebchannel/qwebchannel.js";
            script.onload = function() {
                new QWebChannel(qt.webChannelTransport, function(channel) {
                    window.bridge = channel.objects.bridge;
                    attachFleetManagerHandlers();
                });
            };
            document.head.appendChild(script);
        } else {
            new QWebChannel(qt.webChannelTransport, function(channel) {
                window.bridge = channel.objects.bridge;
                attachFleetManagerHandlers();
            });
        }
        function attachFleetManagerHandlers() {
            function moveOptions(fromId, toId) {
                var from = document.getElementById(fromId);
                var to = document.getElementById(toId);
                Array.from(from.selectedOptions).forEach(opt => {
                    to.appendChild(opt);
                });
            }
            document.getElementById('add-aircraft').onclick = function() {
                moveOptions('available-aircraft', 'selected-aircraft');
            };
            document.getElementById('remove-aircraft').onclick = function() {
                moveOptions('selected-aircraft', 'available-aircraft');
            };
            document.getElementById('add-airport').onclick = function() {
                moveOptions('available-airports', 'selected-airports');
            };
            document.getElementById('remove-airport').onclick = function() {
                moveOptions('selected-airports', 'available-airports');
            };
            document.getElementById('save-selection-btn').onclick = function() {
                var selectedAircraft = [];
                Array.from(document.getElementById('selected-aircraft').options).forEach(opt => {
                    selectedAircraft.push(opt.value);
                });
                var selectedAirports = [];
                Array.from(document.getElementById('selected-airports').options).forEach(opt => {
                    selectedAirports.push(opt.value);
                });
                if (window.bridge && window.bridge.saveSelections) {
                    window.bridge.saveSelections(selectedAircraft, selectedAirports);
                    alert("Selections saved!");
                } else {
                    alert("Bridge not available.");
                }
            };
            document.getElementById('scan-now-btn').onclick = function() {
                if (window.bridge && window.bridge.runScan) {
                    window.bridge.runScan();
                    setTimeout(function() {
                        if (window.bridge && window.bridge.showFleetPanel) {
                            window.bridge.showFleetPanel();
                        }
                    }, 1200);
                } else {
                    alert("Scan bridge not available!");
                }
            };
        }
        """
        self.map_view.page().runJavaScript(js)

    def show_flightsetup_panel(self):
        inner_html = '''
            <div style="width: 100%; min-height: 82px; display: flex; align-items: center; justify-content: center;">
                <div style="font-size: 1.20rem; font-weight: 600; color: #263959; letter-spacing: 0.03em; text-align: center; width: 100%;">
                Flight Setup
                </div>
            </div>
            '''
        self.show_overlay_panel("flightsetup-panel", inner_html)

    def show_flightops_panel(self):
        inner_html = '''
            <div style="width: 100%; min-height: 82px; display: flex; align-items: center; justify-content: center;">
                <div style="font-size: 1.20rem; font-weight: 600; color: #263959; letter-spacing: 0.03em; text-align: center; width: 100%;">
                Flight Operations
                </div>
            </div>
            '''
        self.show_overlay_panel("flightops-panel", inner_html)

    def show_settings_panel(self):
        inner_html = """
        <div style="width: 100%; min-height: 82px; display: flex; align-items: center; justify-content: center;">
            <div style="font-size: 1.20rem; font-weight: 600; color: #263959; letter-spacing: 0.03em; text-align: center; width: 100%;">
            Settings
            </div>
        </div>
        """
        self.show_overlay_panel("settings-panel", inner_html)

    def show_profile_panel(self):
        inner_html = """
        <div style="width: 100%; min-height: 82px; display: flex; align-items: center; justify-content: center;">
            <div style="font-size: 1.20rem; font-weight: 600; color: #263959; letter-spacing: 0.03em; text-align: center; width: 100%;">
            Profile
            </div>
        </div>
        """
        self.show_overlay_panel("profile-panel", inner_html)

    def show_devbuild_panel(self):
        inner_html = '''
            <div style="width: 100%; min-height: 82px; display: flex; align-items: center; justify-content: center;">
                <div style="font-size: 1.20rem; font-weight: 600; color: #263959; letter-spacing: 0.03em; text-align: center; width: 100%;">
                DevBuild
                </div>
            </div>
            '''
        self.show_overlay_panel("devbuild-panel", inner_html)

    def inject_overlay(self, html_content):
        """
        Injecte l'HTML (panel overlay) dans la carte via JS.
        """
        js_code = """
        if (window.hideCustomOverlay) window.hideCustomOverlay();
        var tmp = document.createElement('div');
        tmp.innerHTML = %s;
        document.body.appendChild(tmp.firstChild);
        """ % (
            json.dumps(html_content)
        )
        self.map_view.page().runJavaScript(js_code)

    def set_menu_checked(self, btn):
        # Uncheck all, then check only the right one
        for b in self.menu_buttons:
            b.setChecked(False)
        btn.setChecked(True)

    def refresh_map(self):
        map_path = os.path.abspath(os.path.join(self.map_dir, "map.html"))
        self.map_view.load(QUrl.fromLocalFile(map_path))

    def change_language(self, lang_code):
        self.translator.set_language(lang_code)
        self.setWindowTitle(self.translator.t("main_window_title"))
        # Optionnel : rafraîchir le texte des overlays selon la langue


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
