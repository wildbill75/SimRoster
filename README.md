✈️ RealAirlinesPlanner (working title: "Real Airlines Planner")

RealAirlinesPlanner is a Python-based application designed for Microsoft Flight Simulator 2024. It generates realistic flight plans based on Flightradar24 data, SimBrief integration, and only uses aircraft and airports that are actually installed in your simulator.

🧠 Goal: simulate real airline operations with 100% realistic constraints — your current addons define what you can fly.

🖥️ Key Features
🔍 Automatic scan of installed aircraft and airports (Community, Official, Addon Linker, etc.)

🗺️ Interactive map of selected airports

🛫 Real flight selection based on mock Flightradar24 data

🧾 Automatic SimBrief flight plan generation

✅ User-friendly GUI built with PyQt5

📦 Installation
1. Requirements
Python 3.10 or newer

Microsoft Flight Simulator 2024

Fenix A319 / A320 / A321 liveries installed

LFPO and LFMN airports installed in MSFS

2. Install dependencies
bash
Copy
Edit
pip install -r requirements.txt
3. Launch the app
bash
Copy
Edit
python scripts/gui/main_gui.py
🗂️ Project Structure
perl
Copy
Edit
RealAirlinesPlanner/
├── scripts/               # Main application logic
│   ├── gui/               # PyQt5 interface
│   ├── utils/             # Map generator and helpers
│   └── scanner/           # MSFS addons scanner
├── data/                  # Source data (airports.csv, callsigns, etc.)
├── results/               # Generated content (JSON scans and selections)
├── map/                   # HTML and JSON for the interactive map
├── requirements.txt       # Python dependencies
└── README.md              # This file
🚧 Upcoming Features
📍 Real-time flight selection from Flightradar24 (mock or API)

📦 Marketplace detection for MSFS official addons

🌐 Convert the app into a web-based version (Flask or Electron)

✈️ Career simulation mode (inspired by ElevateX, A Pilot’s Life)

📸 Preview
Coming soon – screenshots of the UI (Dashboard, Map, Scan, Flight plan, etc.)

👨‍💻 Author
Bertrand / wildbill75-com

GitHub: https://github.com/wildbill75

🤖 AI Collaboration
This project was developed with the assistance of ChatGPT (OpenAI), used as a development copilot for architecture design, UI creation, Python coding, and custom MSFS tool integration.

🙏 Credits
Thanks to the following tools and communities:

SimBrief API – for flight plan generation

Fenix A32X – aircraft and livery support

MSFS Addon Linker – advanced addon management

OurAirports.com – open-source airport location data

📄 License
This project is currently under private development.
A formal license (open source or commercial) will be defined in the future.