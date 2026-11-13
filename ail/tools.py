import attributes as pa
from base_syntax import merge_dotted
#变量替换
def resolve_expr(expr):
    expr = merge_dotted(expr)
    out = []
    for t in expr:
        v = get_value(pa.TYPE_dictionary, t)
        if v is None:
            out.append(t)
        elif isinstance(v, str):
            out.append(f'"{v}"')
        else:
            out.append(str(v))
    return out
def len_str(tokens):
    i = 0
    for i in str(tokens):
        i+=1
    return i
#语句里是否含特定符号
def has_symbol(stmt,symbol):
    return symbol in stmt
#传入变量表与名
def get_value(env, name):
    for local in reversed(pa.CALL_STACK):
        if name in local:
            return local[name]
    # 再查全局
    for typ, table in env.items():
        if name in table:
            return table[name]
    if "." in name:
        cls, member = name.split(".", 1)
        if cls in pa.CLASS_dictionary and member in pa.CLASS_dictionary[cls]:
            return pa.CLASS_dictionary[cls][member]["value"]
    return None
#获取值类型
def get_type(value):
    v = get_value(pa.TYPE_dictionary, value)
    if v is not None:
        value = v
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "string"
    return "unknown"
#找出所有括号，返回其的下标
def extract_groups(tokens, open_char="(", close_char=")"):
    groups = []
    stack = []
    for i, t in enumerate(tokens):
        if t == open_char:
            stack.append(i)
        elif t == close_char:
            if not stack:
                raise SyntaxError(f"多余的 {close_char}")
            left = stack.pop()
            groups.append((left, i, tokens[left+1:i]))
    if stack:
        raise SyntaxError(f"缺少 {close_char}")
    return groups
#找配对括号下标
def find_matching(tokens, start, open_char="(", close_char=")"):
    if start >= len(tokens) or tokens[start] != open_char:
        raise SyntaxError(f"位置 {start} 不是 {open_char}: {tokens[start:start+1]}")
    depth = 0
    for i in range(start, len(tokens)):
        if tokens[i] == open_char:
            depth += 1
        elif tokens[i] == close_char:
            depth -= 1
            if depth == 0:
                return i
    raise SyntaxError(f"缺少 {close_char}: {tokens[start:]}")