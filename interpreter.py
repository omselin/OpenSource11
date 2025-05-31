from command_parser import parse_and_execute_command
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from map_module import Map
from variablemap import VariableMap
from inf import Inf
import re


EMPTY, SEMICOLON = ' ', ';'


def interpretline(
    map: 'Map',
    pc: int,
    variable_map: VariableMap,
    start_x: int = 0,
    recursionlimit=100
) -> bool:
    """
    한 줄(pc)에서 start_x 위치부터 오른쪽으로 ';' 명령어 해석.
    if: False 시 해당 줄 남은 명령 스킵 (True 리턴)
    while: 조건이 True인 동안 start_x=x+1 위치부터 재귀적으로 실행
    """
    if recursionlimit<0:
        raise RecursionError("무한루프 발생!!")
    for x in range(start_x, map.W):
        if map.board[pc][x] != SEMICOLON:
            continue

        # --- 코드 추출 ---
        code = ''
        tx = x - 1
        while tx >= 0 and map.board[pc][tx] not in (EMPTY, SEMICOLON,'#'):
            code = map.board[pc][tx] + code
            tx -= 1

        # --- if 처리 ---
        if code.startswith('if(') and code.endswith(')'):
            cond = code[3:-1].strip()
            try:
                condition=variable_map.get_value(cond)
            except:
                continue
            if not condition:
                # 이 줄 나머지 건너뛰고 성공 리턴
                return True
        # --- while 처리 (재귀 호출 사용) ---
        elif code.startswith('while(') and code.endswith(')'):
            cond = code[6:-1].strip()
            # 조건이 True인 동안, 줄의 나머지(start_x=x+1부터) 재귀 실행
            try:
                condition = variable_map.get_value(cond)
            except:
                continue
            if condition:
                if not interpretline(map, pc, variable_map, start_x=x+1,recursionlimit=recursionlimit-1):
                    return False
                if not interpretline(map, pc, variable_map, x-len(code),recursionlimit=recursionlimit-1):
                    return False
                # while 끝나면 더 이상 이 줄의 뒤쪽 명령 안 실행
            return True

        # --- 일반 명령 실행 ---
        else:
            try:
                GameOver = parse_and_execute_command(
                    map,
                    variable_map,
                    code,
                    pos=(x, pc)
                )
            except SyntaxError as e:
                continue
            except NameError as e:
                continue
           
            if not GameOver:
                return False

    # 한 줄 끝까지 정상 실행
    return True


def interpret(map: 'Map') -> bool:
    """
    전체 보드를 위에서 아래로 순회하며 interpretline(start_x=0) 실행
    """
    vm = VariableMap()
    for pc in range(map.H):
        if not interpretline(map, pc, vm):
            return False
        

    return True


def get_board_inf(map: "Map"):
    # 토큰 정의
    FUNC     = {"print","drop","swap","delete","scramble","teleport","explode","inverse"}
    CONTROL  = {"if","while","return","return_"}
    SEMI_CH  = {";"}
    BOX_CH   = {"#"}
    OP_CH    = {"=", "+", "-", "*", "/", "%", "|", "&", "!", "(", ")"}
    QUOTE    = {"\"","\'"}

    # 결과 배열 초기화
    board_inf = [
        [Inf.NONE for _ in range(map.W)]
        for _ in range(map.H)
    ]

    # 0) 문자열 리터럴 스캔: "여기안에공백없음"
    string_pattern = re.compile(r'("([^"\s;#]+)")|(\'([^\'\s;#]+)\')')
    for i in range(map.H):
        row = "".join(map.board[i])
        for m in string_pattern.finditer(row):
            start, end = m.start(), m.end()
            for k in range(start, end):
                board_inf[i][k] = Inf.STRING

    # 1) 다글자 토큰 스캔 (문자열 리터럴 건너뛰기)
    scan_list = [
        (CONTROL, Inf.CONTROL),
        (FUNC,    Inf.FUNC),
    ]
    for i in range(map.H):
        row = "".join(map.board[i])
        for token_set, inf_type in scan_list:
            for token in token_set:
                start = 0
                while True:
                    idx = row.find(token, start)
                    if idx == -1:
                        break
                    # 문자열 리터럴 안에 겹치지 않도록 체크
                    if board_inf[i][idx] == Inf.STRING:
                        start = idx + 1
                        continue
                    # 발견된 모든 문자 위치에 inf_type 기록
                    for k in range(len(token)):
                        # 기존 STRING 태그 덮어쓰지 않도록
                        if board_inf[i][idx + k] == Inf.NONE:
                            board_inf[i][idx + k] = inf_type
                    start = idx + 1

    # 2) 남은 한 글자 칸 분류
    for i in range(map.H):
        for j in range(map.W):
            if board_inf[i][j] != Inf.NONE:
                continue  # 이미 태그된 칸 건너뜀
            c = map.board[i][j]
            if c in SEMI_CH:
                board_inf[i][j] = Inf.SEMICOLON
            elif c in OP_CH:
                board_inf[i][j] = Inf.OP
            elif c in BOX_CH:
                board_inf[i][j] = Inf.BOX
            elif c in QUOTE:
                board_inf[i][j] = Inf.STRING
            # else: Inf.NONE 유지

    return board_inf


