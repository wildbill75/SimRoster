import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import scanner  # Assure-toi que scanner.py est bien près de ce fichier


def get_executable_folder():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(__file__)

class MSFSGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MSFS GUI Viewer")
        self.geometry("900x600")

        self.log_lines = []

        # Bouton pour lancer le scan
        self.scan_button = ttk.Button(self, text="Scan Now", command=self.run_scan)
        self.scan_button.pack(pady=10)

        # Zone de texte pour afficher les logs et résultats
        self.output_text = tk.Text(self, wrap=tk.WORD, height=35)
        self.output_text.pack(fill=tk.BOTH, expand=True)

        self.after(100, self.run_scan)  # Lancer automatiquement le scan au démarrage

    def run_scan(self):
        self.output_text.delete(1.0, tk.END)
        self.log_lines.append("\U0001F50D Scanning in progress...")
        self.update_output()

        try:
            scan_results = scanner.scan_msfs_content()

            # Enregistrement dans le dossier de l'exécutable
            json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scanresults.json")
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(scan_results, f, indent=2, ensure_ascii=False)

            self.log_lines.append("\n\u2705 Scan completed.\n")

            self.display_section(scan_results.get("community_airports", []), "Community Airports")
            self.display_section(scan_results.get("asobo_airports", []), "Asobo Airports")
            self.display_section(scan_results.get("marketplace_airports", []), "Marketplace Airports")
            self.display_section(scan_results.get("aircraft", []), "Aircraft")

        except Exception as e:
            self.log_lines.append(f"\n\u274C Error during scan: {e}")

        self.update_output()

    def display_section(self, items, title):
        self.log_lines.append(f"\n=== {title} ({len(items)}) ===")
        for item in items:
            self.log_lines.append(str(item))

    def update_output(self):
        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(tk.END, "\n".join(self.log_lines))
        self.output_text.see(tk.END)


if __name__ == "__main__":
    import sys
    app = MSFSGUI()
    app.mainloop()
