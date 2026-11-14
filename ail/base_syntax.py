import re
from attributes import pattern, STMT_STARTERS, KEY_SYMBOL
#切词元
def tokenize(text):
    #去 // 注释
    text = re.sub(r'//[^\n]*', '', text)
    return re.findall(pattern, text)
#把类token和并
def merge_dotted(tokens):
    out, i = [], 0
    while i < len(tokens):
        if i + 2 < len(tokens) and tokens[i+1] == "." and \
           re.fullmatch(r'[A-Za-z_]\w*', tokens[i]) and \
           re.fullmatch(r'[A-Za-z_]\w*', tokens[i+2]):
            out.append(f"{tokens[i]}.{tokens[i+2]}")
            i += 3
        else:
            out.append(tokens[i])
            i += 1
    return out
#后面有:
def has_symbol_after_head(stmt,symbol):
    return len(stmt) >= 2 and stmt[1] == symbol
#返回:的下标
def symbol_index(stmt):
    try:
        return stmt.index(":")
    except ValueError:
        return -1
#以token为基础，再加一层[]
def split_statements(tokens):
    stmts, cur = [], []
    depth = 0
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if t == "{":
            depth += 1
        elif t == "}":
            depth -= 1

        prev_is_colon = i > 0 and tokens[i-1] == ":"
        is_at_end = (t == "@" and len(cur) >= 2
                     and cur[-1] not in ("@", "&")
                     and re.fullmatch(r'[A-Za-z_]\w*', cur[-1]))
        prev_is_close_brace = i > 0 and tokens[i-1] == "}"
        prev_is_colon = i > 0 and tokens[i-1] == ":"
        prev_is_amp   = i > 0 and tokens[i-1] == "&"
        prev_is_close_brace = i > 0 and tokens[i-1] == "}"
        is_at_end = (t == "@" and len(cur) >= 2
                    and cur[-1] not in ("@", "&")
                    and re.fullmatch(r'[A-Za-z_]\w*', cur[-1]))
        prev_is_colon = i > 0 and tokens[i-1] == ":"
        prev_is_amp   = i > 0 and tokens[i-1] == "&"
        prev_is_def   = i > 0 and tokens[i-1] == "def"
        prev_is_close_brace = i > 0 and tokens[i-1] == "}"
        is_at_end = (t == "@" and len(cur) >= 2
                    and cur[-1] not in ("@", "&")
                    and re.fullmatch(r'[A-Za-z_]\w*', cur[-1]))

        is_starter = depth == 0 and (
            (t in STMT_STARTERS and cur and not prev_is_colon
            and not prev_is_amp and not prev_is_def) or
            (t in KEY_SYMBOL and cur and not is_at_end) or
            (i + 1 < len(tokens) and tokens[i+1] == ":" and cur) or
            (i + 1 < len(tokens) and tokens[i+1] == "=" and cur and
            re.fullmatch(r'[A-Za-z_]\w*', t)) or
            (prev_is_close_brace and re.fullmatch(r'[A-Za-z_]\w*', t) and cur)
        )
        if is_starter:
            stmts.append(cur); cur = []
        cur.append(t)
        i += 1
    if cur:
        stmts.append(cur)
    return stmts
def split_args(tokens):
    args, cur = [], []
    depth = 0
    for t in tokens:
        if t in ("(", "{", "["):
            depth += 1
        elif t in (")", "}", "]"):
            depth -= 1
        if t == "," and depth == 0:
            args.append(cur); cur = []
        else:
            cur.append(t)
    if cur:
        args.append(cur)
    return args