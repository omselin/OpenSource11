from typing import List, Tuple, Optional, Dict
import copy
import multiprocessing
from interpreter import interpret, get_board_inf
from inf import Inf
import 출력관련
#import winsound


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
        # UNDO/REDO 스택: board 상태를 deep copy하여 보관
        self._history: List[List[List[str]]] = []
        self._future: List[List[List[str]]] = []
        # 렌더용 과거 상태
        self.past_board: List[List[str]] = [row.copy() for row in self.logic.board]
        self.past_board_inf: Optional[List[List[Inf]]] = None

        # 멀티프로세싱 풀(항상 살아 있는 상태로 유지)
        self._pool = multiprocessing.Pool(processes=4)
        # 방향별 AsyncResult 저장: (dx, dy) → AsyncResult
        self._futures: Dict[Tuple[int, int], multiprocessing.pool.AsyncResult] = {}

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
        self._clear_futures()
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
        self._clear_futures()
        return True

    def _clear_futures(self):
        """모든 비동기 예측을 취소하지는 못하지만, 레퍼런스를 지워서 무시합니다."""
        self._futures.clear()

    def _precompute_next_moves(self):
        """
        현재 self.logic 상태를 4방향으로 각각 복사하여
        비동기(멀티프로세싱)로 move_and_execute를 호출한 뒤 AsyncResult를 저장합니다.
        기다리지 않고 즉시 반환합니다.
        """
        # 기존에 남아 있는 Future들이 있으면 모두 무시(덮어쓰기)
        self._clear_futures()

        for move in self._NEXT_MOVES:
            # MapLogic 복제본을 생성
            logic_copy = copy.deepcopy(self.logic)
            # apply_async로 비동기 실행, 즉시 AsyncResult 반환
            future = self._pool.apply_async(_simulate_move, args=(logic_copy, move))
            self._futures[move] = future
        # 이 시점에 함수는 반환되며, 백그라운드에서 4개의 작업이 실행 중입니다.

    def initialize(self):
        """
        최초 해석/실행을 호출하고, UNDO를 위해 상태를 저장한 뒤 결과를 반환합니다.
        """
        result = self.logic.initialize()
        self.save_state()
        # 초기 상태에서의 예측을 즉시 예약해 둡니다.
        self._precompute_next_moves()
        return result

    def move_and_execute(self, dx: int, dy: int):
        """
        사용자 입력 방향(dx, dy)에 대해:
        1) 미리 예약된 비동기 예측(Future)이 있는지 검사
           - 있으면 future.ready()로 완료 여부 확인
             · 완료되었으면 future.get()으로 결과 획득
             · 아직 미완료라면, 동기적으로 원본 self.logic에 move_and_execute 호출
           - 없으면(예측이 없으면) 바로 원본 self.logic에 move_and_execute 호출
        2) 예측/동기 처리 결과가 예외(exc)이면 raise
        3) 결과가 False면(False 반환, 이동 불가)
        4) 정상 결과면 self.logic을 적절히 업데이트
        5) 상태 저장, 차후 4방향 예측 예약
        """
# 맵이 변경되었으므로 히스토리 저장
        if not self._history:
            self.save_state()
        elif self._history[-1] != self.logic.board:
            self.save_state()
            #winsound.Beep(1000, 500)
        future = self._futures.get((dx, dy))

        if future is None:
            # → 예측이 없으면 동기 처리: 원본 self.logic에 바로 적용
            try:
                #winsound.Beep(1000, 500)  
                move_result = self.logic.move_and_execute(dx, dy)
                logic_copy = self.logic  # 원본이 이미 바뀌었으므로 복사본 불필요
                exc = None
            except Exception as e:
                move_result = None
                logic_copy = None
                exc = e

        else:
            # → Future가 있으면 완료 여부 확인
            if future.ready():
                logic_copy, move_result, exc = future.get()

            else:
                # 아직 완료되지 않았다면 동기 처리: 원본 self.logic에 바로 적용
                try:
                    #winsound.Beep(1000, 500)  
                    move_result = self.logic.move_and_execute(dx, dy)
                    logic_copy = self.logic
                    exc = None
                except Exception as e:
                    move_result = None
                    logic_copy = None
                    exc = e

            # (dx, dy) 예측으로 예약했던 Future는 사용했으므로 제거
            self._futures.pop((dx, dy), None)

        # 예측/동기 처리 결과 검사
        if exc:
            self._clear_futures()
            raise exc

        if move_result is False:
            self._clear_futures()
            return False

        # 정상 이동/해석: self.logic은 이미 위에서 직접 호출했거나
        # 예측 복제본이 들어왔다면 logic_copy로 교체됨
        if logic_copy is not self.logic:
            # 미래에서 넘어온 복제본을 사용해야 하는 경우
            self.logic = logic_copy

        

        # 새로운 상태 기반으로 4방향 비동기 예측 예약
        self._precompute_next_moves()
        return move_result

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
