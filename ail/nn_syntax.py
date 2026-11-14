import re
import sys
from attributes import *
from base_syntax import merge_dotted, split_statements,split_args
from tools import *
from runtime import register, execute
from advanced_syntax import *
@register("&")
def handle_marker(stmt):
    kind = stmt[1] if len(stmt) > 1 else None

    if kind == "layer":
        if len(stmt) < 3:
            raise SyntaxError(f"&layer 缺少名字: {stmt}")
        pa.LAYER_STATE["pending_name"] = stmt[2]
        return None

    if kind == "train_main":
        pa.TRAIN_STATE["pending_main"] = True
        return None

    if kind == "train_finish":
        pa.TRAIN_STATE["pending_finish"] = True
        return None

    raise SyntaxError(f"未知 & 标记: {stmt}")
@register("layer")
def handle_layer_block(stmt):
    name = pa.LAYER_STATE["pending_name"]
    if name is None:
        raise SyntaxError(f"layer 块缺少 &layer 标记: {stmt}")

    # 取 {} 内的体
    body = extract_body(stmt, "{", "}")
    if body is None:
        raise SyntaxError(f"layer 缺少 body: {stmt}")

    # 解析 50,60 60,30
    rows = []
    i = 0
    while i < len(body):
        a = body[i]
        if i + 2 < len(body) and body[i+1] == ",":
            b = body[i+2]
            rows.append((int(float(a)), int(float(b))))
            i += 3
        else:
            i += 1

    pa.LAYER_dictionary[name] = rows
    pa.LAYER_STATE["pending_name"] = None 
    return None
@register("save")
def handle_save(stmt):
    path_tokens = stmt[2:-1]
    path = eval_string(resolve_expr(path_tokens))

    if pa.TRAIN_STATE["pending_finish"]:
        pa.TRAIN_STATE["finish_callbacks"].append(lambda p=path: real_save(p))
        pa.TRAIN_STATE["pending_finish"] = False
    else:
        real_save(path)
    return None
def real_save(path):
    print(f"[save] {path}")