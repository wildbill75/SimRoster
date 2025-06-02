import os

map_path = r"C:\Users\Bertrand\Documents\RealAirlinesPlanner\map\map.html"
print("File exists:", os.path.exists(map_path))
print("Absolute path:", os.path.abspath(map_path))

with open(map_path, "r", encoding="utf-8") as f:
    print("Fichier ouvert sans erreur, taille:", len(f.read()))
