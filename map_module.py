from typing import List, Tuple, Optional, Dict
import copy
from concurrent.futures import ThreadPoolExecutor, Future
import threading
from interpreter import interpret, get_board_inf
from inf import Inf
import 출력관련
import winsound


def _simulate_move(logic_snapshot: "Map", move: Tuple[int, int]):
    """
    단일 방향(dx, dy)에 대해 MapLogic.move_and_execute를 호출하여
    (변경된 MapLogic, 결과, 예외) 튜플을 반환합니다.
    """
    dx, dy = move
    try:
        result = logic_snapshot.move_and_execute(dx, dy)
        return (logic_snapshot, result, None)
    except Exception as e:
        return (None, None, e)


class Map:
    """
    현재 맵 상태를 보관하고, 플레이어 이동, board_inf 계산 및 interpret 호출을 담당하는 클래스
    """
    EMPTY = ' '
    SEMICOLON = ';'
    WALL = '#'

    def __init__(self, name: str, raw_data: List[str], returnValue):
        self.name = name
        lines = raw_data
        self.H = len(lines)
        self.W = max(len(line) for line in lines) if lines else 0
        # board[y][x] 형태로 저장
        self.board: List[List[str]] = [list(line.ljust(self.W, self.EMPTY)) for line in lines]
        self.returnValue = returnValue
        # board_inf를 초기 계산
        self.board_inf: List[List[Inf]] = get_board_inf(self)

    def find_players(self) -> List[Tuple[int, int]]:
        """현재 보드 위에 있는 모든 플레이어(';') 좌표를 반환합니다."""
        return [
            (x, y)
            for y in range(self.H)
            for x in range(self.W)
            if self.board[y][x] == self.SEMICOLON
        ]

    def move_block(self, x: int, y: int, dx: int, dy: int) -> bool:
        """
        (x, y)에 있는 블록을 (dx, dy) 방향으로 밀어봅니다.
        - 앞이 빈칸이면 블록 이동 가능
        - 앞이 고정 블록('#') 또는 플레이어(';')면 이동 불가
        - 재귀적으로 앞 블록을 밀어 비운 뒤 현재 블록을 이동
        """
        nx, ny = x + dx, y + dy
        if not (0 <= nx < self.W and 0 <= ny < self.H):
            return False

        target = self.board[ny][nx]
        if target == self.EMPTY:
            return True
        if target == self.WALL or target == self.SEMICOLON:
            return False

        if not self.move_block(nx, ny, dx, dy):
            return False

        # 앞 칸이 비워졌으니 현재 블록 이동
        self.board[ny + dy][nx + dx] = target
        self.board[ny][nx] = self.EMPTY
        return True

    def move_player(self, dx: int, dy: int) -> bool:
        """
        모든 플레이어를 (dx, dy) 방향으로 이동시도합니다.
        - 이동 가능한 블록들을 재귀적으로 밀고, 플레이어를 한 칸 이동합니다.
        """
        players = self.find_players()
        for x, y in players:
            if not self.move_block(x, y, dx, dy):
                continue
            self.board[y][x] = self.EMPTY
            nx, ny = x + dx, y + dy
            self.board[ny][nx] = self.SEMICOLON
        return True

    def _update_inf(self):
        """현재 board 상태를 바탕으로 board_inf를 갱신합니다."""
        self.board_inf = get_board_inf(self)

    def initialize(self):
        """
        최초 해석/실행을 수행하고 결과를 반환합니다.
        이후 board_inf를 갱신합니다.
        """
        result = interpret(self)
        self._update_inf()
        return result

    def move_and_execute(self, dx: int, dy: int):
        """
        플레이어를 이동시키고 interpret을 호출하여 명령어를 실행한 뒤 결과를 반환합니다.
        실행 후 board_inf를 갱신합니다.
        """
        self.move_player(dx, dy)
        result = interpret(self)
        self._update_inf()
        return result


class MapManager:
    """
    MapLogic 인스턴스를 감싸서
    - 맵 히스토리(UNDO/REDO) 저장 및 제어
    - 다음 4방향에 대한 비동기 예측 (멀티프로세싱)
    - 맵 렌더링 (전체 또는 변경된 부분만 갱신)
    를 담당하는 클래스입니다.
    """
    # 예측할 4가지 방향: 위, 아래, 왼쪽, 오른쪽
    _NEXT_MOVES = [(0, -1), (0, 1), (-1, 0), (1, 0)]

    def __init__(self, logic: Map):
        self.logic = logic
        self._history, self._future = [], []

        self.past_board = [row.copy() for row in logic.board]
        self.past_board_inf = None

        self._pool: ThreadPoolExecutor = ThreadPoolExecutor(max_workers=4)
        self._pred_future: Optional[Future] = None   # 단일 future
        self._pred_dir:    Optional[Tuple[int, int]] = None
        self._lock = threading.Lock()

        self._last_dir: Optional[Tuple[int, int]] = None  # 직전 사용자가 이동한 방향

    def save_state(self):
        """현재 로직의 board를 deep copy하여 히스토리에 저장하고 REDO 스택 초기화."""
        self._history.append(copy.deepcopy(self.logic.board))
        self._future.clear()

    def undo(self) -> bool:
        """
        이전 상태로 되돌립니다. 성공 시 True, 실패 시 False.
        성공 시 logic.board, H, W, board_inf가 복원됩니다.
        """
        if not self._history:
            return False
        # 현재 보드를 REDO 스택에 저장
        self._future.append(copy.deepcopy(self.logic.board))
        prev_state = self._history.pop()
        self.logic.board = copy.deepcopy(prev_state)
        self.logic.H = len(prev_state)
        self.logic.W = len(prev_state[0]) if prev_state else 0
        self.logic._update_inf()
        # 예측된 데이터는 더 이상 유효하지 않으므로 초기화
        self._clear_future()
        #winsound.Beep(1000, 500)
        return True

    def redo(self) -> bool:
        """
        UNDO 이후 다시 앞으로 진행합니다. 성공 시 True, 실패 시 False.
        """
        if not self._future:
            return False
        self._history.append(copy.deepcopy(self.logic.board))
        next_state = self._future.pop()
        self.logic.board = copy.deepcopy(next_state)
        self.logic.H = len(next_state)
        self.logic.W = len(next_state[0]) if next_state else 0
        self.logic._update_inf()
        # 예측된 데이터는 더 이상 유효하지 않으므로 초기화
        self._clear_future()
        return True

    def _precompute_next_move(self, direction: Tuple[int, int]) -> None:
        """direction 한 가지만 미리 계산"""
        self._clear_future()
        logic_copy = copy.deepcopy(self.logic)
        self._pred_future = self._pool.submit(_simulate_move, logic_copy, direction)
        self._pred_dir    = direction

    def _clear_future(self):
        self._pred_future = None
        self._pred_dir    = None

    def initialize(self):
        res = self.logic.initialize()
        self.save_state()            # 첫 상태 저장
        # 아직 사용자가 움직인 적이 없으므로 예측은 건너뛰어도 된다.
        return res

    def move_and_execute(self, dx: int, dy: int):
        direction = (dx, dy)
        # (1) 직전 방향 예측이 있고 완료됐다면 사용
        if self._pred_dir == direction and self._pred_future and self._pred_future.done():
            logic_copy, result, exc = self._pred_future.result()
            #winsound.Beep(1000, 500)
            self._clear_future()
            if exc:
                raise exc
            if logic_copy is not self.logic:
                with self._lock:
                    self.logic = logic_copy
        else:
            # (2) 예측 없거나 미완료 → 동기 실행
            with self._lock:
                result = self.logic.move_and_execute(dx, dy)

        if result is False:          # 이동 불가
            self._clear_future()
            return False

        # (3) 히스토리 저장
        if not self._history or self._history[-1] != self.logic.board:
            self.save_state()

        # (4) 방금 방향을 기록하고, 같은 방향을 다시 예측
        self._last_dir = direction
        self._precompute_next_move(direction)
        return result

    def render_all(self, log: str):
        """보드 전체를 ANSI 컬러 적용하여 출력합니다."""
        game_map = self.logic
        W, H = game_map.W, game_map.H
        board = game_map.board
        board_inf = game_map.board_inf

        # 1) 맵 상단
        print(' ' + '_' * W)

        # 2) ANSI 컬러 매핑
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

        # 3) 각 행 출력
        for i in range(H):
            print('|', end='')
            buffer = ''
            prev_type = board_inf[i][0]
            for j in range(W):
                cur_type = board_inf[i][j]
                ch = board[i][j]
                if cur_type != prev_type:
                    print(f"{COLOR[prev_type]}{buffer}{RESET}", end='')
                    buffer = ch
                    prev_type = cur_type
                else:
                    buffer += ch
            print(f"{COLOR[prev_type]}{buffer}{RESET}", end='')
            print('|')

        # 4) 맵 하단
        print(' ' + '‾' * W)

        # 5) 상태창
        print("\n화살표 이동    Q:종료  Z:UNDO  X:REDO")
        print("맵:", game_map.name)
        print("리턴값:", game_map.returnValue)
        print(log)

        # 6) 이후 diff를 위해 현재 상태 저장
        self.past_board = [row.copy() for row in board]
        self.past_board_inf = [row.copy() for row in board_inf]

    def render_diff(self, log: str):
        """이전 보드와 Inf 정보를 기반으로 변경된 부분만 갱신 출력합니다."""
        game_map = self.logic
        W, H = game_map.W, game_map.H
        board = game_map.board
        new_board_inf = game_map.board_inf

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

        for y in range(H):
            for x in range(W):
                old_ch = self.past_board[y][x]
                new_ch = board[y][x]
                old_type = self.past_board_inf[y][x] if self.past_board_inf else None
                new_type = new_board_inf[y][x]
                if new_ch != old_ch or new_type != old_type:
                    # 커서를 (y+2, x+2)로 이동 (1행: 상단 테두리, 1열: '|' 기호)
                    print(f"\033[{y+2};{x+2}H", end='')
                    print(f"{COLOR[new_type]}{new_ch}{RESET}", end='')

        # 상태창 갱신
        status_row = H + 4
        print(f"\033[{status_row};1H", end='')
        print("화살표 이동    Q:종료  Z:UNDO  X:REDO")
        print(f"맵: {game_map.name}")
        print(f"리턴값: {game_map.returnValue}")
        print(log)

        # 7) 이후 diff를 위해 현재 상태 저장
        self.past_board = [row.copy() for row in board]
        self.past_board_inf = [row.copy() for row in new_board_inf]

    def render(self, log: str = ".                                             "):
        """
        출력 전처리를 수행한 뒤,
        past_board_inf가 None이면 전체 렌더, 아니면 변경된 부분만 렌더합니다.
        """
        H = self.logic.H
        r = 출력관련.출력전처리(H + 7)
        if not r or self.past_board_inf is None:
            self.render_all(log)
        else:
            self.render_diff(log)
