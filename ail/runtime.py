import re

from attributes import *
from base_syntax import *

from tools import *

STATEMENT_HANDLERS = {}

def register(head):
    def wrapper(fn):
        STATEMENT_HANDLERS[head] = fn
        return fn
    return wrapper


def execute(stmt):
    if not stmt:
        return None
    head = stmt[0]
    if len(stmt) >= 2 and stmt[1] == ":":
        h = STATEMENT_HANDLERS.get("__class_member__")
        if not h:
            raise SyntaxError(f"未注册类成员处理器: {stmt}")
        return h(stmt)

    if (len(stmt) >= 3 and stmt[1] == "="
            and re.fullmatch(r'[A-Za-z_]\w*', stmt[0])):
        h = STATEMENT_HANDLERS.get("__assign__")
        if not h:
            raise SyntaxError(f"未注册赋值处理器: {stmt}")
        return h(stmt)
    if (len(stmt) >= 3 and stmt[1] == "(" and stmt[-1] == ")" 
            and re.fullmatch(r'[A-Za-z_]\w*', stmt[0])
            and stmt[0] not in STATEMENT_HANDLERS 
            and stmt[0] not in ("while", "if", "def", "return", "len", "print", "input")):
        from advanced_syntax import eval_expr
        eval_expr(stmt)
        return None
    h = STATEMENT_HANDLERS.get(head)
    if h:
        return h(stmt)

    raise SyntaxError(f"未知语句: {stmt}")

def src(text):
    tokens = tokenize(text)
    stmts = split_statements(tokens)
    for stmt in stmts:
        execute(stmt)
if __name__ == '__main__':
    from advanced_syntax import *   
    # 测试
    src('''
def x(num) {
    return num + 1
}
@x@
def d(x) {
    return x + 1
}
x(1)
print(d())
    ''')
