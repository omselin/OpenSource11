from command_parser import parse_and_execute_command
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from map_module import Map
from variablemap import VariableMap

EMPTY, SEMICOLON = ' ', ';'


def interpretline(
    map: 'Map',
    pc: int,
    variable_map: VariableMap,
    start_x: int = 0
) -> bool:
    """
    한 줄(pc)에서 start_x 위치부터 오른쪽으로 ';' 명령어 해석.
    if: False 시 해당 줄 남은 명령 스킵 (True 리턴)
    while: 조건이 True인 동안 start_x=x+1 위치부터 재귀적으로 실행
    """
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
            if not variable_map.get_value(cond):
                # 조건 거짓 → 이 줄 나머지 건너뛰고 성공 리턴
                return True

        # --- while 처리 (재귀 호출 사용) ---
        elif code.startswith('while(') and code.endswith(')'):
            cond = code[6:-1].strip()
            # 조건이 True인 동안, 줄의 나머지(start_x=x+1부터) 재귀 실행
            if variable_map.get_value(cond):
                if not interpretline(map, pc, variable_map, start_x=x+1):
                    return False
                if not interpretline(map, pc, variable_map, x-len(code)-1):
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
