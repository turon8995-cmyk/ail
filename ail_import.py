import os

import attributes as pa
from runtime import register
from py_import import import_python, resolve


def src_file(path):
    from base_syntax import tokenize, split_statements
    from runtime import execute
    with open(path, encoding="utf-8") as f:
        text = f.read()
    for stmt in split_statements(tokenize(text)):
        execute(stmt)


def run_isolated(path):
    saved_types = pa.TYPE_dictionary
    saved_funcs = pa.FUNCTION_dictionary
    saved_classes = pa.CLASS_dictionary
    saved_current = pa.IMPORT_STATE["current"]
    saved_value = pa.last_value
    fresh_types = {k: {} for k in saved_types}
    fresh_funcs = {}
    fresh_classes = {}
    pa.TYPE_dictionary = fresh_types
    pa.FUNCTION_dictionary = fresh_funcs
    pa.CLASS_dictionary = fresh_classes
    pa.last_value = None
    _push_bindings(fresh_types, fresh_funcs, fresh_classes)
    pa.IMPORT_STATE["current"] = os.path.dirname(os.path.abspath(path))
    try:
        src_file(path)
    finally:
        _pop_bindings(saved_types, saved_funcs, saved_classes)
        pa.TYPE_dictionary = saved_types
        pa.FUNCTION_dictionary = saved_funcs
        pa.CLASS_dictionary = saved_classes
        pa.last_value = saved_value
        pa.IMPORT_STATE["current"] = saved_current
    return fresh_types, fresh_funcs, fresh_classes


def _push_bindings(types, funcs, classes):
    import advanced_syntax
    import tools
    pa._SAVED_BINDINGS = (
        advanced_syntax.TYPE_dictionary, advanced_syntax.FUNCTION_dictionary,
        advanced_syntax.CLASS_dictionary, tools.pa.TYPE_dictionary)
    advanced_syntax.TYPE_dictionary = types
    advanced_syntax.FUNCTION_dictionary = funcs
    advanced_syntax.CLASS_dictionary = classes


def _pop_bindings(types, funcs, classes):
    import advanced_syntax
    import tools
    saved = pa._SAVED_BINDINGS
    advanced_syntax.TYPE_dictionary = saved[0]
    advanced_syntax.FUNCTION_dictionary = saved[1]
    advanced_syntax.CLASS_dictionary = saved[2]


def bind_target(target, value):
    for table in pa.TYPE_dictionary.values():
        if target in table:
            table[target] = value
            return
    pa.TYPE_dictionary['int'][target] = value


def apply_import(rel, namespace, attribute):
    path = resolve(rel)
    if path is None:
        raise FileNotFoundError(f"找不到文件: {rel}")

    if path.endswith(".py"):
        import_python(rel, namespace)
        return

    if path in pa.IMPORT_STATE["files"]:
        return
    pa.IMPORT_STATE["files"].append(path)

    types, funcs, classes = run_isolated(path)

    for name, fn in funcs.items():
        target = name if namespace is None else namespace + "." + name
        pa.FUNCTION_dictionary[target] = fn
        if namespace is not None and attribute:
            pa.FUNCTION_dictionary.setdefault(name, fn)

    for cls, members in classes.items():
        pa.CLASS_dictionary.setdefault(cls, {}).update(members)

    if attribute:
        for table in types.values():
            for var, value in table.items():
                target = var if namespace is None else namespace + "." + var
                bind_target(target, value)


def parse_import(stmt):
    if len(stmt) < 2:
        raise SyntaxError(f"import 格式错误: {stmt}")
    raw = stmt[1]
    if not (raw.startswith('"') and raw.endswith('"')):
        raise SyntaxError(f"import 路径要用字符串: {stmt}")
    rel = raw[1:-1]
    namespace = None
    attribute = False
    i = 2
    while i < len(stmt):
        if stmt[i] == "as":
            if i + 1 >= len(stmt):
                raise SyntaxError(f"import as 缺少名字: {stmt}")
            namespace = stmt[i + 1]
            i += 2
        elif stmt[i] == "with" and i + 1 < len(stmt) and stmt[i + 1] == "attribute":
            attribute = True
            i += 2
        else:
            raise SyntaxError(f"import 未知修饰: {stmt}")
    return rel, namespace, attribute


@register("import")
def handle_import(stmt):
    rel, namespace, attribute = parse_import(stmt)
    apply_import(rel, namespace, attribute)
    return None
