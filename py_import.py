import importlib
import importlib.util
import inspect
import os
import re
import sys

import attributes as pa

PACKAGES_DIR = "packages"


def project_root():
    if pa.IMPORT_STATE["root"]:
        return pa.IMPORT_STATE["root"]
    return os.getcwd()


def resolve(rel):
    root = project_root()
    for path in (os.path.join(root, rel),
                 os.path.join(root, PACKAGES_DIR, rel),
                 os.path.abspath(rel)):
        if os.path.isfile(path):
            return os.path.abspath(path)
    return None


def load_python(rel):
    path = resolve(rel)
    if path is None:
        return None
    name = "_ail_import_" + re.sub(r'\W', '_', os.path.splitext(path)[0])
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def call_python(fn, args):
    try:
        params = inspect.signature(fn).parameters
    except (TypeError, ValueError):
        return fn(*args)
    required = [n for n, p in params.items()
                if p.default is p.empty
                and p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)]
    if len(required) == len(params) and len(required) - 1 == len(args):
        return fn(fn, *args)
    return fn(*args)


def import_python(rel, namespace):
    module = load_python(rel)
    if module is None:
        return False

    for name, obj in vars(module).items():
        if name.startswith("_"):
            continue
        if inspect.isroutine(obj):
            if name in pa.FUNCTION_dictionary:
                continue
            pa.FUNCTION_dictionary[name] = {
                "params": list(inspect.signature(obj).parameters),
                "body": [],
                "decorator": None,
                "python": obj,
            }
        elif isinstance(obj, type):
            if name not in pa.CLASS_dictionary:
                pa.CLASS_dictionary[name] = {"python": obj}

    if namespace:
        for name, obj in vars(module).items():
            if name.startswith("_"):
                continue
            if inspect.isroutine(obj):
                pa.FUNCTION_dictionary.setdefault(namespace + "." + name,
                                                  pa.FUNCTION_dictionary.get(name))
        for name, obj in vars(module).items():
            if name.startswith("_") or not isinstance(obj, type):
                continue
            pa.CLASS_dictionary.setdefault(namespace, {})[name] = {
                "type": "py_class", "value": obj}

    return True


def import_python_class(namespace, class_name):
    entry = pa.CLASS_dictionary.get(namespace, {}).get(class_name)
    if not entry or entry.get("type") != "py_class":
        return None
    return entry["value"]
