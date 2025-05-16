from menu import Menu
from map_module import Map
import json
import sys
from typing import List, Dict, Any


if __name__ == "__main__":
    # 커서 숨기기
    sys.stdout.write("\033[?25l")
    sys.stdout.flush()

    menu = Menu("mapdata.json")
    menu.run()