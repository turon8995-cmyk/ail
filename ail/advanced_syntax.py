import re
import sys
from attributes import *
from base_syntax import merge_dotted, split_statements,split_args
from tools import *
from runtime import register, execute


#算
def num(nums):
    token = nums[:]

    def two(t):
        i = 0
        while i < len(t):
            if t[i] in ("+", "-"):
                a = float(t[i-1]); b = float(t[i+1])
                r = a + b if t[i] == "+" else a - b
                t[i-1:i+2] = [str(r)]
                i = max(i - 1, 0)
            else:
                i += 1
        return t

    def one(t):
        i = 0
        while i < len(t):
            if t[i] in ("*", "/"):
                a = float(t[i-1]); b = float(t[i+1])
                if t[i] == "/" and b == 0:
                    raise ZeroDivisionError("0不能被除")
                r = a * b if t[i] == "*" else a / b
                t[i-1:i+2] = [str(r)]
                i = max(i - 1, 0)
            else:
                i += 1
        return two(t)

    stack, i = [], 0
    while i < len(token):
        if token[i] == "(":
            stack.append(i); i += 1
        elif token[i] == ")":
            if not stack:
                raise SyntaxError("多余）")
            left = stack.pop()
            inner = token[left+1:i]
            token[left:i+1] = one(inner)
            i = left + 1
        else:
            i += 1
    if stack:
        raise SyntaxError("缺少 )")
    return one(token)
#是字符串
def is_string_token(t):
    return bool(re.fullmatch(r'"[^"]*"', t))
#字符串操作
def eval_string(tokens):
    parts = []
    for t in tokens:
        if t == "+":
            continue
        if is_string_token(t):
            parts.append(t[1:-1])
        elif re.fullmatch(r'\d+\.?\d*', t):
            parts.append(t)
        else:
            v = get_value(TYPE_dictionary, t)
            if v is None:
                raise NameError(f"未定义变量: {t}")
            parts.append(str(v))
    return "".join(parts)

def eval_expr(tokens):
    tokens = merge_dotted(tokens)
    if not tokens:
        raise SyntaxError("空表达式")

    while True:
        found = False
        i = 0
        while i < len(tokens):
            if (i + 1 < len(tokens) and tokens[i+1] == "("
                    and re.fullmatch(r'[A-Za-z_]\w*', tokens[i])
                    and tokens[i] in FUNCTION_dictionary):
                # 找配对 )
                depth = 0
                j = i + 1
                while j < len(tokens):
                    if tokens[j] == "(":
                        depth += 1
                    elif tokens[j] == ")":
                        depth -= 1
                        if depth == 0:
                            break
                    j += 1
                if depth != 0:
                    raise SyntaxError(f"括号不配对: {tokens}")

                arg_tokens = tokens[i+2:j]
                args = split_args(arg_tokens)
                arg_values = [eval_expr(a) for a in args]
                result = call_function(tokens[i], arg_values)

                tokens = tokens[:i] + [str(result)] + tokens[j+1:]
                found = True
                break
            else:
                i += 1
        if not found:
            break

    tokens = resolve_expr(tokens)

    if any(is_string_token(t) for t in tokens):
        return eval_string(tokens)

    result = num(tokens)
    if not result:
        raise SyntaxError(f"无法求值: {tokens}")
    try:
        return float(result[0])
    except ValueError:
        raise SyntaxError(f"无法求值: {tokens}")
def eval_condition(tokens):
    tokens = merge_dotted(resolve_expr(tokens))

    for op in (">=", "<=", "==", "!=", ">", "<"):
        if op in tokens:
            i = tokens.index(op)
            left_list  = num(tokens[:i])
            right_list = num(tokens[i+1:])

            if not left_list or not right_list:
                raise SyntaxError(f"表达式不完整: {tokens}")
            try:
                left  = float(left_list[0])
                right = float(right_list[0])
            except ValueError:
                raise SyntaxError(f"暂不支持非数字: {tokens}")

            return {
                ">":  left >  right,
                "<":  left <  right,
                ">=": left >= right,
                "<=": left <= right,
                "==": left == right,
                "!=": left != right,
            }[op]

    result = num(tokens)
    if not result:
        raise SyntaxError(f"条件为空: {tokens}")
    try:
        return bool(float(result[0]))
    except ValueError:
        raise SyntaxError(f"暂不支持非数字: {tokens}")
#语法
@register("len")
def handle_len(stmt):
    if len(stmt) < 3 or stmt[1] != "(" or stmt[-1] != ")":
        raise SyntaxError(f"格式错误: {stmt}")
    inner = stmt[2:-1]
    if any(is_string_token(t) for t in inner):
        s = eval_string(inner)
    else:
        s = str(num(resolve_expr(inner))[0])
    return None
def _handle_decl(stmt):
    if len(stmt) < 3:
        raise SyntaxError(f"格式错误: {stmt}")
    head = stmt[0]
    name, raw = stmt[1], stmt[2]
    if head == "int":
        TYPE_dictionary['int'][name] = int(float(raw))
    elif head == "float":
        TYPE_dictionary['float'][name] = float(raw)
    elif head == "string":
        TYPE_dictionary['string'][name] = raw.strip('"')
    elif head == "train":
        TYPE_dictionary['train'][name] = raw
    return None
for _t in ("int", "float", "string", "train"):
    register(_t)(_handle_decl)
@register("if")
def handle_if(stmt):
    brace = stmt.index("{")
    cond_tokens = stmt[1:brace]
    body_tokens = stmt[brace+1:-1]
    if eval_condition(cond_tokens):
        for sub in split_statements(body_tokens):
            r = execute(sub)
            if r is not None:
                return r
    return None
@register("while")
def handle_while(stmt):
    brace = stmt.index("{")
    cond_tokens = stmt[1:brace]
    body_tokens = stmt[brace+1:-1]
    while eval_condition(cond_tokens):
        for sub in split_statements(body_tokens):
            r = execute(sub)
            if r is not None:
                return r
    return None
@register("print")
def handle_print(stmt):
    if len(stmt) < 3 or stmt[1] != "(" or stmt[-1] != ")":
        raise SyntaxError(f"print 格式错误: {stmt}")
    expr = stmt[2:-1]
    if not expr:
        sys.stdout.write("\n")
        return None
    value = eval_expr(expr)
    sys.stdout.write(str(value) + "\n")
    return None
@register("__class_member__")
def handle_class_member(stmt):
    if len(stmt) < 5:
        raise SyntaxError(f"成员声明太短: {stmt}")
    class_name, typ, member, raw = stmt[0], stmt[2], stmt[3], stmt[4]
    if typ == "int":
        value = int(float(raw))
    elif typ == "float":
        value = float(raw)
    elif typ == "string":
        value = raw.strip('"')
    elif typ == "train":
        value = raw
    else:
        raise SyntaxError(f"未知类型: {typ}")
    CLASS_dictionary.setdefault(class_name, {})[member] = {
        "type": typ, "value": value,
    }
    return None
@register("__assign__")
def handle_assign(stmt):
    name = stmt[0]
    value = float(num(resolve_expr(stmt[2:]))[0])
    for typ, table in TYPE_dictionary.items():
        if name in table:
            table[name] = value
            return None
    TYPE_dictionary['int'][name] = value
    return None
#执行函数
import attributes as pa

def call_function(name, args):
    global last_value
    fn = pa.FUNCTION_dictionary.get(name)
    if fn is None:
        raise NameError(f"未定义函数: {name}")

    decorator = fn.get("decorator")

    if not args and pa.last_value is not None:
        args = [pa.last_value]

    params = fn["params"]
    body   = fn["body"]
    if len(params) != len(args):
        raise TypeError(f"{name} 需要 {len(params)} 个参数，给了 {len(args)}")

    local = dict(zip(params, args))
    pa.CALL_STACK.append(local)

    result = None
    try:
        for sub in split_statements(body):
            r = execute(sub)
            if r is not None:
                result = r
                break
    finally:
        pa.CALL_STACK.pop()

    pa.last_value = result

    if decorator and decorator[0] == "@@":
        pa.last_return[decorator[1]] = result
    pa.last_return[name] = result

    return result
@register("def")
def handle_def(stmt):
    global pending_decorator
    name = stmt[1]

    # 参数
    paren_groups = extract_groups(stmt, "(", ")")
    if not paren_groups:
        raise SyntaxError(f"def 缺少参数列表: {stmt}")
    _, _, params_tokens = paren_groups[0]
    params = [p for p in params_tokens if p != ","]

    # body
    brace_groups = extract_groups(stmt, "{", "}")
    if not brace_groups:
        raise SyntaxError(f"def 缺少 body: {stmt}")
    _, _, body = brace_groups[-1]

    FUNCTION_dictionary[name] = {
        "params": params,
        "body": body,
        "decorator": pa.DECORATOR_STATE["pending"],
    }
    pa.DECORATOR_STATE["pending"] = None

    # &train_main 认领
    if pa.TRAIN_STATE["pending_main"]:
        pa.TRAIN_STATE["main"] = name
        pa.TRAIN_STATE["pending_main"] = False

    return None
@register("return")
def handle_return(stmt):
    if len(stmt) <= 1:
        return None
    return eval_expr(stmt[1:])
@register("@")
def handle_decorator(stmt):
    global pending_decorator
    if len(stmt) == 2:
        pending_decorator = ("@", stmt[1])
    elif len(stmt) == 3 and stmt[2] == "@":
        pending_decorator = ("@@", stmt[1])
    else:
        raise SyntaxError(f"未知 @ 修饰: {stmt}")
    return None
