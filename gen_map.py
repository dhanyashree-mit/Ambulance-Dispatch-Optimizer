import json
import os

def calculate_manhattan(z1, z2):
    r1 = ord(z1[0]) - ord('A')
    c1 = int(z1[1]) - 1
    r2 = ord(z2[0]) - ord('A')
    c2 = int(z2[1]) - 1
    return abs(r1 - r2) + abs(c1 - c2)

zones = []
distances = {}

for r in ['A', 'B', 'C', 'D']:
    for c in ['1', '2', '3', '4']:
        z = f"{r}{c}"
        zones.append(z)

for z1 in zones:
    distances[z1] = {}
    for z2 in zones:
        dist = calculate_manhattan(z1, z2)
        distances[z1][z2] = dist * 2

city_map = {
    "zones": zones,
    "traffic_multipliers": {
        "normal": 1.0,
        "rush_hour": 1.8,
        "night": 0.7
    },
    "distances": distances
}

out_path = "c:/Users/bhatd/OneDrive/Desktop/Meta_Hackathon/ambulance-dispatch-env/data/city_map.json"
os.makedirs(os.path.dirname(out_path), exist_ok=True)
with open(out_path, "w") as f:
    json.dump(city_map, f, indent=4)

print("Generated city_map.json successfully")
