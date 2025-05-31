import sys
from map_module import Map,MapManager
import os

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


def clear_screen():
    # 화면 전체 지우고 커서 좌상단으로
    print("\033[0;0H", end='')

# game.py




DIR = {'UP': (0, -1), 'DOWN': (0, 1), 'LEFT': (-1, 0), 'RIGHT': (1, 0)}

class Game:
    def __init__(self, map:Map):
        self.mapmanager = MapManager(map)



    def start(self):
        if os.name == 'nt':
            os.system('cls')
        if not self.mapmanager.initialize():
            return True
            
        self.mapmanager.render()
        while True:
            if key_pressed():
                ch = get_key()
                if ch.lower() == 'q':# QUIT
                    return False
                if ch.lower() == 'z':  # UNDO
                    if self.mapmanager.undo():
                        self.mapmanager.render()
                    continue
                if ch.lower() == 'x':  # REDO
                    if self.mapmanager.redo():
                        self.mapmanager.render()
                    continue
                if ch in DIR:
                    dx, dy = DIR[ch]
                    try:
                        result=self.mapmanager.move_and_execute(dx, dy)
                        # 실패하는 경우는 아직은 무한루프뿐임
                    except RecursionError as e:
                        self.mapmanager.perform_undo()
                        self.mapmanager._future.clear()
                        self.mapmanager.render(f"Error: {e}")
                        #실패한 경우 다시 되돌리기기
                        continue
                    self.mapmanager.render()
                    if not result:
                        return True


