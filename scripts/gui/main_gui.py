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


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.translator = Translator("en")
        self.setWindowTitle("RealAirlinesPlanner")
        self.setGeometry(100, 100, 1200, 800)
        self.base_dir = BASE_DIR
        self.results_dir = RESULTS_DIR
        self.data_dir = DATA_DIR
        self.map_dir = MAP_DIR

        # === 1. Sélecteur de langue ===
        self.language_selector = QComboBox()
        self.language_selector.addItem("English", "en")
        self.language_selector.addItem("Français", "fr")
        self.language_selector.addItem("Deutsch", "de")
        self.language_selector.addItem("Español", "es")
        self.language_selector.setCurrentIndex(0)
        self.language_selector.currentIndexChanged.connect(
            lambda _: self.change_language(self.language_selector.currentData())
        )

        # === 2. Barre de navigation (onglets du haut) ===
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

        # === 3. Carte interactive (plein écran, Leaflet dans QWebEngineView) ===
        self.map_view = QWebEngineView()
        self.map_view.setMinimumHeight(500)
        self.map_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.refresh_map()

        # === 4. Layout principal vertical ===
        self.central = QWidget()
        self.setCentralWidget(self.central)
        central_layout = QVBoxLayout(self.central)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)
        central_layout.addWidget(self.language_selector)
        central_layout.addWidget(nav_bar_widget)
        central_layout.addWidget(
        self.map_view, stretch=10
        )  # Seule la carte, pas de stack/overlay Qt

        # === 5. Connexions des boutons du menu => show_xxx_overlay
        self.btn_dashboard.clicked.connect(self.show_dashboard_panel)
        self.btn_fleet.clicked.connect(self.show_fleet_panel)
        self.btn_setup.clicked.connect(self.show_flightsetup_panel)
        self.btn_ops.clicked.connect(self.show_flightops_panel)
        self.btn_settings.clicked.connect(self.show_settings_panel)
        self.btn_profile.clicked.connect(self.show_profile_panel)
        self.btn_devbuild.clicked.connect(self.show_devbuild_panel)
        self.btn_dashboard.setChecked(True)
        self.show_dashboard_panel()  # Affiche le dashboard au lancement

    # ============ INJECTION HTML/CSS OVERLAY DANS LA CARTE ============

    def show_dashboard_panel(self):
        html = """
            <h2 style="font-size:2em; margin-bottom:1em;">Dashboard</h2>
            <div style="font-size:1.2em;">
                Bienvenue sur le Dashboard !<br>
                Ici tu auras un résumé de l’activité, des liens rapides, etc.
            </div>
        
        """
        self.show_overlay_panel(html)

    def show_fleet_panel(self):
        html = """
            <h2 style="font-size:2em; margin-bottom:1em;">Fleet & Airport Manager</h2>
            <div style="font-size:1.2em;">
                Gère tes avions, livrées, et aéroports installés.<br>
                Bientôt : scan dynamique, filtre, sélection, etc.
            </div>
            
        """
        self.show_overlay_panel(html)

    def show_flightsetup_panel(self):
        html = """
            <h2 style="font-size:2em; margin-bottom:1em;">Flight Setup</h2>
            <div style="font-size:1.2em;">
                Prépare le plan de vol : sélection avion, aéroport, paramètres.<br>
                (À venir : choix du vol, génération SimBrief, etc.)
            </div>
    
        """
        self.show_overlay_panel(html)

    def show_flightops_panel(self):
        html = """
            <h2 style="font-size:2em; margin-bottom:1em;">Flight Ops</h2>
            <div style="font-size:1.2em;">
                Lancement du vol réel, suivi du vol, intégration SimBrief & FR24.<br>
                (Bientôt : suivi live, infos météo, etc.)
            </div>
        
        """
        self.show_overlay_panel(html)

    def show_settings_panel(self):
        html = """
            <h2 style="font-size:2em; margin-bottom:1em;">Settings</h2>
            <div style="font-size:1.2em;">
                Réglages généraux du logiciel.<br>
                Langue, thème, options avancées à venir.
            </div>
           
        """
        self.show_overlay_panel(html)

    def show_profile_panel(self):
        html = """
            <h2 style="font-size:2em; margin-bottom:1em;">Profile</h2>
            <div style="font-size:1.2em;">
                Infos du profil utilisateur.<br>
                (À venir : SimBrief, XP, logs, etc.)
            </div>
           
        """
        self.show_overlay_panel(html)

    def show_devbuild_panel(self):
        html = """
            <h2 style="font-size:2em; margin-bottom:1em;">DevBuild</h2>
            <div style="font-size:1.2em;">
                Panneau développeur – Version Beta.<br>
                (Logs, tests, fonctions expérimentales, etc.)
            </div>
           
        """
        self.show_overlay_panel(html)

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

    def show_overlay_panel(self, html_content):
        js = """
            // Supprime TOUS les overlays, même en cascade
            var c = 0;
            while (document.getElementById('custom-overlay')) {
                document.getElementById('custom-overlay').remove();
                c++;
                if (c > 10) break; // sécurité anti-boucle infinie
            }
        """
        js += f"""
            var div = document.createElement('div');
            div.id = 'custom-overlay';
            div.style.position = 'fixed';
            div.style.left = '50%';
            div.style.top = '50%';
            div.style.transform = 'translate(-50%, -50%)';
            div.style.minWidth = '420px';
            div.style.minHeight = '220px';
            div.style.background = '#fff';
            div.style.color = '#23293b';
            div.style.borderRadius = '22px';
            div.style.boxShadow = '0 12px 60px 0 rgba(50,60,80,0.24)';
            div.style.zIndex = 9999;
            div.style.padding = '44px 36px 38px 36px';
            div.style.display = 'flex';
            div.style.flexDirection = 'column';
            div.style.alignItems = 'center';
            div.style.fontFamily = "'Segoe UI', Arial, sans-serif";
            div.innerHTML = `{html_content.replace('`','\\`')}`;
            document.body.appendChild(div);
        """
        self.map_view.page().runJavaScript(js)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
