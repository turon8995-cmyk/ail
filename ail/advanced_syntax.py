import re
import sys
from attributes import *
from base_syntax import merge_dotted, split_statements,split_args
from tools import *
from runtime import register, execute
from py_import import call_python
from nn.nn_state import *

#算
def num(nums):
    token = nums[:]

    def two(t):
        i = 0
        while i < len(t):
            if t[i] in ("+", "-") and 0 < i < len(t) - 1:
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
            if t[i] in ("*", "/") and 0 < i < len(t) - 1:
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

def literal(tokens):
    open_ch, close_ch = ("[", "]") if tokens[0] == "[" else ("{", "}")
    if tokens[-1] != close_ch:
        raise SyntaxError(f"数组不完整: {tokens}")
    inner = tokens[1:-1]
    if not inner:
        return []
    return [eval_expr(part) for part in split_args(inner)]

def _eval_index(tokens):
    from tools import find_matching
    i = 0
    while i < len(tokens):
        if tokens[i] == "[":
            if i == 0 or not re.fullmatch(r'[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*',
                                         tokens[i-1]):
                raise SyntaxError(f"下标目标错误: {tokens}")
            end = find_matching(tokens, i, "[", "]")
            name = tokens[i-1]
            index = eval_expr(tokens[i+1:end])
            value = get_value(TYPE_dictionary, name)
            if isinstance(value, str) and value.startswith("@inst") and value[5:].isdigit():
                value = pa.INSTANCE_STORE.get(int(value[5:]))
            if not isinstance(value, (list, str)):
                raise TypeError(f"{name} 不能下标访问: {tokens}")
            try:
                item = value[int(float(index))]
            except IndexError:
                raise IndexError(f"下标越界: {name}[{index}]")
            tokens = tokens[:i-1] + _value_token(item) + tokens[end+1:]
            i = 0
            continue
        i += 1
    return tokens


def _value_token(value):
    if isinstance(value, str):
        return ['"' + value + '"']
    if isinstance(value, list):
        return ["["] + _list_tokens(value)[1:-1] + ["]"]
    return [str(value)]


def _list_tokens(items):
    out = []
    for i, x in enumerate(items):
        if i:
            out.append(",")
        out.extend(_value_token(x))
    return out


def eval_expr(tokens):
    tokens = merge_dotted(tokens)
    if not tokens:
        raise SyntaxError("空表达式")

    if len(tokens) == 2 and tokens[0] == "-":
        return -eval_expr(tokens[1:])
    if len(tokens) == 2 and tokens[0] == "+":
        return eval_expr(tokens[1:])

    tokens = _eval_index(tokens)

    while True:
        found = False
        i = 0
        changed = False
        while i < len(tokens):
            if (i + 1 < len(tokens) and tokens[i+1] == "("
                    and re.fullmatch(r'[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*', tokens[i])
                    and (tokens[i] in FUNCTION_dictionary
                         or tokens[i] in BUILTIN_FUNCTIONS
                         or tokens[i].endswith(".init")
                         or callable_method(tokens[i]))):
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
                arg_values = [_call_arg(a) for a in args]
                if tokens[i] in BUILTIN_FUNCTIONS and tokens[i] not in FUNCTION_dictionary:
                    result = BUILTIN_FUNCTIONS[tokens[i]](*arg_values)
                else:
                    result = call_function(tokens[i], arg_values)

                before = tokens[:]
                if isinstance(result, str):
                    tokens = tokens[:i] + ['"' + result + '"'] + tokens[j+1:]
                elif isinstance(result, list) and all(
                        isinstance(x, (int, float, str)) for x in result):
                    tokens = tokens[:i] + _list_tokens(result) + tokens[j+1:]
                elif isinstance(result, (list, dict)) or not isinstance(
                        result, (int, float, bool, type(None))):
                    pa.INSTANCE_STORE[id(result)] = result
                    tokens = tokens[:i] + [f"@inst{id(result)}"] + tokens[j+1:]
                else:
                    tokens = tokens[:i] + [str(result)] + tokens[j+1:]
                if tokens == before:
                    raise SyntaxError(f"无法求值: {tokens}")
                found = True
                break
            else:
                i += 1
        if not found:
            break

    tokens = resolve_expr(tokens)

    if len(tokens) == 1 and tokens[0].startswith("@inst"):
        return pa.INSTANCE_STORE.get(int(tokens[0][5:]))
    if len(tokens) == 1 and tokens[0] == "None":
        return None
    if len(tokens) == 1 and tokens[0] == "True":
        return True
    if len(tokens) == 1 and tokens[0] == "False":
        return False

    if tokens and (tokens[0] == "[" or tokens[0] == "{"):
        return literal(tokens)

    if any(is_string_token(t) for t in tokens):
        return eval_string(tokens)

    result = num(tokens)
    if not result:
        raise SyntaxError(f"无法求值: {tokens}")
    try:
        return float(result[0])
    except ValueError:
        raise SyntaxError(f"无法求值: {tokens}")
def _cmp_value(tokens):
    tokens = [t for t in tokens if t]
    if not tokens:
        raise SyntaxError("表达式不完整")
    if any(is_string_token(t) for t in tokens):
        return eval_string(tokens)
    if tokens[0] in ("[", "{"):
        return literal(tokens)
    return float(num(tokens)[0])


def eval_condition(tokens):
    tokens = merge_dotted(tokens)

    for op in ("==", "!=", ">=", "<=", ">", "<"):
        if op in tokens:
            i = tokens.index(op)
            left = _cmp_value(resolve_expr(tokens[:i]))
            right = _cmp_value(resolve_expr(tokens[i+1:]))
            if op in (">", "<", ">=", "<="):
                if isinstance(left, str) or isinstance(right, str):
                    if not (isinstance(left, str) and isinstance(right, str)):
                        raise SyntaxError(f"不能比较字符串和数字: {tokens}")
                else:
                    left, right = float(left), float(right)
            return {
                ">":  left >  right,
                "<":  left <  right,
                ">=": left >= right,
                "<=": left <= right,
                "==": left == right,
                "!=": left != right,
            }[op]

    value = _cmp_value(resolve_expr(tokens))
    if isinstance(value, str):
        return bool(value)
    return bool(value)
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
    return None
for _t in ("int", "float", "string"):
    register(_t)(_handle_decl)
@register("else")
def handle_else(stmt):
    raise SyntaxError(f"else 不能单独使用: {stmt}")
@register("if")
def handle_if(stmt):
    brace = stmt.index("{")
    cond_tokens = stmt[1:brace]
    close = find_matching(stmt, brace, "{", "}")
    body_tokens = stmt[brace+1:close]
    rest = stmt[close+1:]

    if eval_condition(cond_tokens):
        return _run_block(body_tokens)
    return _run_else(rest)


def _run_else(rest):
    if not rest:
        return None
    if rest[0] != "else":
        raise SyntaxError(f"if 之后只能是 else: {rest}")
    if len(rest) < 3 or rest[1] != "{":
        raise SyntaxError(f"else 格式错误: {rest}")
    return _run_block(rest[2:-1])


def _run_block(tokens):
    for sub in split_statements(tokens):
        r = execute(sub)
        if r is not None:
            return r
    return None
@register("for")
def handle_for(stmt):
    brace = stmt.index("{")
    header = stmt[1:brace]
    if len(header) < 3:
        raise SyntaxError(f"for 格式错误: {stmt}")
    var = header[0]
    start = eval_expr(header[1:-1])
    end = eval_expr(header[-1:])
    body = stmt[brace+1:-1]

    i = int(float(start))
    while i < int(float(end)):
        _bind_number(var, float(i))
        r = _run_block(body)
        if r is BREAK_SIGNAL:
            break
        if r is not None:
            return r
        i += 1
    return None


class _Break:
    def __repr__(self):
        return "<break>"


BREAK_SIGNAL = _Break()


def _bind_number(name, value):
    for table in TYPE_dictionary.values():
        if name in table:
            table[name] = value
            return
    TYPE_dictionary['int'][name] = value
@register("break")
def handle_break(stmt):
    return BREAK_SIGNAL
@register("while")
def handle_while(stmt):
    brace = stmt.index("{")
    cond_tokens = stmt[1:brace]
    body_tokens = stmt[brace+1:-1]
    while eval_condition(cond_tokens):
        r = _run_block(body_tokens)
        if r is BREAK_SIGNAL:
            break
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
    sys.stdout.write(_show(value) + "\n")
    return None


def _show(value):
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(_show(x) for x in value) + "]"
    if hasattr(value, "__dict__") and not isinstance(value, type):
        return "<" + type(value).__name__ + ">"
    return str(value)
@register("input")
def handle_input(stmt):
    if len(stmt) < 3 or stmt[1] != "(" or stmt[-1] != ")":
        raise SyntaxError(f"input 格式错误: {stmt}")
    expr = stmt[2:-1]
    value = BUILTIN_FUNCTIONS["input"]() if not expr else eval_expr(expr)
    return value
@register("__class_member__")
def handle_class_member(stmt):
    if len(stmt) < 5:
        raise SyntaxError(f"成员声明太短: {stmt}")
    class_name, typ, member, raw = stmt[0], stmt[2], stmt[3], stmt[4]
    if typ == "int":
        value = int(float(raw))
    elif typ == "train":
        TRAIN_class.setdefault(class_name, {})[member] = {
            "value": raw,
        }
        return None
    elif typ == "float":
        value = float(raw)
    elif typ == "string":
        value = raw.strip('"')
    else:
        raise SyntaxError(f"未知类型: {typ}")
    CLASS_dictionary.setdefault(class_name, {})[member] = {
        "type": typ, "value": value,
    }
    return None
@register("__class_def__")
def handle_class_def(stmt):
    class_name = stmt[0]
    body = stmt[2:]
    paren = extract_groups(body, "(", ")")
    if not paren:
        raise SyntaxError(f"类函数缺少参数: {stmt}")
    _, _, params_tokens = paren[0]
    params = [p for p in params_tokens if p != ","]

    braces = extract_groups(body, "{", "}")
    if not braces:
        raise SyntaxError(f"类函数缺少 body: {stmt}")
    _, _, func_body = braces[-1]

    name = stmt[3]
    FUNCTION_dictionary[class_name + "." + name] = {
        "params": params,
        "body": func_body,
        "decorator": None,
        "owner": class_name,
    }
    CLASS_dictionary.setdefault(class_name, {})[name] = {
        "type": "def", "value": FUNCTION_dictionary[class_name + "." + name],
    }
    return None


def instance_of(class_name):
    if class_name not in CLASS_dictionary:
        raise NameError(f"未定义类: {class_name}")
    out = {}
    for member, entry in CLASS_dictionary[class_name].items():
        if entry.get("type") == "def":
            continue
        value = entry.get("value")
        out[member] = {"type": entry.get("type"), "value": value}
    return out
@register("__assign__")
def handle_assign(stmt):
    name = stmt[0]
    expr = merge_dotted(stmt[2:])
    if expr and all(is_string_token(t) or t == "+" for t in expr):
        value = eval_string(expr)
    elif expr and expr[0] in ("[", "{"):
        value = literal(expr)
    elif (len(expr) >= 3 and expr[-1] == ")" and expr[-2] == "("
          and expr[0].endswith(".init")):
        value = instance_of(expr[0][:-5])
    else:
        value = eval_expr(expr)
    if isinstance(value, dict) and any(
            isinstance(v, dict) and "value" in v for v in value.values()):
        pa.INSTANCE_STORE[id(value)] = value
        value = f"@inst{id(value)}"
    for typ, table in TYPE_dictionary.items():
        if name in table:
            table[name] = value
            return None
    TYPE_dictionary['int'][name] = value
    return None
@register("__member_assign__")
def handle_member_assign(stmt):
    if stmt[1] == ".":
        obj, member = stmt[0], stmt[2]
        value = eval_expr(stmt[4:])
    else:
        obj, member = stmt[0].split(".", 1)
        value = eval_expr(stmt[2:])
    inst = get_value(TYPE_dictionary, obj)
    if isinstance(inst, str) and inst.startswith("@inst") and inst[5:].isdigit():
        inst = pa.INSTANCE_STORE.get(int(inst[5:]))
    if isinstance(inst, dict) and member in inst:
        if isinstance(inst[member], dict) and "value" in inst[member]:
            inst[member]["value"] = value
            return None
    if isinstance(inst, dict):
        inst[member] = {"type": "any", "value": value}
        return None
    if obj in CLASS_dictionary and member in CLASS_dictionary[obj]:
        CLASS_dictionary[obj][member]["value"] = value
        return None
    raise NameError(f"无法赋值: {stmt}")
@register("__index_assign__")
def handle_index_assign(stmt):
    from tools import find_matching
    name = stmt[0]
    end = find_matching(stmt, 1, "[", "]")
    index = int(float(eval_expr(stmt[2:end])))
    value = eval_expr(stmt[end+2:])
    target = get_value(TYPE_dictionary, name)
    if isinstance(target, str) and target.startswith("@inst") and target[5:].isdigit():
        target = pa.INSTANCE_STORE.get(int(target[5:]))
    if not isinstance(target, list):
        raise TypeError(f"{name} 不是数组，不能下标赋值")
    try:
        target[index] = value
    except IndexError:
        raise IndexError(f"下标越界: {name}[{index}]")
    return None
#执行函数
import attributes as pa

def nearest_return(name):
    fn = FUNCTION_dictionary.get(name)
    if fn is None:
        return None
    if fn.get("source") is not None:
        value = pa.last_return.get(fn["source"])
    else:
        value = pa.last_return.get(name)
    if value is not None:
        return value
    return pa.last_value


def _call_arg(tokens):
    tokens = [t for t in tokens if t]
    if not tokens:
        return None
    if len(tokens) == 1 and re.fullmatch(r'[A-Za-z_]\w*', tokens[0]):
        value = get_value(TYPE_dictionary, tokens[0])
        if value is None:
            return tokens[0]
        return value
    return eval_expr(tokens)


def callable_method(name):
    if "." not in name:
        return False
    head, method = name.rsplit(".", 1)
    target = get_value(TYPE_dictionary, head)
    if isinstance(target, str) and target.startswith("@inst") and target[5:].isdigit():
        target = pa.INSTANCE_STORE.get(int(target[5:]))
    return isinstance(target, list) and method == "forward"


def forward_network(net, x=None):
    if not net:
        return None
    if x is None or isinstance(x, str) or not isinstance(x, (list, int, float)):
        try:
            import numpy as _np
            size = net[0].w.shape[0]
            x = _np.random.randn(1, size)
        except Exception:
            return net
    else:
        import numpy as _np
        if not isinstance(x, list):
            x = [x]
        if x and isinstance(x[0], (int, float)):
            x = [x]
        x = _np.array(x, dtype=float)
    for i, layer in enumerate(net):
        activate = i != len(net) - 1
        if not hasattr(layer, "forward"):
            raise TypeError(f"第 {i} 层没有 forward 方法")
        x = layer.forward(x, activate)
    return x.tolist()


def _instantiate(class_path, args):
    from py_import import import_python_class

    parts = class_path.split(".")
    if len(parts) == 2:
        namespace, class_name = parts
        cls = import_python_class(namespace, class_name)
        if cls is not None:
            if args and len(args) == 1 and isinstance(args[0], str):
                shape = _shape_rows(args[0])
                if shape is not None:
                    return [cls(i, o) for i, o in shape]
            try:
                return cls(*args)
            except TypeError:
                return cls
        if class_name in CLASS_dictionary:
            return instance_of(class_name)
    elif class_path in CLASS_dictionary:
        return instance_of(class_path)

    raise NameError(f"未定义类: {class_path}")


def _shape_rows(name):
    import nn.nn_state as ns
    if hasattr(ns, "LAYER_dictionary") and name in ns.LAYER_dictionary:
        return ns.LAYER_dictionary[name]
    from attributes import LAYER_dictionary as ld
    return ld.get(name)


def call_function(name, args):
    global last_value
    if name.endswith(".init"):
        result = _instantiate(name[:-5], args)
        pa.last_value = result
        pa.last_return[name] = result
        return result

    if "." in name:
        head, method = name.rsplit(".", 1)
        target = get_value(TYPE_dictionary, head)
        if isinstance(target, str) and target.startswith("@inst") and target[5:].isdigit():
            target = pa.INSTANCE_STORE.get(int(target[5:]))
        if isinstance(target, list) and method == "forward":
            result = forward_network(target, args[0] if args else None)
            pa.last_value = result
            pa.last_return[name] = result
            return result

    fn = pa.FUNCTION_dictionary.get(name)
    if fn is None:
        raise NameError(f"未定义函数: {name}")

    if fn.get("python") is not None:
        result = call_python(fn["python"], args)
        pa.last_value = result
        pa.last_return[name] = result
        return result

    decorator = fn.get("decorator")

    if not args and len(fn["params"]) == 1:
        value = nearest_return(name)
        if value is None:
            raise TypeError(
                f"{name} 需要 1 个参数，但没有可用的上一个函数返回值")
        args = [value]

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
    if TRAIN_STATE["pending_main"]:
        TRAIN_STATE["main"] = name
        TRAIN_STATE["pending_main"] = False

    return None
@register("return")
def handle_return(stmt):
    if len(stmt) <= 1:
        return None
    expr = merge_dotted(stmt[1:])
    if all(is_string_token(t) or t == "+" for t in expr):
        return eval_string(expr)
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
