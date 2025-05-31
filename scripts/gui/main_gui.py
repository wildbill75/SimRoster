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


# Chemins relatifs
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RESULTS_DIR = os.path.join(BASE_DIR, "results")
DATA_DIR = os.path.join(BASE_DIR, "scripts", "data")
MAP_DIR = os.path.join(BASE_DIR, "map")
MAP_HTML_PATH = os.path.join(MAP_DIR, "map.html")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Real Airlines Planner Prototype")
        self.setGeometry(100, 100, 900, 600)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.community_path = os.path.expandvars(
            r"%LOCALAPPDATA%\Packages\Microsoft.Limitless_8wekyb3d8bbwe\LocalCache\Packages\Community"
        )
        self.streamed_path = os.path.expandvars(
            r"%LOCALAPPDATA%\Packages\Microsoft.Limitless_8wekyb3d8bbwe\LocalCache\Packages\StreamedPackages"
        )

        self.dashboard_tab = self.build_dashboard_tab()
        self.scan_tab = self.build_scan_tab()
        self.settings_tab = self.build_settings_tab()
        self.flightplan_tab = self.build_flightplan_tab()
        self.realflight_tab = self.build_realflight_tab()

        self.tabs.addTab(self.dashboard_tab, "Dashboard")
        self.tabs.addTab(self.scan_tab, "Scan")
        self.tabs.addTab(self.settings_tab, "Settings")
        self.tabs.addTab(self.flightplan_tab, "Flight Plan")
        self.tabs.addTab(self.realflight_tab, "Vol réel")

        QTimer.singleShot(500, self.refresh_scan_tab)

    def build_dashboard_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        self.map_view = QWebEngineView()

        # Ajout immédiat du widget dans l'UI
        layout.addWidget(self.map_view)

        # Bouton pour forcer le rechargement plus tard
        btn_refresh_map = QPushButton("Rafraîchir la carte")
        btn_refresh_map.clicked.connect(self.refresh_map)
        layout.addWidget(btn_refresh_map)

        # Éléments d'interface déjà présents dans ton onglet Dashboard
        layout.addWidget(QLabel("Infos"))
        layout.addWidget(QLabel("Envol"))
        layout.addWidget(QLabel("Préparation"))
        layout.addWidget(QLabel("Dernier scan"))
        layout.addWidget(QLabel("Statistiques à venir"))

        tab.setLayout(layout)

        # 🧠 Appel direct de la méthode qui charge la carte
        self.refresh_map()

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
        layout = QVBoxLayout(tab)

        self.input_community = QLineEdit(self.community_path)
        btn_browse_community = QPushButton("Parcourir Community")
        btn_browse_community.clicked.connect(self.browse_community)

        self.input_streamed = QLineEdit(self.streamed_path)
        btn_browse_streamed = QPushButton("Parcourir StreamedPackages")
        btn_browse_streamed.clicked.connect(self.browse_streamed)

        layout.addWidget(QLabel("Dossier Community"))
        layout.addWidget(self.input_community)
        layout.addWidget(btn_browse_community)

        layout.addWidget(QLabel("Dossier StreamedPackages"))
        layout.addWidget(self.input_streamed)
        layout.addWidget(btn_browse_streamed)

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
        print("[DEBUG] Rafraîchissement visuel forcé des labels Scan.")

    def refresh_map(self):
        # On remonte à la racine du projet (RealAirlinesPlanner) et on va dans "map/map.html"
        map_path = os.path.abspath(os.path.join(BASE_DIR, "map", "map.html"))
        print("[DEBUG] Chemin absolu vers la carte :", map_path)

        if not os.path.exists(map_path):
            print("[ERREUR] Le fichier map.html est introuvable à ce chemin.")
        else:
            print("[DEBUG] Le fichier map.html a été trouvé correctement.")

        self.map_view.load(QUrl.fromLocalFile(map_path))
        print("[INFO] Carte rechargée dans le dashboard.")

    def generate_airports_map_data(self):
        """
        Génère un fichier JSON contenant les aéroports sélectionnés avec coordonnées lat/lon
        à partir de 'airports.csv' pour affichage dans Leaflet.
        """
        csv_path = os.path.join(DATA_DIR, "airports.csv")
        selected_json = os.path.join(RESULTS_DIR, "selected_airports.json")
        output_json = os.path.join("map", "airports_map_data.json")

        if not os.path.exists(csv_path) or not os.path.exists(selected_json):
            print("[WARN] Fichier CSV ou JSON manquant pour la carte.")
            return

        with open(selected_json, "r", encoding="utf-8") as f:
            selected = json.load(f)
            selected_icaos = {a["icao"] for a in selected if "icao" in a}

        results = []
        with open(csv_path, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                icao = row.get("ICAO", "").strip().upper()
                if icao in selected_icaos:
                    try:
                        lat = float(row["Latitude"])
                        lon = float(row["Longitude"])
                        results.append(
                            {
                                "icao": icao,
                                "name": row.get("Name", "Unknown"),
                                "lat": lat,
                                "lon": lon,
                            }
                        )
                    except Exception as e:
                        print(f"[ERREUR] Coordonnées invalides pour {icao} : {e}")

        with open(output_json, "w", encoding="utf-8") as out:
            json.dump(results, out, indent=2)
            print(f"[INFO] {len(results)} aéroports exportés pour la carte.")   


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
