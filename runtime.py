import re

from attributes import *
from base_syntax import *

from tools import *

STATEMENT_HANDLERS = {}
HANDLER_OWNERS = {}

def register(head, override=False):
    def wrapper(fn):
        old = STATEMENT_HANDLERS.get(head)
        if old is not None and old is not fn and not override:
            raise RuntimeError(
                f"语句处理器 {head!r} 已被 {old.__module__}.{old.__name__} 注册，"
                f"不能再被 {fn.__module__}.{fn.__name__} 覆盖")
        STATEMENT_HANDLERS[head] = fn
        HANDLER_OWNERS[head] = fn.__module__ + "." + fn.__name__
        return fn
    return wrapper


def execute(stmt):
    if not stmt:
        return None
    head = stmt[0]
    if len(stmt) > 3 and any(t == "." for t in stmt) and "." not in stmt[0]:
        from base_syntax import merge_dotted
        merged = merge_dotted(stmt)
        if merged != stmt:
            stmt = merged
            head = stmt[0]
    if (len(stmt) >= 4 and stmt[1] == ":" and stmt[2] == "def"):
        h = STATEMENT_HANDLERS.get("__class_def__")
        if not h:
            raise SyntaxError(f"未注册类函数处理器: {stmt}")
        return h(stmt)

    if len(stmt) >= 2 and stmt[1] == ":":
        h = STATEMENT_HANDLERS.get("__class_member__")
        if not h:
            raise SyntaxError(f"未注册类成员处理器: {stmt}")
        return h(stmt)

    if (len(stmt) >= 5 and stmt[1] == "[" and "=" in stmt):
        h = STATEMENT_HANDLERS.get("__index_assign__")
        if not h:
            raise SyntaxError(f"未注册下标赋值处理器: {stmt}")
        return h(stmt)

    if ((len(stmt) >= 3 and stmt[1] == "=" and "." in stmt[0])
            or (len(stmt) >= 5 and stmt[1] == "." and stmt[3] == "=")):
        h = STATEMENT_HANDLERS.get("__member_assign__")
        if not h:
            raise SyntaxError(f"未注册成员赋值处理器: {stmt}")
        return h(stmt)

    if (len(stmt) >= 3 and stmt[1] == "="
            and re.fullmatch(r'[A-Za-z_]\w*', stmt[0])):
        h = STATEMENT_HANDLERS.get("__assign__")
        if not h:
            raise SyntaxError(f"未注册赋值处理器: {stmt}")
        return h(stmt)
    if (len(stmt) >= 3 and stmt[1] == "(" and stmt[-1] == ")" 
            and re.fullmatch(r'[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*', stmt[0])
            and stmt[0] not in STATEMENT_HANDLERS 
            and stmt[0] not in ("while", "if", "def", "return", "len", "print", "input")):
        from advanced_syntax import eval_expr
        eval_expr(stmt)
        return None
    h = STATEMENT_HANDLERS.get(head)
    if h:
        return h(stmt)

    raise SyntaxError(f"未知语句: {stmt}")

