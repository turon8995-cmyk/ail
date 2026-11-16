from attributes import *
from base_syntax import tokenize, split_statements
from runtime import execute
import sys
import os
import advanced_syntax
import ail_import
import nn.nn_syntax

def src(text):
    tokens = tokenize(text)
    stmts = split_statements(tokens)
    has_mode = any(len(s) == 2 and s[0] == "mode" for s in stmts)
    if not has_mode:
        for stmt in stmts:
            execute(stmt)
        return
    current = None
    for stmt in stmts:
        if len(stmt) == 2 and stmt[0] == "mode":
            current = stmt[1]
            continue
        if current is None:
            continue
        execute(stmt)

def run_file(path):
    if not os.path.isfile(path):
        print(f"找不到文件: {path}", file=sys.stderr)
        return 2
    with open(path, encoding="utf-8") as f:
        text = f.read()
    IMPORT_STATE["current"] = os.path.dirname(os.path.abspath(path))
    src(text)
    return 0

if __name__ == '__main__':
    argv = [a for a in sys.argv[1:] if a != "-"]
    if argv:
        argv[0] = argv[0].lstrip("-")
    if argv and argv[0] == "src":
        if len(argv) < 2:
            print("用法: python main.py -src <文件>", file=sys.stderr)
            sys.exit(2)
        sys.exit(run_file(argv[1]))
    # 测试
#    src('''
#&layer xx
#layer{
#50,60
#60,30
#}
#
#&train_main
#def train() {
#    print("训练中")
#}
#
#print("完成")
#    ''')
