import os
import sys
import json
from map_module import Map
from game import Game
from typing import Dict, Any
import 출력관련


# ────────── 키 입력 처리 (Windows / Unix) ──────────
try:
    import msvcrt
    def get_key():
        ch = msvcrt.getwch()
        if ch == '\xe0':  # 화살표 키
            ch2 = msvcrt.getwch()
            return {'H': 'UP', 'P': 'DOWN', 'K': 'LEFT', 'M': 'RIGHT'}.get(ch2, '')
        return ch
    def key_pressed():
        return msvcrt.kbhit()
except ImportError:
    import tty, termios, select
    def get_key():
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
            if ch == '\x1b':  # 화살표 키 시작
                seq = sys.stdin.read(2)
                return {'[A': 'UP', '[B': 'DOWN', '[D': 'LEFT', '[C': 'RIGHT'}.get(seq, '')
            return ch
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
    def key_pressed():
        dr, _, _ = select.select([sys.stdin], [], [], 0)
        return bool(dr)

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

class Menu:
    def __init__(self, mapdata_file: str = "mapdata.json"):
        """
        mapdata_file: 경로 to JSON file for persistence
        """
        self.mapdata_file = mapdata_file
        # 파일에서 직접 맵 데이터 로드
        try:
            with open(self.mapdata_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"맵 데이터 로드 실패: {e}")
            sys.exit(1)

        # JSON 구조를 내부 dict로 변환
        self.maps: Dict[str, Dict[str, Any]] = {}
        for m in data.get('maps', []):
            name = m.get('name')
            if not name:
                continue
            self.maps[name] = {
                'data': m.get('data', []),
                'locked': m.get('locked', True),
                'returnValue': m.get('returnValue', None)
            }
        self.titles = list(self.maps.keys())
        self.current = 0
        # 화면에 표시할 윈도우 범위
        self.window_start = 0
        self.page_size = 10

    def _unlock_next(self):
        next_idx = self.current + 1
        if next_idx < len(self.titles):
            nxt = self.titles[next_idx]
            if self.maps[nxt].get('locked', True):
                self.maps[nxt]['locked'] = False
                # 파일 업데이트
                try:
                    with open(self.mapdata_file, 'r+', encoding='utf-8') as f:
                        data = json.load(f)
                        for entry in data.get('maps', []):
                            if entry.get('name') == nxt:
                                entry['locked'] = False
                                break
                        f.seek(0)
                        json.dump(data, f, ensure_ascii=False, indent=2)
                        f.truncate()
                except Exception as e:
                    print(f"맵 데이터 업데이트 실패: {e}")

    def run(self):
        total = len(self.titles)
        clear()
        while True:
            출력관련.출력전처리(13)
            print("=== 맵 선택 ===")
            # 현재 윈도우 범위에 해당하는 맵만 출력
            end = self.window_start + self.page_size
            display = self.titles[self.window_start:end]
            for idx, title in enumerate(display):
                global_idx = self.window_start + idx
                item = self.maps[title]
                sel = "▶" if global_idx == self.current else "  "
                lock = " [Locked]" if item.get('locked', False) else ""
                print(f"{sel} {title}{lock}                    ")         
            print("\n↑/↓: 이동    →: 선택    Q: 종료")

            # 키 입력 대기
            while not key_pressed():
                pass
            ch = get_key()
            if ch.lower() == 'q':
                return

            if ch == 'UP':
                if self.current > 0:
                    self.current -= 1
                    # 윈도우 위로 스크롤
                    if self.current < self.window_start:
                        self.window_start = max(0, self.window_start - 1)
            elif ch == 'DOWN':
                if self.current < total - 1:
                    self.current += 1
                    # 윈도우 아래로 스크롤
                    if self.current >= self.window_start + self.page_size:
                        max_start = max(0, total - self.page_size)
                        self.window_start = min(self.window_start + 1, max_start)
            elif ch == 'RIGHT':
                # 현 위치 맵 실행
                while True:
                    title = self.titles[self.current]
                    item = self.maps[title]
                    if item.get('locked', False):
                        break
                    try:
                        map_inst = Map(title,item['data'], item['returnValue'])
                        r = Game(map_inst).start()
                    except RecursionError as e:
                        input(f"맵 로드 실패: {e}")
                        break

                    
                    # 클리어 후 다음 맵 잠금 해제
                    self._unlock_next()
                    if not r:
                        break
                    # 다음 인덱스로 이동
                    # 다음 맵이 없거나 잠겨있으면 중단
                    if self.current+1 >= total or self.maps[self.titles[self.current+1]].get('locked', False):
                        break
                    self.current += 1
                if self.window_start+self.page_size <= self.current:
                    self.window_start = self.current+1 - self.page_size
                # 메뉴로 복귀
                clear()
                continue
