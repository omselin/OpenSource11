from menu import Menu
import sys


# 열 수 있는 최대 크기 예시: 120x40 (가로 x 세로)

if __name__ == "__main__":
    # 커서 숨기기
    sys.stdout.write("\033[?25l")
    sys.stdout.flush()

    menu = Menu("mapdata.json")
    menu.run()