import os
import sys
import json
from map_module import Map
from game import Game

# ────────── 키 입력 처리 (Windows / Unix) ──────────
try:
    import msvcrt
    def get_key():
        return msvcrt.getwch()
    def key_pressed():
        return msvcrt.kbhit()
except ImportError:
    import tty, termios, select
    def get_key():
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            return sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
    def key_pressed():
        dr, _, _ = select.select([sys.stdin], [], [], 0)
        return bool(dr)

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

class Menu:
    def __init__(self, maps: dict):
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
                lock = " [Locked]" if item.locked else ""
                print(f"{sel} {title}{lock}")
            print("\n↑/↓: 이동    →: 선택    Q: 종료")

            # 키 입력 대기
            while not key_pressed():
                pass

            ch = get_key()
            if ch.lower() == 'q':
                return

            # 방향키 확인
            if ch == '\xe0':
                direction = get_key()
                if direction == 'H' and self.current > 0:            # ↑
                    self.current -= 1
                elif direction == 'P' and self.current < len(self.titles) - 1:  # ↓
                    self.current += 1
                elif direction == 'M':  # → 선택
                    selected = self.maps[self.titles[self.current]]
                    if selected.locked:
                        continue
                    Game(selected).start()


            


