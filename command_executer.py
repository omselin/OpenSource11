from typing import TYPE_CHECKING, Tuple
if TYPE_CHECKING:
    from map_module import Map
    from variablemap import VariableMap

EMPTY, PLAYER_CHAR = ' ', ';'
DIR = {'UP': (0, -1), 'DOWN': (0, 1), 'LEFT': (-1, 0), 'RIGHT': (1, 0)}

def drop(map: 'Map', text: str) -> Tuple[bool, bool]:
    """
    board에 있는 `text` 전부를 아래로 떨어뜨린다.
    - 같은 줄에 연속으로 있는 정확한 문자열만 대상으로 함
    - 밑에 다른 문자가 있거나 보드 바닥에 닿으면 멈춤
    - 하나라도 움직였으면 changed=True
    반환: (changed, True)
    """
    if not text:
        return False, True

    L = len(text)
    board = map.board
    H, W = map.H, map.W

    # 1) 모든 occurrence 수집
    occ = []
    for y in range(H):
        for x in range(W - L + 1):
            if ''.join(board[y][x:x + L]) == text:
                occ.append((x, y))

    # 2) 아래쪽부터 처리(충돌 계산을 단순화)
    occ.sort(key=lambda p: p[1], reverse=True)

    changed = False
    for x, y in occ:
        # 다른 이동 때문에 이미 지워졌을 수도 있으니 다시 확인
        if ''.join(board[y][x:x + L]) != text:
            continue

        # 2-1) 떨어질 수 있는 최대 거리 계산
        dist = 0
        while True:
            ny = y + dist + 1
            if ny >= H:                    # 바닥
                break
            # 아래 칸들이 모두 빈칸인지 확인
            blocked = any(board[ny][x + i] != map.EMPTY for i in range(L))
            if blocked:
                break
            dist += 1

        if dist == 0:
            continue  # 이미 바로 밑이 막혀 있음

        # 2-2) 문자 이동
        changed = True
        for i in range(L):                 # 원래 위치 지우기
            board[y][x + i] = map.EMPTY
        for i, ch in enumerate(text):      # 새로운 위치 채우기
            board[y + dist][x + i] = ch

    return changed, True
def print_text(map:'Map',pos:tuple,text:str):
    for i, ch in enumerate(text, start=1):
        tx, ty = pos[0] + i, pos[1]
        if 0 <= tx < map.W and 0 <= ty < map.H:
            map.board[ty][tx] = ch
    return True,True
def assignment(variable_map:'VariableMap',operand_list:list,value):
    for i in range(len(operand_list)-1,-1,-1):
        if operand_list[i].isalpha():
            variable_map.set_variable(operand_list[i], value)
        else:
            return True,False#,f"Invalid variable name '{variable_list[i]}'."
    return True,True