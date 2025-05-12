
from menu import Menu
from map_module import Map
import json
import sys


def read_map_data(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    maps = {}
    for e in data["maps"]:
        raw = e.get("data", "")
        map_text = "\n".join(raw) if isinstance(raw, list) else raw
        maps[e["name"]] = Map(e["name"], locked=e.get("locked", False), data=map_text)
    return maps   
if __name__ == "__main__":
    sys.stdout.write("\033[?25l")
    sys.stdout.flush()
    maps = read_map_data("mapdata.json")
    Menu(maps).run()