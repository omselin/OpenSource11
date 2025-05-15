import os
import sys
from map_module import Map
from interpreter import interpret
from variablemap import VariableMap

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
            if ch == '\x1b':  # 화살표 키
                seq = sys.stdin.read(2)
                return {'[A': 'UP', '[B': 'DOWN', '[D': 'LEFT', '[C': 'RIGHT'}.get(seq, '')
            return ch
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
    def key_pressed():
        dr, _, _ = select.select([sys.stdin], [], [], 0)
        return bool(dr)

# ────────── 상수 및 유틸 ──────────
EMPTY, SEMICOLON = ' ', ';'
DIR = {'UP': (0, -1), 'DOWN': (0, 1), 'LEFT': (-1, 0), 'RIGHT': (1, 0)}

def clear_screen():
    # 화면 전체 지우고 커서 좌상단으로
    print("\033[0;0H", end='')

# game.py



# 키 입력 처리 (생략, 기존 코드 유지)
# ... get_key(), key_pressed() 구현 그대로 ...

DIR = {'UP': (0,-1),'DOWN':(0,1),'LEFT':(-1,0),'RIGHT':(1,0)}

DIR = {'UP': (0, -1), 'DOWN': (0, 1), 'LEFT': (-1, 0), 'RIGHT': (1, 0)}

class Game:
    def __init__(self, map:Map):
        self.map = map



    def start(self):
        if os.name == 'nt':
            os.system('cls')
        self.map.render()
        while True:
            if key_pressed():
                ch = get_key()
                if ch.lower() == 'q':
                    break
                if ch.lower() == 'z':  # UNDO
                    if self.map.perform_undo():
                        self.map.render()
                    continue
                if ch.lower() == 'x':  # REDO
                    if self.map.perform_redo():
                        self.map.render()
                    continue
                if ch in DIR:
                    dx, dy = DIR[ch]
                    try:
                        result=self.map.move_and_exe(dx, dy)
                    except RecursionError as e:
                        self.map.perform_undo()
                        self.map._future.clear()
                        self.map.render(f"Error: {e}")
                        continue
                    self.map.render()
                    if not result:
                        break
        print("게임 종료")

