import command_executer as ce  
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from map_module import Map
    from variablemap import VariableMap


'''
명령어를 분류하고 분해만 하는 함수
처리는 command_executer.py에서 함
'''
def parse_and_execute_command(map:'Map',variable_map:'VariableMap',code, pos:tuple):
    if code == 'return':
        if map.returnValue is None:
            return False
        else:
            return True
    if code.startswith("return_"):
        if variable_map.get_value(code[7:])==map.returnValue:
            return False
        else:
            return True
    
    # move("..."), 문자열 길이 2 이상 지원
    if code.startswith('drop(') and code.endswith(')'):
        arg = code[5:-1]
        text=variable_map.get_value(arg)
        return ce.drop(map,str(text))
    # print("..."), 인용부호 처리
    if code.startswith('print(') and code.endswith(')'):
        arg = code[6:-1]
        text=variable_map.get_value(arg)
        return ce.print_text(map,pos,str(text))
    if '=' in code:
        # 변수 대입 처리
        operand_list = code.split('=')
        last= operand_list[-1]
        value= variable_map.get_value(last)
        return ce.assignment(variable_map,operand_list[:-1],value)
# ⬇️ 이호영님 작업 시작 위치 (이 아래에만 작성해 주세요. 이 주석은 나중에 병합 기준이 되므로 수정하지 마세요.)
# ⬇️ 오유민님 작업 시작 위치 (이 아래에만 작성해 주세요. 이 주석은 나중에 병합 기준이 되므로 수정하지 마세요.)
    if code.startswith('scramble(') and code.endswith(')'):
        arg = code[9:-1].strip().strip('"').strip("'")
        return ce.scramble_oh(map, [arg], None)

# ⬇️ 이기상님 작업 시작 위치 (이 아래에만 작성해 주세요. 이 주석은 나중에 병합 기준이 되므로 수정하지 마세요.)
    if code.startswith('swap(') and code.endswith(')'):
        args = code[5:-1]
        a, b = [x.strip().strip("'") for x in args.split(",")]
        return ce.swap(map, [a, b], None)
    if code.startswith('delete(') and code.endswith(')'):
        arg = code[7:-1].strip()

        # 문자열이면 따옴표 제거
        if (arg.startswith("'") and arg.endswith("'")) or (arg.startswith('"') and arg.endswith('"')):
            char = arg[1:-1]
        else:
            char = variable_map.get_value(arg)

        return ce.delete(map, [char], None)
# ⬇️ 이현우님 작업 시작 위치 (이 아래에만 작성해 주세요. 이 주석은 나중에 병합 기준이 되므로 수정하지 마세요.)
# ⬇️ Farhan Latiff님 작업 시작 위치 (이 아래에만 작성해 주세요. 이 주석은 나중에 병합 기준이 되므로 수정하지 마세요.)


                
        
    raise SyntaxError(f"Unknown command: {code}")