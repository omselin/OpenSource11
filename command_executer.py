EMPTY, PLAYER_CHAR = ' ', ';'
DIR = {'UP': (0, -1), 'DOWN': (0, 1), 'LEFT': (-1, 0), 'RIGHT': (1, 0)}

def move(text: str,dx,dy,board,H,W):
    positions = [(x, y) for y in range(H) for x in range(W) if board[y][x] in text]
    # 방향별 정렬
    if dx > 0: positions.sort(key=lambda p: p[0], reverse=True)
    if dx < 0: positions.sort(key=lambda p: p[0])
    if dy > 0: positions.sort(key=lambda p: p[1], reverse=True)
    if dy < 0: positions.sort(key=lambda p: p[1])
    for x, y in positions:
        ch = board[y][x]
        nx, ny = x + dx, y + dy
        if 0 <= nx < W and 0 <= ny < H and board[ny][nx] == EMPTY:
            board[ny][nx] = ch
            board[y][x] = EMPTY
    return True
def print_text(text: str,px,py,board,H,W):
    for i, ch in enumerate(text, start=1):
        tx, ty = px + i, py
        if 0 <= tx < W and 0 <= ty < H and board[ty][tx] == EMPTY:
            board[ty][tx] = ch
    return True