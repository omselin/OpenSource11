# map.py
import os
from typing import List, Tuple
import copy
from interpreter import interpret
from colorama import Cursor

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
        self.returnValue=returnValue
        # UNDO/REDO 스택
        self._history: List[List[List[str]]] = []
        self._future: List[List[List[str]]] = []   
        interpret(self) # 이거 에러처리해야함


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
        if len(self._history) <= 1:
            return False
        self._future.append(self._history.pop())
        prev = self._history[-1]
        self._restore_state(prev)
        return True

    def redo(self) -> bool:
        """UNDO 이후 다시 앞으로"""
        if not self._future:
            return False
        state = self._future.pop()
        self._history.append(state)
        self._restore_state(state)
        return True

    def find_players(self) -> List[Tuple[int, int]]:
        return [
            (x, y)
            for y in range(self.H)
            for x in range(self.W)
            if self.board[y][x] == self.PLAYER
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
        if target == '#' or target == self.PLAYER:
            return False

        # 재귀적으로 그 앞 블록을 먼저 밀어 비워 본다
        if not self.move_block(nx, ny, dx, dy):
            return False  # 앞이 안 비워지면 현재 블록도 못 밀음

        # 앞 칸이 비워졌으니 현재 블록 한 칸 이동
        self.board[ny + dy][nx + dx] = target
        self.board[ny][nx] = self.EMPTY
        return True
    def move_and_exe(self,dx:int,dy:int):
        self._save_state()# 현재 상태 저장
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
            self.board[ny][nx] = self.PLAYER

        return True

    def render(self,log="                                             ") -> None:
        print(Cursor.POS(1, 1), end='')  # 커서 위치 초기화
        for row in self.board:
            print(''.join(row))
        print("\n화살표 이동    Q:종료  Z:UNDO  X:REDO")
        print("맵:", self.name)
        print("리턴값:", self.returnValue)
        print(log)

    # 외부에서 호출할 수 있는 UNDO/REDO 메서드
    def perform_undo(self) -> bool:
        return self.undo()

    def perform_redo(self) -> bool:
        return self.redo()