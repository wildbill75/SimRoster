import sys
import os
import json

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QTabWidget, QLabel,
    QPushButton, QFileDialog, QHBoxLayout, QLineEdit, QMessageBox, QComboBox,
    QTableWidget, QTableWidgetItem
)

# Chemin vers le dossier 'results' à la racine du projet
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
RESULTS_DIR = os.path.join(BASE_DIR, "results")
DATA_DIR = os.path.join(BASE_DIR, "scripts", "data")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Real Airlines Planner Prototype")
        self.setGeometry(100, 100, 900, 600)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.community_path = os.path.expandvars(r"%LOCALAPPDATA%\Packages\Microsoft.Limitless_8wekyb3d8bbwe\LocalCache\Packages\Community")
        self.streamed_path = os.path.expandvars(r"%LOCALAPPDATA%\Packages\Microsoft.Limitless_8wekyb3d8bbwe\LocalCache\Packages\StreamedPackages")

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

    def build_dashboard_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.addWidget(QLabel("Carte (à venir)"))
        layout.addWidget(QLabel("Infos / Envol / Préparation / Dernier scan / Statistiques à venir"))
        return tab

    def build_scan_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self.btn_load_aircraft = QPushButton("Charger les avions sélectionnés")
        self.btn_load_airports = QPushButton("Charger les aéroports sélectionnés")

        self.btn_load_aircraft.clicked.connect(self.load_selected_aircraft)
        self.btn_load_airports.clicked.connect(self.load_selected_airports)

        layout.addWidget(self.btn_load_aircraft)
        layout.addWidget(self.btn_load_airports)

        self.aircraft_table = QTableWidget()
        self.aircraft_table.setColumnCount(4)
        self.aircraft_table.setHorizontalHeaderLabels(["Model", "Registration", "Company", "ICAO"])
        layout.addWidget(QLabel("Avions détectés :"))
        layout.addWidget(self.aircraft_table)
        self.aircraft_count = QLabel("")
        layout.addWidget(self.aircraft_count)

        self.airport_table = QTableWidget()
        self.airport_table.setColumnCount(3)
        self.airport_table.setHorizontalHeaderLabels(["ICAO", "Name", "Source"])
        layout.addWidget(QLabel("Aéroports détectés :"))
        layout.addWidget(self.airport_table)
        self.airport_count = QLabel("")
        layout.addWidget(self.airport_count)

        return tab

    def load_selected_aircraft(self):
        path = os.path.join(RESULTS_DIR, 'selected_aircraft.json')
        if not os.path.exists(path):
            QMessageBox.warning(self, "Erreur lecture avions", f"Fichier introuvable :\n{path}")
            return

        with open(path, "r", encoding="utf-8") as f:
            aircraft_list = json.load(f)

        self.aircraft_table.setRowCount(len(aircraft_list))
        for row, aircraft in enumerate(aircraft_list):
            self.aircraft_table.setItem(row, 0, QTableWidgetItem(aircraft.get("model", "")))
            self.aircraft_table.setItem(row, 1, QTableWidgetItem(aircraft.get("registration", "")))
            self.aircraft_table.setItem(row, 2, QTableWidgetItem(aircraft.get("company", "")))
            self.aircraft_table.setItem(row, 3, QTableWidgetItem(aircraft.get("icao", "")))

        self.aircraft_count.setText(f"{len(aircraft_list)} avion(s) sélectionné(s).")

    def load_selected_airports(self):
        path = os.path.join(RESULTS_DIR, 'selected_airports.json')
        if not os.path.exists(path):
            QMessageBox.warning(self, "Erreur lecture aéroports", f"Fichier introuvable :\n{path}")
            return

        with open(path, "r", encoding="utf-8") as f:
            airport_list = json.load(f)

        self.airport_table.setRowCount(len(airport_list))
        for row, airport in enumerate(airport_list):
            self.airport_table.setItem(row, 0, QTableWidgetItem(airport.get("icao", "")))
            self.airport_table.setItem(row, 1, QTableWidgetItem(airport.get("name", "")))
            self.airport_table.setItem(row, 2, QTableWidgetItem(airport.get("source", "")))

        self.airport_count.setText(f"{len(airport_list)} aéroport(s) sélectionné(s).")

    def build_settings_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        layout.addWidget(QLabel("Chemin du dossier Community :"))
        self.input_community = QLineEdit(self.community_path)
        btn_browse_community = QPushButton("Parcourir...")
        btn_browse_community.clicked.connect(self.browse_community)
        layout.addWidget(self.input_community)
        layout.addWidget(btn_browse_community)

        layout.addWidget(QLabel("Chemin du dossier StreamedPackages :"))
        self.input_streamed = QLineEdit(self.streamed_path)
        btn_browse_streamed = QPushButton("Parcourir...")
        btn_browse_streamed.clicked.connect(self.browse_streamed)
        layout.addWidget(self.input_streamed)
        layout.addWidget(btn_browse_streamed)

        return tab

    def browse_community(self):
        path = QFileDialog.getExistingDirectory(self, "Sélectionner le dossier Community")
        if path:
            self.input_community.setText(path)

    def browse_streamed(self):
        path = QFileDialog.getExistingDirectory(self, "Sélectionner le dossier StreamedPackages")
        if path:
            self.input_streamed.setText(path)

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

        self.label_summary = QLabel("")
        layout.addWidget(self.label_summary)

        btn_save_flightplan = QPushButton("Enregistrer le plan de vol")
        btn_save_flightplan.clicked.connect(self.save_flightplan)
        layout.addWidget(btn_save_flightplan)

        self.load_selected_data()
        self.combo_departure.currentIndexChanged.connect(self.update_summary)
        self.combo_arrival.currentIndexChanged.connect(self.update_summary)
        self.combo_aircraft.currentIndexChanged.connect(self.update_summary)

        return tab

    def load_selected_data(self):
        self.selected_airports = []
        self.selected_aircraft = []

        airport_path = os.path.join(RESULTS_DIR, "selected_airports.json")
        aircraft_path = os.path.join(RESULTS_DIR, "selected_aircraft.json")

        if os.path.exists(airport_path):
            with open(airport_path, "r", encoding="utf-8") as f:
                self.selected_airports = json.load(f)

        if os.path.exists(aircraft_path):
            with open(aircraft_path, "r", encoding="utf-8") as f:
                self.selected_aircraft = json.load(f)

        self.combo_departure.clear()
        self.combo_arrival.clear()
        self.combo_aircraft.clear()

        for airport in self.selected_airports:
            label = f"{airport.get('icao', '')} | {airport.get('name', '')}"
            self.combo_departure.addItem(label, airport)
            self.combo_arrival.addItem(label, airport)

        for ac in self.selected_aircraft:
            label = f"{ac.get('model', '')} | {ac.get('company', '')} | {ac.get('registration', '')}"
            self.combo_aircraft.addItem(label, ac)

        self.update_summary()

    def update_summary(self):
        if self.combo_departure.count() < 1 or self.combo_arrival.count() < 1 or self.combo_aircraft.count() < 1:
            self.label_summary.setText("Merci de sélectionner au moins deux aéroports et un avion.")
            return

        dep_idx = self.combo_departure.currentIndex()
        arr_idx = self.combo_arrival.currentIndex()
        ac_idx = self.combo_aircraft.currentIndex()

        if dep_idx == arr_idx:
            self.label_summary.setText("Départ et arrivée doivent être différents.")
            return

        dep_airport = self.combo_departure.itemData(dep_idx)
        arr_airport = self.combo_arrival.itemData(arr_idx)
        aircraft = self.combo_aircraft.itemData(ac_idx)

        summary = (
            f"<b>Départ:</b> {dep_airport['icao']} ({dep_airport['name']})<br>"
            f"<b>Arrivée:</b> {arr_airport['icao']} ({arr_airport['name']})<br>"
            f"<b>Avion:</b> {aircraft['model']} {aircraft['company']} ({aircraft['registration']})"
        )
        self.label_summary.setText(summary)

    def save_flightplan(self):
        dep_idx = self.combo_departure.currentIndex()
        arr_idx = self.combo_arrival.currentIndex()
        ac_idx = self.combo_aircraft.currentIndex()

        if dep_idx == arr_idx:
            QMessageBox.warning(self, "Erreur", "Départ et arrivée doivent être différents.")
            return

        dep_airport = self.combo_departure.itemData(dep_idx)
        arr_airport = self.combo_arrival.itemData(arr_idx)
        aircraft = self.combo_aircraft.itemData(ac_idx)

        plan = {
            "departure": dep_airport,
            "arrival": arr_airport,
            "aircraft": aircraft
        }

        output_file = os.path.join(RESULTS_DIR, "selected_flight_plan.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(plan, f, indent=4, ensure_ascii=False)

        QMessageBox.information(self, "Plan de vol enregistré", f"Le plan de vol a été enregistré !\n\n{output_file}")

    def build_realflight_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.addWidget(QLabel("Fonctionnalités de vol réel à venir..."))
        return tab

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
