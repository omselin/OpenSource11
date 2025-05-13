import os
import sys
from map_module import Map
from command_parser import parse_and_execute_command
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

class Game:
    def __init__(self, map_instance: Map):
        self.map = map_instance
        self._parse_map()
        self.last_dir = (0, 0)
        self.variable_map={}

    def _parse_map(self):
        lines = self.map.data.splitlines()
        self.H = len(lines)
        self.W = max(len(line) for line in lines)
        self.board = [list(line.ljust(self.W, EMPTY)) for line in lines]

    def start(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        self._run_code()
        self._draw()
        while True:
            if key_pressed():
                ch = get_key()
                if ch.lower() == 'q':
                    break
                if ch in DIR:
                    dx, dy = DIR[ch]
                    result = self._move_player(dx, dy)
                    if not result:
                        break
                    self._draw()
        print("게임 종료")

    def _draw(self):
        clear_screen()
        for row in self.board:
            print(''.join(row))
        print("\n화살표 이동    Q 종료")
    def _move_player(self, dx, dy):
        player_positions = [(x, y) for y in range(self.H) for x in range(self.W) if self.board[y][x] == SEMICOLON]
        for px, py in player_positions:
            self._move(px, py, dx, dy)
        return self._run_code()

            
    def _move(self,px,py, dx, dy):
        nx, ny = px + dx, py + dy
        if not (0 <= nx < self.W and 0 <= ny < self.H):
            return True
        target = self.board[ny][nx]
        # 블럭(문자) 밀기
        if target != EMPTY and target != SEMICOLON:
            fx, fy = nx + dx, ny + dy
            if 0 <= fx < self.W and 0 <= fy < self.H and self.board[fy][fx] == EMPTY:
                self.board[fy][fx] = target
                self.board[ny][nx] = EMPTY
            else:
                return True
        if target == SEMICOLON:
            return True
        # 플레이어 이동
        self.board[py][px] = EMPTY
        px, py = nx, ny
        self.board[py][px] = SEMICOLON
        self.last_dir = (dx, dy)

    def _run_code(self):
        # 플레이어 왼쪽으로 이어진 문자 읽기
        self.variable_map.clear()
        for y in range(self.H):
            for x in range(self.W):
                if self.board[y][x] == SEMICOLON:
                    code = ''
                    tx = x - 1
                    while tx >= 0 and self.board[y][tx] != EMPTY and self.board[y][tx] != SEMICOLON:
                        code = self.board[y][tx] + code
                        tx -= 1
                    GameOver,문법 = parse_and_execute_command(self.last_dir, self.board,self.variable_map,code, self.H, self.W, x, y)
                    if not GameOver:
                        return False
        return True



