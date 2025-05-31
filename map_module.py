
from typing import List, Tuple
import copy
from interpreter import interpret,get_board_inf
from inf import Inf
import 출력관련



class Map:
    """
    맵 데이터를 관리하고, 보드 상태, 렌더링, UNDO/REDO를 책임지는 클래스
    """
    EMPTY = ' '
    SEMICOLON = ';'

    def __init__(self,name:str, raw_data: List[str],returnValue):
        self.name=name
        lines = raw_data
        self.H = len(lines)
        self.W = max(len(line) for line in lines) if lines else 0
        self.board = [list(line.ljust(self.W, self.EMPTY)) for line in lines]
        self.past_board = [row.copy() for row in self.board]
        self.past_board_inf=None
        self.returnValue=returnValue
        # UNDO/REDO 스택
        self._history: List[List[List[str]]] = []
        self._future: List[List[List[str]]] = []   



    def _save_state(self):
        # 현재 보드 상태 저장
        self._history.append(copy.deepcopy(self.board))
        # 새 동작 시 REDO 스택 초기화
        self._future.clear()

    def _restore_state(self, state: List[List[str]]):
        self.board = copy.deepcopy(state)
        self.H = len(self.board)
        self.W = len(self.board[0]) if self.board else 0

    def undo(self) -> bool:
        """이전 상태로 되돌리기"""
        if len(self._history) <= 0:
            return False
        self._future.append(copy.deepcopy(self.board))
        prev = self._history.pop()
        self._restore_state(prev)
        return True

    def redo(self) -> bool:
        """UNDO 이후 다시 앞으로"""
        if not self._future:
            return False
        self._history.append(copy.deepcopy(self.board))
        state = self._future.pop()
        self._restore_state(state)
        return True

    def find_players(self) -> List[Tuple[int, int]]:
        return [
            (x, y)
            for y in range(self.H)
            for x in range(self.W)
            if self.board[y][x] == self.SEMICOLON
        ]

    def move_block(self, x: int, y: int, dx: int, dy: int) -> bool:
        """(x, y)에 있는 블록을 (dx, dy) 방향으로 밀기
        - 연속 블록은 재귀로 한 번에 밀고
        - '#' 은 고정 블록(immovable)
        """
        nx, ny = x + dx, y + dy

        # 보드 경계 체크
        if not (0 <= nx < self.W and 0 <= ny < self.H):
            return False

        target = self.board[ny][nx]

        # 다음 칸이 빈칸이면 바로 이동 가능
        if target == self.EMPTY:
            return True

        # 고정 블록('#')이나 플레이어(';')은 못 밀음
        if target == '#' or target == self.SEMICOLON:
            return False

        # 재귀적으로 그 앞 블록을 먼저 밀어 비워 본다
        if not self.move_block(nx, ny, dx, dy):
            return False  # 앞이 안 비워지면 현재 블록도 못 밀음

        # 앞 칸이 비워졌으니 현재 블록 한 칸 이동
        self.board[ny + dy][nx + dx] = target
        self.board[ny][nx] = self.EMPTY
        return True
    def initialize(self):
        result=interpret(self)
        self._save_state()
        return result
    def move_and_exe(self,dx:int,dy:int):
        if len(self._history)==0: 
            self._save_state()# 현재 상태 저장
        elif self._history[-1]!=self.board:#변화가 없을때
            self._save_state()
        self.move_player(dx,dy)# 플레이어 이동
        return interpret(self)# # 명령어 해석 및 실행 여기서 RecursionError 발생 가능
    def move_player(self, dx: int, dy: int) -> bool:
        players = self.find_players()
        for x, y in players:
            if not self.move_block(x, y, dx, dy):
                continue
            # 플레이어 이동
            self.board[y][x] = self.EMPTY
            nx, ny = x + dx, y + dy
            self.board[ny][nx] = self.SEMICOLON

        return True
    def render_all(self,log):
        # 2) 맵 상단
        print(' ' + '_' * self.W)

        # 3) board_inf 계산
        board_inf = get_board_inf(self)
        self.past_board_inf=board_inf

        # 4) 타입별 ANSI 컬러 매핑 (앞/뒤 reset 포함)
        COLOR = {
            Inf.NONE:      "\033[38;2;135;206;250m",  # 흰색
            Inf.SEMICOLON: "\033[36m",  # 청록색색
            Inf.OP:        "\033[33m",  # 노란색
            Inf.FUNC:      "\033[38;5;229m",  # 연한노란색
            Inf.CONTROL:   "\033[35m",  # 보라색
            Inf.BOX:       "\033[90m",  # 밝은 회색 
            Inf.STRING:    "\033[38;2;255;200;100m" ,#밝은은주황색

        }
        RESET = "\033[0m"

        # 5) 각 행 출력
        for i in range(self.H):
            print('|', end='')

            # 버퍼와 현재 타입
            buffer = ''
            prev_type = board_inf[i][0]

            for j in range(self.W):
                cur_type = board_inf[i][j]
                ch = self.board[i][j]

                # 타입이 바뀌면 그간 쌓인 buffer를 출력하고 초기화
                if cur_type != prev_type:
                    # 색 적용
                    print(f"{COLOR[prev_type]}{buffer}{RESET}", end='')
                    buffer = ch
                    prev_type = cur_type
                else:
                    buffer += ch

            # 마지막 버퍼 출력
            print(f"{COLOR[prev_type]}{buffer}{RESET}", end='')
            print('|')

        # 6) 맵 하단
        print(' ' + '‾' * self.W)

        # 7) 상태창
        print("\n화살표 이동    Q:종료  Z:UNDO  X:REDO")
        print("맵:", self.name)
        print("리턴값:", self.returnValue)
        print(log)
    def render_diff(self, log):
        # ANSI 컬러 매핑 (render_all과 동일)
        COLOR = {
            Inf.NONE:      "\033[38;2;135;206;250m",
            Inf.SEMICOLON: "\033[36m",
            Inf.OP:        "\033[33m",
            Inf.FUNC:      "\033[38;5;229m",
            Inf.CONTROL:   "\033[35m",
            Inf.BOX:       "\033[90m",
            Inf.STRING:    "\033[38;2;255;200;100m",
        }
        RESET = "\033[0m"

        # 새 타입 맵 계산
        new_board_inf = get_board_inf(self)

        # 1) 변경된 셀만 출력
        for y in range(self.H):
            for x in range(self.W):
                old_ch = self.past_board[y][x]
                new_ch = self.board[y][x]
                old_type = self.past_board_inf[y][x]
                new_type = new_board_inf[y][x]

                if new_ch != old_ch or new_type != old_type:
                    # 커서를 (y+2, x+2) 위치로 이동 (1행: 상단 테두리, 1열: '|' 기호)
                    print(f"\033[{y+2};{x+2}H", end='')
                    # 색 적용 후 문자 출력
                    print(f"{COLOR[new_type]}{new_ch}{RESET}", end='')

        # 2) 상태창도 갱신
        # 커서를 맵 아래로 이동
        status_row = self.H + 4
        print(f"\033[{status_row};1H", end='')
        print("화살표 이동    Q:종료  Z:UNDO  X:REDO")
        print(f"맵: {self.name}")
        print(f"리턴값: {self.returnValue}")
        print(log)

        # 3) 이후 비교용으로 현재 상태 저장
        self.past_board = [row.copy() for row in self.board]
        self.past_board_inf = new_board_inf


    def render(self, log=".                                             ") -> None:
        
        #log=x
        r=출력관련.출력전처리(self.H+7)
        if not r or self.past_board_inf is None:
            self.render_all(log=log)
        else:
            self.render_diff(log=log)

        

    # 외부에서 호출할 수 있는 UNDO/REDO 메서드
    def perform_undo(self) -> bool:
        return self.undo()

    def perform_redo(self) -> bool:
        return self.redo()