import os
import sys
from game import Game
from typing import Dict, Any

# ────────── 키 입력 처리 (Windows / Unix) ──────────
try:
    import msvcrt
    def get_key():
        ch = msvcrt.getwch()
        if ch == '\xe0':  # 화살표 키
            ch2 = msvcrt.getwch()
            return {'H': 'UP', 'P': 'DOWN', 'K': 'LEFT', 'M': 'RIGHT'}.get(ch2, '')
        return ch
    def key_pressed():
        return msvcrt.kbhit()
except ImportError:
    import tty, termios, select
    def get_key():
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
            if ch == '\x1b':  # 화살표 키 시작
                seq = sys.stdin.read(2)
                return {'[A': 'UP', '[B': 'DOWN', '[D': 'LEFT', '[C': 'RIGHT'}.get(seq, '')
            return ch
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
    def key_pressed():
        dr, _, _ = select.select([sys.stdin], [], [], 0)
        return bool(dr)

# menu.py
import os
import sys
from map_module import Map
from game import Game
from typing import Dict, Any

# 키 입력 처리 생략
# ... get_key(), key_pressed() 유지 ...

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

class Menu:
    def __init__(self, maps: Dict[str, Dict[str, Any]]):
        """
        maps: {name: {'lines': List[str], 'locked': bool}}
        """
        self.maps = maps
        self.titles = list(maps.keys())
        self.current = 0

    def run(self):
        while True:
            clear()
            print("=== 맵 선택 ===\n")
            for idx, title in enumerate(self.titles):
                item = self.maps[title]
                sel = "▶" if idx == self.current else "  "
                lock = " [Locked]" if item.get('locked', False) else ""
                print(f"{sel} {title}{lock}")
            print("\n↑/↓: 이동    →: 선택    Q: 종료")

            while not key_pressed():
                pass
            ch = get_key()
            if ch.lower() == 'q':
                return

            if ch == 'UP' and self.current > 0:
                self.current -= 1
            elif ch == 'DOWN' and self.current < len(self.titles) - 1:
                self.current += 1
            elif ch == 'RIGHT':
                item = self.maps[self.titles[self.current]]
                if item.get('locked', False):
                    continue
                # MapData에서 name, locked 없이 lines만 사용해 Map 인스턴스 생성
                lines = item.get('lines', [])
                returnValue = item.get('returnValue', None)
                try:
                    map_inst = Map(lines,returnValue)
                except Exception as e:
                    input(f"맵 로드 실패: {e}")
                    continue

                Game(map_inst).start()