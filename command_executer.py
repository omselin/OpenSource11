from typing import TYPE_CHECKING, Tuple
if TYPE_CHECKING:
    from map_module import Map
    from variablemap import VariableMap


def drop(map: 'Map', text: str) -> Tuple[bool, bool]:
    """
    board에 있는 `text` 전부를 아래로 떨어뜨린다.
    - 같은 줄에 연속으로 있는 정확한 문자열만 대상으로 함
    - 밑에 다른 문자가 있거나 보드 바닥에 닿으면 멈춤
    - 하나라도 움직였으면 changed=True
    반환: (changed, True)
    """
    if not text:
        return True

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

    return True
def print_text(map:'Map',pos:tuple,text:str):
    for i, ch in enumerate(text, start=1):
        tx, ty = pos[0] + i, pos[1]
        if 0 <= tx < map.W and 0 <= ty < map.H:
            if map.board[ty][tx] == '#' or map.board[ty][tx] == ';':
                continue
            map.board[ty][tx] = ch
    return True
def assignment(variable_map:'VariableMap',operand_list:list,value):
    for i in range(len(operand_list)-1,-1,-1):
        if operand_list[i].isalpha():
            variable_map.set_variable(operand_list[i], value)
        else:
            raise SyntaxError(f"Invalid variable name: {operand_list[i]}")
    return True
# ⬇️ 이호영님 작업 시작 위치 (이 아래에만 작성해 주세요. 이 주석은 나중에 병합 기준이 되므로 수정하지 마세요.)
# ⬇️ 오유민님 작업 시작 위치 (이 아래에만 작성해 주세요. 이 주석은 나중에 병합 기준이 되므로 수정하지 마세요.)
import random

def scramble_oh(map, args, out):
    """
    맵의 각 줄에서 주어진 target 문자열을 찾아 글자를 무작위로 섞은 후 교환
    """

    target = args[0]

    for y in range(map.H):
       #line = map.board[y]
       line = ''.join(map.board[y])
       if target in line:
            # 글자 섞기
            scrambled = list(target)
            random.shuffle(scrambled)
            scrambled_str = ''.join(scrambled)
            line = line.replace(target, scrambled_str)
            map.board[y] = list(line)  # 문자열 → 리스트 (리스트 유지!)

    return True

def teleport_oh(map, args, out):
    """
    함수 안의 문자 확인 후 맵 훑어보고 같은 문자가 있는 경우 그 문자 옆으로 주인공(;) 위치 이동
    """
    target = args[0]
    new_board = [list(row) for row in map.board]
    height = len(new_board)
    width = len(new_board[0]) if height > 0 else 0

    n = 0
    # 주인공 위치 찾기
    for y in range(height):
        for x in range(width):
            if new_board[y][x] == ";" and new_board[y][x-6] == "t":
                hero_pos = (y, x)
                n = 1
                break#첫 번째로 발견된 ; 위치만 기억
        if n == 1:
            break  # hero_pos를 찾았으면 y 루프도 종료

    # 맵 전체 탐색: target 문자 찾기
    found = False
    for y in range(height):
        for x in range(width):
            if new_board[y][x] == target:
                # 같은 라인에 있는 경우는 제외(함수 안 문자 옆으로 이동 방지)
                if hero_pos and (y == hero_pos[0]):
                    continue
                # 주변 좌표 확인 (왼쪽, 오른쪽, 위, 아래)
                directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
                for dy, dx in directions:
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < height and 0 <= nx < width:
                        if new_board[ny][nx] == " ":  # 빈 칸일 때
                            # 기존 위치 비우기
                            hy, hx = hero_pos
                            new_board[hy][hx] = " "
                            # 새로운 위치로 이동
                            new_board[ny][nx] = ";"
                            found = True
                            break
                if found:
                    break
        if found:
            break

    map.board = new_board
    return True

# ⬇️ 이기상님 작업 시작 위치 (이 아래에만 작성해 주세요. 이 주석은 나중에 병합 기준이 되므로 수정하지 마세요.)
def swap(map: 'Map', args: list, out) -> bool:
    """
    map.board 전체에서 문자 a를 b로 전역적으로 교환한다.
    """
    a, b = args
    board = map.board
    H, W = map.H, map.W

    # 보드 복사하면서 교환
    for y in range(H):
        for x in range(W):
            if board[y][x] == a:
                board[y][x] = '__TEMP__'

    for y in range(H):
        for x in range(W):
            if board[y][x] == '__TEMP__':
                board[y][x] = b
    
    return True
def delete(map: 'Map', args: list, out) -> bool:
    """
    delete(char): 보드 전체에서 해당 문자를 공백(" ")으로 전환
    """
    if not args:
        raise SyntaxError("delete 명령은 delete(char) 형식이어야 합니다")
    target = args[0]

    board = map.board
    H, W = map.H, map.W

    for y in range(H):
        for x in range(W):
            if board[y][x] == target:
                board[y][x] = " "

    return True
# ⬇️ 이현우님 작업 시작 위치 (이 아래에만 작성해 주세요. 이 주석은 나중에 병합 기준이 되므로 수정하지 마세요.)
# ⬇️ Farhan Latiff님 작업 시작 위치 (이 아래에만 작성해 주세요. 이 주석은 나중에 병합 기준이 되므로 수정하지 마세요.)