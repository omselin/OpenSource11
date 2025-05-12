import command_executer as ce  
EMPTY, PLAYER_CHAR = ' ', ';'
DIR = {'UP': (0, -1), 'DOWN': (0, 1), 'LEFT': (-1, 0), 'RIGHT': (1, 0)}

def parse_and_execute_command(last_dir, board, H, W, px, py):
    # 플레이어 왼쪽으로 이어진 문자 읽기
    code = ''
    tx = px - 1
    while tx >= 0 and board[py][tx] != EMPTY:
        code = board[py][tx] + code
        tx -= 1
    if code == 'return':
        return False
    # move("..."), 문자열 길이 2 이상 지원
    if code.startswith('move(') and code.endswith(')'):
        raw = code[5:-1]
        if len(raw) >= 2 and raw[0] in ('"', "'") and raw[-1] == raw[0]:
            text = raw[1:-1]
        else:
            text = raw
        dx, dy = last_dir
        # 이동 대상 문자 위치 수집
        return ce.move(text, dx, dy, board, H, W)
    # print("..."), 인용부호 처리
    if code.startswith('print(') and code.endswith(')'):
        arg = code[6:-1]
        if len(arg) >= 2 and arg[0] in ('"', "'") and arg[-1] == arg[0]:
            text = arg[1:-1]
        else:
            text = arg
        return ce.print_text(text, px, py, board, H, W)
        
    return True