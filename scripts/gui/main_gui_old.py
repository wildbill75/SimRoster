import sys
import os
import json
import webbrowser
import csv

from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QTabWidget,
    QLabel,
    QPushButton,
    QFileDialog,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QComboBox,
    QCheckBox,
    QScrollArea,
    QGroupBox,
    QFormLayout,
)
from PyQt5.QtCore import QTimer, QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView

# ✅ Ajout du chemin racine
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

# ✅ Import du traducteur
from scripts.utils.i18n import Translator

# ✅ Import fonctions de génération de carte
from scripts.utils.generate_map import (
    generate_airports_map_data,
    generate_airports_map_html,
)

# ✅ Constantes de chemin
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RESULTS_DIR = os.path.join(BASE_DIR, "results")
DATA_DIR = os.path.join(BASE_DIR, "scripts", "data")
MAP_DIR = os.path.join(BASE_DIR, "map")
MAP_HTML_PATH = os.path.join(MAP_DIR, "map.html")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # ✅ Initialisation du traducteur multilingue
        self.translator = Translator("en")

        # ✅ Définition des chemins principaux
        self.base_dir = BASE_DIR
        self.results_dir = RESULTS_DIR
        self.data_dir = DATA_DIR
        self.map_dir = MAP_DIR
        self.community_path = os.path.expandvars(
            r"%LOCALAPPDATA%\Packages\Microsoft.Limitless_8wekyb3d8bbwe\LocalCache\Packages\Community"
        )
        self.streamed_path = os.path.expandvars(
            r"%LOCALAPPDATA%\Packages\Microsoft.Limitless_8wekyb3d8bbwe\LocalCache\Packages\StreamedPackages"
        )

        # ✅ Fenêtre principale
        self.setWindowTitle(self.translator.t("main_window_title"))
        self.setGeometry(100, 100, 1200, 800)

        # ✅ Sélecteur de langue (haut de l’interface)
        self.language_selector = QComboBox()
        self.language_selector.addItem("English", "en")
        self.language_selector.addItem("Français", "fr")
        self.language_selector.addItem("Deutsch", "de")
        self.language_selector.addItem("Español", "es")
        self.language_selector.setCurrentIndex(0)
        self.language_selector.currentIndexChanged.connect(
            lambda _: self.change_language(self.language_selector.currentData())
        )

        # ✅ Conteneur onglets
        self.tabs = QTabWidget()

        layout = QVBoxLayout()
        layout.addWidget(self.language_selector)
        layout.addWidget(self.tabs)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # ✅ Initialisation interface
        self.build_tabs()

        # ✅ Données de carte + mise à jour interface
        generate_airports_map_data()
        QTimer.singleShot(500, self.refresh_scan_tab)
 
    def build_tabs(self):
        self.tabs.clear()
        try:
            self.dashboard_tab = self.build_dashboard_tab()
            self.tabs.addTab(self.dashboard_tab, self.translator.t("dashboard_tab"))
        except Exception as e:
            print(f"[ERREUR] dashboard_tab : {e}")

        try:
            self.scan_tab = self.build_scan_tab()
            self.tabs.addTab(self.scan_tab, self.translator.t("scan_tab"))
        except Exception as e:
            print(f"[ERREUR] scan_tab : {e}")

        try:
            self.settings_tab = self.build_settings_tab()
            self.tabs.addTab(self.settings_tab, self.translator.t("settings_tab"))
        except Exception as e:
            print(f"[ERREUR] settings_tab : {e}")

        try:
            self.flightplan_tab = self.build_flightplan_tab()
            self.tabs.addTab(self.flightplan_tab, self.translator.t("flight_plan_tab"))
        except Exception as e:
            print(f"[ERREUR] flightplan_tab : {e}")

        try:
            self.realflight_tab = self.build_realflight_tab()
            self.tabs.addTab(self.realflight_tab, self.translator.t("real_flight_tab"))
        except Exception as e:
            print(f"[ERREUR] realflight_tab : {e}")
        try:
            self.devbuild_tab = self.build_devbuild_tab()
            self.tabs.addTab(self.devbuild_tab, self.translator.t("devbuild_tab"))
        except Exception as e:
            print(f"[ERREUR] Impossible de charger l'onglet DevBuild : {e}")
      

    def build_dashboard_tab(self):
        """
        Onglet Dashboard : affiche la carte interactive avec les aéroports sélectionnés,
        et un bouton pour recharger manuellement la carte.
        """
        tab = QWidget()
        layout = QVBoxLayout()

        # 🔁 Agrandissement de la carte
        self.map_view = QWebEngineView()
        self.map_view.setMinimumHeight(500)  # Ajuste ici si besoin (ex : 600, 700...)
        layout.addWidget(self.map_view, stretch=1)

        # 🔁 Bouton de rafraîchissement manuel
        btn_refresh_map = QPushButton(self.translator.t("refresh_map"))
        btn_refresh_map.clicked.connect(self.refresh_map)
        layout.addWidget(btn_refresh_map)

        # ❌ Labels supprimés pour libérer de l'espace
        # layout.addWidget(QLabel("Infos"))
        # layout.addWidget(QLabel("Envol"))
        # layout.addWidget(QLabel("Préparation"))
        # layout.addWidget(QLabel("Dernier scan"))
        # layout.addWidget(QLabel("Statistiques à venir"))

        # Appliquer le layout
        tab.setLayout(layout)

        # 🔁 Génération initiale des fichiers map
        generate_airports_map_data()
        generate_airports_map_html()

        return tab

    def build_scan_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Groupes pour aéroports et avions
        self.aircraft_checkboxes = []
        self.airport_checkboxes = []

        # Scroll area pour les avions
        aircraft_group = QGroupBox("Avions détectés")
        aircraft_layout = QVBoxLayout()
        self.scroll_aircraft = QScrollArea()
        self.scroll_aircraft.setWidgetResizable(True)
        self.container_aircraft = QWidget()
        self.container_aircraft.setLayout(aircraft_layout)
        self.scroll_aircraft.setWidget(self.container_aircraft)
        aircraft_group.setLayout(QVBoxLayout())
        aircraft_group.layout().addWidget(self.scroll_aircraft)

        # Scroll area pour les aéroports
        airport_group = QGroupBox("Aéroports détectés")
        airport_layout = QVBoxLayout()
        self.scroll_airport = QScrollArea()
        self.scroll_airport.setWidgetResizable(True)
        self.container_airport = QWidget()
        self.container_airport.setLayout(airport_layout)
        self.scroll_airport.setWidget(self.container_airport)
        airport_group.setLayout(QVBoxLayout())
        airport_group.layout().addWidget(self.scroll_airport)

        # Boutons de sauvegarde
        btn_save_aircraft = QPushButton("Sauvegarder les avions sélectionnés")
        btn_save_airports = QPushButton("Sauvegarder les aéroports sélectionnés")
        btn_save_aircraft.clicked.connect(self.save_aircraft_selection)
        btn_save_airports.clicked.connect(self.save_airport_selection)

        # Ajoute tout au layout principal
        layout.addWidget(aircraft_group)
        layout.addWidget(btn_save_aircraft)
        layout.addSpacing(20)
        layout.addWidget(airport_group)
        layout.addWidget(btn_save_airports)

        tab.setLayout(layout)

        # Chargement initial
        self.load_aircraft_list()
        self.load_airport_list()

        return tab

    def load_aircraft_list(self):
        self.aircraft_checkboxes.clear()
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
        self.airport_checkboxes.clear()
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
            try:
                path = os.path.join(RESULTS_DIR, "airport_scanresults.json")
                with open(path, "r", encoding="utf-8") as f:
                    airports = json.load(f)
                self.label_airports.setText(f"{len(airports)} aéroport(s) sélectionné(s).")
                self.label_airports.repaint()
                print(f"[DEBUG] Chargement aéroports depuis : {path}")
                print(f"[DEBUG] Nombre d'aéroports : {len(airports)}")
            except Exception as e:
                self.label_airports.setText("Erreur lors du chargement des aéroports.")
                print(f"[ERREUR] load_selected_airports : {e}")

    def save_aircraft_selection(self):
        selected = []
        for cb, data in zip(self.aircraft_checkboxes, self.aircraft_data):
            if cb.isChecked():
                selected.append(data)
        path = os.path.join(RESULTS_DIR, "selected_aircraft.json")
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(selected, f, indent=4, ensure_ascii=False)
            QMessageBox.information(
                self, "Succès", f"{len(selected)} avion(s) sauvegardé(s) !"
            )
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur sauvegarde avions : {e}")

    def save_airport_selection(self):
        selected = []
        for cb, data in zip(self.airport_checkboxes, self.airport_data):
            if cb.isChecked():
                selected.append(data)
        path = os.path.join(RESULTS_DIR, "selected_airports.json")
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(selected, f, indent=4, ensure_ascii=False)
            QMessageBox.information(
                self, "Succès", f"{len(selected)} aéroport(s) sauvegardé(s) !"
            )
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur sauvegarde aéroports : {e}")

    def build_settings_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        # 🔤 Titre de l'onglet Paramètres
        title = QLabel(self.translator.t("settings_title"))
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        # 🌍 Choix de la langue
        lang_label = QLabel(self.translator.t("select_language"))
        self.lang_combo = QComboBox()
        self.lang_combo.addItem("English", "en")
        self.lang_combo.addItem("Français", "fr")
        self.lang_combo.addItem("Deutsch", "de")
        self.lang_combo.addItem("Español", "es")

        # Pré-sélectionner la langue actuelle
        current_lang_index = self.lang_combo.findData(self.translator.language)
        if current_lang_index != -1:
            self.lang_combo.setCurrentIndex(current_lang_index)

         # ✅ Connexion corrigée : déclenchement sur le texte affiché
        self.lang_combo.currentTextChanged.connect(self.on_language_selected)

        layout.addWidget(lang_label)
        layout.addWidget(self.lang_combo)

        tab.setLayout(layout)
        return tab

    def browse_community(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Sélectionner le dossier Community"
        )
        if folder:
            self.input_community.setText(folder)

    def browse_streamed(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Sélectionner le dossier StreamedPackages"
        )
        if folder:
            self.input_streamed.setText(folder)

    def build_flightplan_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        btn_reload = QPushButton("Recharger la sélection avion/aéroport")
        btn_reload.clicked.connect(self.load_selected_data)
        layout.addWidget(btn_reload)

        self.combo_departure = QComboBox()
        self.combo_arrival = QComboBox()
        self.combo_aircraft = QComboBox()

        layout.addWidget(QLabel("Aéroport de départ"))
        layout.addWidget(self.combo_departure)
        layout.addWidget(QLabel("Aéroport d'arrivée"))
        layout.addWidget(self.combo_arrival)
        layout.addWidget(QLabel("Avion utilisé"))
        layout.addWidget(self.combo_aircraft)

        self.label_summary = QLabel("Résumé du vol")
        layout.addWidget(self.label_summary)

        btn_save = QPushButton("Enregistrer le plan de vol")
        btn_save.clicked.connect(self.save_flightplan)
        layout.addWidget(btn_save)

        self.load_selected_data()
        self.combo_departure.currentIndexChanged.connect(self.update_summary)
        self.combo_arrival.currentIndexChanged.connect(self.update_summary)
        self.combo_aircraft.currentIndexChanged.connect(self.update_summary)

        return tab

    def load_selected_data(self):
        self.selected_airports = []
        self.selected_aircraft = []
        ap_path = os.path.join(RESULTS_DIR, "airport_scanresults.json")
        ac_path = os.path.join(RESULTS_DIR, "aircraft_scanresults.json")

        if os.path.exists(ap_path):
            with open(ap_path, "r", encoding="utf-8") as f:
                self.selected_airports = json.load(f)
        if os.path.exists(ac_path):
            with open(ac_path, "r", encoding="utf-8") as f:
                self.selected_aircraft = json.load(f)

        self.combo_departure.clear()
        self.combo_arrival.clear()
        self.combo_aircraft.clear()

        for ap in self.selected_airports:
            label = f"{ap['icao']} | {ap['name']}"
            self.combo_departure.addItem(label, ap)
            self.combo_arrival.addItem(label, ap)

        for ac in self.selected_aircraft:
            label = f"{ac['model']} | {ac['company']} | {ac['registration']}"
            self.combo_aircraft.addItem(label, ac)

        self.update_summary()

    def update_summary(self):
        if (
            self.combo_departure.count() < 1
            or self.combo_arrival.count() < 1
            or self.combo_aircraft.count() < 1
        ):
            self.label_summary.setText(
                "Merci de charger au moins 2 aéroports et 1 avion."
            )
            return

        dep = self.combo_departure.currentData()
        arr = self.combo_arrival.currentData()
        ac = self.combo_aircraft.currentData()

        if dep["icao"] == arr["icao"]:
            self.label_summary.setText("Départ et arrivée doivent être différents.")
            return

        self.label_summary.setText(
            f"<b>Départ :</b> {dep['icao']} ({dep['name']})<br>"
            f"<b>Arrivée :</b> {arr['icao']} ({arr['name']})<br>"
            f"<b>Avion :</b> {ac['model']} {ac['company']} ({ac['registration']})"
        )

    def save_flightplan(self):
        dep = self.combo_departure.currentData()
        arr = self.combo_arrival.currentData()
        ac = self.combo_aircraft.currentData()

        if dep["icao"] == arr["icao"]:
            QMessageBox.warning(
                self, "Erreur", "Départ et arrivée doivent être différents."
            )
            return

        plan = {"departure": dep, "arrival": arr, "aircraft": ac}
        outpath = os.path.join(RESULTS_DIR, "selected_flight_plan.json")
        with open(outpath, "w", encoding="utf-8") as f:
            json.dump(plan, f, indent=4, ensure_ascii=False)

        QMessageBox.information(
            self, "Plan enregistré", f"Enregistré dans :\n{outpath}"
        )

    def build_realflight_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Combo pour la liste des vols simulés
        self.combo_realflights = QComboBox()
        layout.addWidget(QPushButton("Charger les vols simulés"))
        btn = layout.itemAt(layout.count() - 1).widget()
        btn.clicked.connect(self.load_mock_flights)

        layout.addWidget(self.combo_realflights)

        # Zone d'affichage des infos de vol
        self.label_flightinfo = QLabel("Aucun vol sélectionné.")
        self.label_flightinfo.setWordWrap(True)
        layout.addWidget(self.label_flightinfo)

        # Bouton Enregistrer
        btn_save = QPushButton("Enregistrer ce vol")
        btn_save.clicked.connect(self.save_selected_realflight)
        layout.addWidget(btn_save)

        # Bouton SimBrief avec self.
        self.btn_simbrief = QPushButton("Générer dans SimBrief")
        self.btn_simbrief.setEnabled(False)  # désactivé par défaut
        self.btn_simbrief.clicked.connect(self.launch_simbrief)
        layout.addWidget(self.btn_simbrief)

        # Mise à jour des infos quand un vol est sélectionné
        self.combo_realflights.currentIndexChanged.connect(self.update_flightinfo)

        return tab

    def load_mock_flights(self):
        path = os.path.join(RESULTS_DIR, "mock_fr24_flights.json")
        if not os.path.exists(path):
            QMessageBox.critical(self, "Erreur", f"Fichier introuvable :\n{path}")
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
            self.label_flightinfo.setText("Aucun vol sélectionné.")
            self.btn_simbrief.setEnabled(False)
            return

        flight = self.combo_realflights.itemData(idx)
        self.label_flightinfo.setText(
            f"<b>{flight['flight_number']}</b><br>"
            f"De {flight['departure_icao']} à {flight['arrival_icao']}<br>"
            f"Départ prévu : {flight['scheduled_departure']}<br>"
            f"Arrivée prévue : {flight['scheduled_arrival']}<br>"
            f"Avion : {flight['aircraft_model']} ({flight['registration']})"
        )

        # Activation intelligente du bouton SimBrief
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
            QMessageBox.warning(self, "Erreur", "Aucun vol sélectionné.")
            return
        f = self.combo_realflights.itemData(idx)
        path = os.path.join(RESULTS_DIR, "selected_fr24_flight.json")
        with open(path, "w", encoding="utf-8") as out:
            json.dump(f, out, indent=4, ensure_ascii=False)
        QMessageBox.information(
            self, "Vol enregistré", f"Vol enregistré dans :\n{path}"
        )

    def launch_simbrief(self):
        idx = self.combo_realflights.currentIndex()
        if idx < 0:
            QMessageBox.warning(self, "Erreur", "Aucun vol sélectionné.")
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

    def refresh_scan_tab(self):
        print("[DEBUG] Rafraîchissement visuel forcé des listes Scan.")
        self.load_airport_list()
        self.load_aircraft_list()

    def refresh_map(self):
        """
        Rafraîchit la carte interactive affichée dans le dashboard.
        Cette méthode génère le fichier map_data.json à partir de la sélection,
        vérifie l'existence de map.html et recharge la carte.
        """
        # Générer le fichier map_data.json à partir de la sélection
        generate_airports_map_data()

        # Déterminer le chemin absolu vers map.html
        map_path = os.path.abspath(os.path.join(self.map_dir, "map.html"))
        print(f"[DEBUG] Chemin absolu vers la carte : {map_path}")

        # Vérifier l’existence de la carte
        if not os.path.exists(map_path):
            print(f"[ERREUR] Le fichier map.html est introuvable à ce chemin.")
            return
        else:
            print(f"[DEBUG] Le fichier map.html a été trouvé correctement.")

        # Vérifier l’existence de map_data.json
        map_data_path = os.path.abspath(os.path.join(self.map_dir, "map_data.json"))
        if not os.path.exists(map_data_path):
            print(f"[ERREUR] Le fichier map_data.json est introuvable.")
        else:
            print(f"[DEBUG] Le fichier map_data.json a été généré correctement.")

        # Charger le contenu du fichier JSON (aéroports)
        mapdata_path = os.path.join(self.map_dir, "map_data.json")
        airports_data = []
        if os.path.exists(mapdata_path):
            try:
                with open(mapdata_path, "r", encoding="utf-8") as f:
                    airports_data = json.load(f)
                    print(f"[DEBUG] Le fichier map_data.json a été chargé correctement.")
            except Exception as e:
                print(f"[ERREUR] Lecture de map_data.json : {e}")
        else:
            print(f"[ERREUR] Le fichier map_data.json est introuvable.")

        # Injecter les données dans le HTML (remplacement de la variable spéciale)
        html_template_path = os.path.join(self.map_dir, "map.html")
        try:
            with open(html_template_path, "r", encoding="utf-8") as f:
                html_content = f.read()
                html_with_data = html_content.replace(
                    "__AIRPORTS_DATA__", json.dumps(airports_data, ensure_ascii=False, indent=2)
                )
            with open(html_template_path, "w", encoding="utf-8") as f:
                f.write(html_with_data)
            print("[DEBUG] Données injectées dans map.html avec succès.")
        except Exception as e:
            print(f"[ERREUR] Injection dans map.html : {e}")

        # Charger la carte dans le composant QWebEngineView
        self.map_view.load(QUrl.fromLocalFile(map_path))
        print("[INFO] Carte rechargée dans le dashboard.")

    def change_language(self, lang_code):
        """
        Met à jour la langue de l'application et reconstruit dynamiquement l'interface.
        """
        self.translator.set_language(lang_code)
        self.setWindowTitle(self.translator.t("main_window_title"))
        self.build_tabs()
        self.refresh_map()
        self.refresh_scan_tab()

    def on_language_selected(self, text):
        code = self.lang_combo.currentData()
        if code:
            self.change_language(code)

    def rebuild_ui(self):
        """
        Reconstruit tous les onglets avec les nouvelles traductions.
        """
        self.tabs.clear()

        # Reconstruire les onglets avec la langue actuelle
        self.dashboard_tab = self.build_dashboard_tab()
        self.scan_tab = self.build_scan_tab()
        self.settings_tab = self.build_settings_tab()
        self.flightplan_tab = self.build_flightplan_tab()
        self.realflight_tab = self.build_realflight_tab()

        self.tabs.addTab(self.dashboard_tab, self.translator.t("dashboard_tab"))
        self.tabs.addTab(self.scan_tab, self.translator.t("scan_tab"))
        self.tabs.addTab(self.settings_tab, self.translator.t("settings_tab"))
        self.tabs.addTab(self.flightplan_tab, self.translator.t("flight_plan_tab"))
        self.tabs.addTab(self.realflight_tab, self.translator.t("real_flight_tab"))

        # Met à jour le titre de la fenêtre
        self.setWindowTitle(self.translator.t("main_window_title"))

        # Met à jour les labels du haut et l'onglet paramètres
        if hasattr(self, "language_selector"):
            current_lang_index = self.language_selector.findData(self.translator.language)
            if current_lang_index != -1:
                self.language_selector.setCurrentIndex(current_lang_index)

    def build_devbuild_tab(self):
        """
        Onglet DevBuild : onglet de développement pour les tests internes.
        Contient des boutons utilitaires pour le débogage.
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Exemple : Bouton pour recharger les données de carte
        btn_reload_map = QPushButton("Recharger la carte")
        btn_reload_map.clicked.connect(self.refresh_map)
        layout.addWidget(btn_reload_map)

        # Exemple : Bouton pour forcer le rafraîchissement du Scan
        btn_reload_scan = QPushButton("Recharger la liste Scan")
        btn_reload_scan.clicked.connect(self.refresh_scan_tab)
        layout.addWidget(btn_reload_scan)

        # Exemple : Bouton pour relancer la génération HTML manuellement
        btn_generate_html = QPushButton("Regénérer le HTML de la carte")
        btn_generate_html.clicked.connect(generate_airports_map_html)
        layout.addWidget(btn_generate_html)

        # Espacement
        layout.addStretch()

        return tab

    def check_for_updates(self):
        """
        Simule la vérification de mises à jour pour le moment.
        """
        print("[INFO] Vérification de mise à jour en cours...")
        QMessageBox.information(
            self,
            self.translator.t("devbuild_update_title"),
            self.translator.t("devbuild_update_message")
        )

def generate_airports_map_html():
    """
    Génère un fichier HTML `map.html` à partir de `map_data.json`,
    avec les données injectées directement dans le JavaScript.
    """
    map_json_path = os.path.join(MAP_DIR, "map_data.json")
    map_html_path = os.path.join(MAP_DIR, "map.html")

    if not os.path.exists(map_json_path):
        print(f"[ERREUR] map_data.json introuvable : {map_json_path}")
        return

    # Charger les données JSON des aéroports
    with open(map_json_path, "r", encoding="utf-8") as f:
        airports_data = json.load(f)

    # HTML avec variable spéciale __AIRPORTS_DATA__
    html_template = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8" />
    <title>Carte des Aéroports</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
    <style>
        html, body {{ height: 100%; margin: 0; }}
        #map {{ width: 100%; height: 100%; }}
    </style>
</head>
<body>
    <div id="map"></div>
    <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
    <script>
        const map = L.map('map').setView([46.5, 2.5], 6);
        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            attribution: '© OpenStreetMap contributors'
        }}).addTo(map);

        const airportData = __AIRPORTS_DATA__;

        airportData.forEach(airport => {{
            L.marker([airport.lat, airport.lon])
             .addTo(map)
             .bindPopup(`<strong>${{airport.icao}}</strong><br>${{airport.name}}`);
        }});
    </script>
</body>
</html>
"""

    # Injecter les données dans le HTML
    html_final = html_template.replace(
        "__AIRPORTS_DATA__", json.dumps(airports_data, ensure_ascii=False, indent=2)
    )

    # Écrire le fichier final
    with open(map_html_path, "w", encoding="utf-8") as f:
        f.write(html_final)

    print(f"[INFO] Fichier map.html généré avec succès : {map_html_path}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
