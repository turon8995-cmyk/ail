import re
import sys
from attributes import *
from base_syntax import merge_dotted, split_statements,split_args
from tools import *
from runtime import register, execute
from advanced_syntax import *
from .nn_state import *
@register("&")
def handle_marker(stmt):
    kind = stmt[1] if len(stmt) > 1 else None

    if kind == "layer":
        if len(stmt) < 3:
            raise SyntaxError(f"&layer 缺少名字: {stmt}")
        LAYER_STATE["pending_name"] = stmt[2]
        return None

    if kind == "train_main":
        TRAIN_STATE["pending_main"] = True
        return None

    if kind == "train_finish":
        TRAIN_STATE["pending_finish"] = True
        return None

    raise SyntaxError(f"未知 & 标记: {stmt}")
@register("{")
@register("layer")
def handle_layer_block(stmt):
    name = LAYER_STATE["pending_name"]
    if name is None:
        raise SyntaxError(f"layer 块缺少 &layer 标记: {stmt}")

    if stmt[0] == "{":
        body = stmt[1:-1]
    else:
        body = stmt[2:-1]
    if not body:
        raise SyntaxError(f"layer 缺少 body: {stmt}")

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
    LAYER_dictionary[name] = rows
    LAYER_STATE["pending_name"] = None
    return None
@register("save")
def handle_save(stmt):
    path_tokens = stmt[2:-1]
    path = eval_string(resolve_expr(path_tokens))

    if TRAIN_STATE["pending_finish"]:
        TRAIN_STATE["finish_callbacks"].append(lambda p=path: real_save(p))
        TRAIN_STATE["pending_finish"] = False
    else:
        real_save(path)
    return None
def real_save(path):
    print(f"[save] {path}")
@register("train")
def handle_train(stmt):
    if len(stmt) < 3:
        raise SyntaxError(f"格式错误: {stmt}")
    name, raw = stmt[1], stmt[2]
    TYPE_dictionary['train'][name] = raw
