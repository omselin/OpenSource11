import command_executer as ce  
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from map_module import Map
    from variablemap import VariableMap

EMPTY, PLAYER_CHAR = ' ', ';'
DIR = {'UP': (0, -1), 'DOWN': (0, 1), 'LEFT': (-1, 0), 'RIGHT': (1, 0)}


def parse_and_execute_command(map:'Map',variable_map:'VariableMap',code, pos:tuple):
    if code == 'return':
        if map.returnValue is None:
            return False,True
        else:
            return True,True
    if code.startswith("return_"):
        if variable_map.get_value(code[7:])==map.returnValue:
            return False,True
        else:
            return True,True
    
    # move("..."), 문자열 길이 2 이상 지원
    if code.startswith('drop(') and code.endswith(')'):
        arg = code[5:-1]
        text=variable_map.get_value(arg)
        if text is None:
            return True,False
        # 이동 대상 문자 위치 수집
        return ce.drop(map,text)
    # print("..."), 인용부호 처리
    if code.startswith('print(') and code.endswith(')'):
        arg = code[6:-1]
        text=variable_map.get_value(arg)
        if text is None:
            return True,False
        
        return ce.print_text(map,pos,str(text))
    if '=' in code:
        # 변수 대입 처리
        operand_list = code.split('=', 1)
        last= operand_list[-1]
        value= variable_map.get_value(last)
        if value is None:
            return True,False
        return ce.assignment(variable_map,operand_list[:-1],value)
        

                
        
    return True,False