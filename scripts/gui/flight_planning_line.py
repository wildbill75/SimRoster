from PyQt5.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QSizePolicy,
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt


class FlightPlanningLineWidget(QWidget):
    def __init__(self, flight_data, logo_path="", parent=None):
        super().__init__(parent)
        self.flight_data = flight_data
        self.setObjectName("FlightPlanningLineWidget")
        self.setMinimumHeight(64)
        self.setStyleSheet(
            """
            #FlightPlanningLineWidget {
                background: transparent;
            }
            QLabel {
                color: #fff;
                font-size: 13px;
            }
            QPushButton {
                background: #3060ff;
                color: #fff;
                border-radius: 10px;
                padding: 4px 16px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #183060;
                color: #ffe36e;
            }
        """
        )
        hbox = QHBoxLayout(self)
        hbox.setContentsMargins(6, 4, 6, 4)
        hbox.setSpacing(12)

        # --- Logo compagnie ---
        self.logo_label = QLabel()
        self.logo_label.setFixedSize(42, 42)
        self.logo_label.setScaledContents(True)
        pixmap = QPixmap(logo_path) if logo_path else QPixmap()
        if not pixmap.isNull():
            self.logo_label.setPixmap(pixmap)
        else:
            self.logo_label.setText("🛫")
            self.logo_label.setAlignment(Qt.AlignCenter)
        hbox.addWidget(self.logo_label)

        # --- Infos principales ---
        vbox = QVBoxLayout()
        vbox.setSpacing(2)
        # Ligne 1 : N° de vol — Départ → Arrivée — Heure
        main_text = (
            f"{flight_data.get('flight_number', 'N/A')}   "
            f"{flight_data.get('dep_icao', '')} → {flight_data.get('arr_icao', '')}   "
            f"{flight_data.get('scheduled_departure', 'N/A')[11:16]} - "
            f"{flight_data.get('scheduled_arrival', 'N/A')[11:16]}"
        )
        self.label_main = QLabel(main_text)
        self.label_main.setStyleSheet("font-weight: bold; font-size: 15px;")
        vbox.addWidget(self.label_main)
        # Ligne 2 : Aircraft, registration, gates, callsign
        secondary = []
        if flight_data.get("aircraft_model"):
            secondary.append(flight_data.get("aircraft_model"))
        if flight_data.get("registration"):
            secondary.append(flight_data.get("registration"))
        if flight_data.get("dep_gate"):
            secondary.append(f"GATE {flight_data.get('dep_gate')}")
        if flight_data.get("arr_gate"):
            secondary.append(f"→ {flight_data.get('arr_gate')}")
        if flight_data.get("airline_icao"):
            secondary.append(flight_data.get("airline_icao"))
        self.label_secondary = QLabel("   ".join(secondary))
        self.label_secondary.setStyleSheet("color: #e0e0e0; font-size: 12px;")
        vbox.addWidget(self.label_secondary)
        hbox.addLayout(vbox)

        # --- Bouton Détails ---
        self.btn_details = QPushButton("Details")
        self.btn_details.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        hbox.addWidget(self.btn_details, alignment=Qt.AlignRight)

        self.setLayout(hbox)
