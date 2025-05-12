import command_executer as ce  


EMPTY, PLAYER_CHAR = ' ', ';'
DIR = {'UP': (0, -1), 'DOWN': (0, 1), 'LEFT': (-1, 0), 'RIGHT': (1, 0)}

def get_value(variable_map:dict,text):
    if text.startswith('"') and text.endswith('"') and len(text) >= 2:
        return text[1:-1]
    elif text in variable_map:
        return variable_map[text]
    else:
        try:
            return int(text)
        except ValueError:
            return None
def parse_and_execute_command(last_dir, board,variable_map:dict,code, H, W, px, py):
    if code == 'return':
        return False
    # move("..."), 문자열 길이 2 이상 지원
    if code.startswith('move(') and code.endswith(')'):
        arg = code[6:-1]
        text=get_value(variable_map,arg)
        dx, dy = last_dir
        # 이동 대상 문자 위치 수집
        return ce.move(text, dx, dy, board, H, W)
    # print("..."), 인용부호 처리
    if code.startswith('print(') and code.endswith(')'):
        arg = code[6:-1]
        text=get_value(variable_map,arg)
        if text is None:
            raise ValueError(f"Invalid value '{arg}'.")
        return ce.print_text(text, px, py, board, H, W)
    if '=' in code:
        # 변수 대입 처리
        operand_list = code.split('=', 1)
        last= operand_list[-1]
        value= get_value(variable_map,last)
        if value is None:
            raise ValueError(f"Invalid value '{last}'.")
        return ce.assignment(variable_map,operand_list[:-1],value)
        

                
        
    return True