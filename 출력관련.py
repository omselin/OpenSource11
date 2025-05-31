def get_cursor_pos_windows():
        import ctypes
        # 핸들 가져오기
        h = ctypes.windll.kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
        # CONSOLE_SCREEN_BUFFER_INFO 구조체 정의
        class COORD(ctypes.Structure):
            _fields_ = [("X", ctypes.c_short), ("Y", ctypes.c_short)]
        class SMALL_RECT(ctypes.Structure):
            _fields_ = [("Left", ctypes.c_short), ("Top", ctypes.c_short),
                        ("Right", ctypes.c_short), ("Bottom", ctypes.c_short)]
        class CONSOLE_SCREEN_BUFFER_INFO(ctypes.Structure):
            _fields_ = [
                ("dwSize", COORD),
                ("dwCursorPosition", COORD),
                ("wAttributes", ctypes.c_ushort),
                ("srWindow", SMALL_RECT),
                ("dwMaximumWindowSize", COORD),
            ]

        csbi = CONSOLE_SCREEN_BUFFER_INFO()
        success = ctypes.windll.kernel32.GetConsoleScreenBufferInfo(h, ctypes.byref(csbi))
        if not success:
            raise ctypes.WinError()
        # 반환: (row, col)
        return csbi.dwCursorPosition.Y, csbi.dwCursorPosition.X
def 출력전처리(n:int):
    import os
    x,y=get_cursor_pos_windows()
    if x!=n:
        os.system('cls' if os.name == 'nt' else 'clear')
        return False
    else:
        print("\033[1;1H", end='')
        return True
def move_cursor_ansi(row: int, col: int):
    import sys
    """
    ANSI CSI 시퀀스로 커서를 (row, col) 위치로 이동.
    행(row)과 열(col)은 1부터 시작합니다.
    """
    sys.stdout.write(f"\x1b[{row};{col}H")
    sys.stdout.flush()