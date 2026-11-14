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
    for i, stmt in enumerate(stmts):
        if stmt[0] == "&":
            kind = stmt[1] if len(stmt) > 1 else None
            if kind == "layer":
                if i + 1 >= len(stmts) or stmts[i+1][0] != "layer":
                    raise SyntaxError(f"&layer 后必须是 layer 块: {stmt}")
            elif kind == "train_main":
                if i + 1 >= len(stmts) or stmts[i+1][0] != "def":
                    raise SyntaxError(f"&train_main 后必须是 def: {stmt}")
            elif kind == "train_finish":
                if i + 1 >= len(stmts):
                    raise SyntaxError(f"&train_finish 后必须是一条语句: {stmt}")
        execute(stmt)
if __name__ == '__main__':
    from nn_syntax import *
    from advanced_syntax import *   
    # 测试
    src('''
&layer xx
layer{
50,60
60,30
}

&train_main
def train() {
    print("训练中")
}

print("完成")
    ''')
