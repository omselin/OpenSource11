from menu import Menu
from map_module import Map
import json
import sys
from typing import List, Dict, Any


def read_map_data(file_path: str) -> Dict[str, Dict[str, Any]]:
    """
    JSON 파일에서 maps 정보를 읽어
    반환 형식: {name: {'lines': List[str], 'locked': bool}, ...}
    """
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    maps_dict: Dict[str, Dict[str, Any]] = {}
    for entry in data.get("maps", []):
        name = entry.get("name", "")
        raw_data = entry.get("data", [])
        # raw_data가 리스트라면 그대로, 문자열이면 splitlines()
        if isinstance(raw_data, list):
            lines = raw_data
        else:
            lines = raw_data.splitlines()
        locked = bool(entry.get("locked", False))
        maps_dict[name] = {'lines': lines, 'locked': locked}
    return maps_dict


if __name__ == "__main__":
    # 커서 숨기기
    sys.stdout.write("\033[?25l")
    sys.stdout.flush()

    # mapdata.json에서 dict 형식으로 로드
    maps = read_map_data("mapdata.json")
    # Menu는 dict[name]->{lines, locked} 형태로 받음
    menu = Menu(maps)
    menu.run()