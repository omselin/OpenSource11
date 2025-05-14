import re
from typing import Any, Optional

class VariableMap:
    def __init__(self):
        self.variables: dict[str, Any] = {}

    def set_variable(self, name: str, value: Any) -> None:
        self.variables[name] = value

    def get_value(self, text: str) -> Optional[Any]:
        """
        - 문자열 리터럴('...', "...")
        - 숫자 리터럴
        - 변수명 조회
        - 수식 및 조건식: &&, ||, (), >, <, ==, !=, +, -, *, / 등
        문법 오류가 나면 SyntaxError를 발생시킨다.
        """
        txt = text.strip()

        # ───── 리터럴 및 변수 조회 ─────
        if (txt.startswith('"') and txt.endswith('"')) or (txt.startswith("'") and txt.endswith("'")):
            return txt[1:-1]                                  # 문자열
        if re.fullmatch(r"-?\d+", txt):
            return int(txt)                                   # 정수
        if txt in self.variables:
            return self.variables[txt]                        # 변수

        # ───── 토큰화 ─────
        token_spec = [
    ('NUMBER',   r"\d+"),      # <- 양의 정수만
    ('AND',      r"&&"),
    ('OR',       r"\|\|"),
    ('EQ',       r"=="),
    ('NE',       r"!="),
    ('LE',       r"<="),
    ('GE',       r">="),
    ('LT',       r"<"),
    ('GT',       r">"),
    ('PLUS',     r"\+"),
    ('MINUS',    r"-"),
    ('STAR',     r"\*"),
    ('SLASH',    r"/"),
    ('LPAREN',   r"\("),
    ('RPAREN',   r"\)"),
    ('VAR',      r"[A-Za-z_]\w*"),
    ('SKIP',     r"[ \t]+"),
    ('MISMATCH', r"."),
]
        tok_regex = '|'.join(f"(?P<{n}>{p})" for n, p in token_spec)

        tokens = []
        for mo in re.finditer(tok_regex, txt):
            kind = mo.lastgroup
            value = mo.group()
            if kind == 'SKIP':
                continue
            if kind == 'MISMATCH':
                raise SyntaxError(f"잘못된 토큰: {value!r}")
            tokens.append((kind, value))
        tokens.append(('EOF', ''))

        # ───── 파서 ─────
        idx = 0
        def peek(): return tokens[idx][0]
        def advance():
            nonlocal idx
            tok = tokens[idx]
            idx += 1
            return tok

        # primary → (expr) | NUMBER | VAR | +primary | -primary
        def parse_primary():
            tok = peek()
            if tok == 'LPAREN':
                advance()
                val = parse_expr()
                if peek() != 'RPAREN':
                    raise SyntaxError("')' 누락")
                advance()
                return val

            t, v = advance()
            if t == 'NUMBER':
                return int(v)
            if t == 'VAR':
                return self.variables.get(v, 0)
            if t in ('PLUS', 'MINUS'):
                val = parse_primary()
                return +val if t == 'PLUS' else -val
            raise SyntaxError("잘못된 수식 요소")

        # term   → primary ( (*|/) primary )*
        def parse_term():
            val = parse_primary()
            while peek() in ('STAR', 'SLASH'):
                op, _ = advance()
                rhs = parse_primary()
                val = val * rhs if op == 'STAR' else val / rhs
            return val

        # arith  → term ( (+|-) term )*
        def parse_arith():
            val = parse_term()
            while peek() in ('PLUS', 'MINUS'):
                op, _ = advance()
                rhs = parse_term()
                val = val + rhs if op == 'PLUS' else val - rhs
            return val

        # compare → arith ( == | != | < | > | <= | >= arith )?
        def parse_compare():
            left = parse_arith()
            if peek() in ('EQ', 'NE', 'LT', 'GT', 'LE', 'GE'):
                op, _ = advance()
                right = parse_arith()
                ops = {
                    'EQ': left == right,
                    'NE': left != right,
                    'LT': left < right,
                    'GT': left > right,
                    'LE': left <= right,
                    'GE': left >= right
                }
                return ops[op]
            return left

        # and    → compare (&& compare)*
        def parse_and():
            val = parse_compare()
            while peek() == 'AND':
                advance()
                rhs = parse_compare()
                val = bool(val) and bool(rhs)
            return val

        # expr   → and (|| and)*
        def parse_expr():
            val = parse_and()
            while peek() == 'OR':
                advance()
                rhs = parse_and()
                val = bool(val) or bool(rhs)
            return val

        result = parse_expr()
        if peek() != 'EOF':
            raise SyntaxError("분석되지 않은 잔여 토큰 존재")
        return result

# 사용 예:
# vm = VariableMap()
# vm.set_variable('x',5)
# vm.get_value('x>3 && (x<10 || x==2)')
