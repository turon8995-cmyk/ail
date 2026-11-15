import re
from attributes import pattern, STMT_STARTERS, KEY_SYMBOL
#切词元
def tokenize(text):
    #去 // 注释
    text = re.sub(r'//[^\n]*', '', text)
    raw = re.findall(pattern, text)
    out, i = [], 0
    pairs = {"=": "==", "!": "!=", ">": ">=", "<": "<="}
    while i < len(raw):
        t = raw[i]
        if i + 1 < len(raw) and raw[i+1] == "=" and t in pairs:
            out.append(pairs[t])
            i += 2
            continue
        out.append(t)
        i += 1
    return out
#把类token和并
def merge_dotted(tokens):
    out, i = [], 0
    while i < len(tokens):
        if (re.fullmatch(r'[A-Za-z_]\w*', tokens[i])
                and i + 2 < len(tokens) and tokens[i+1] == "."
                and re.fullmatch(r'[A-Za-z_]\w*', tokens[i+2])):
            name = tokens[i] + "." + tokens[i+2]
            i += 3
            while (i + 1 < len(tokens) and tokens[i] == "."
                   and re.fullmatch(r'[A-Za-z_]\w*', tokens[i+1])):
                name += "." + tokens[i+1]
                i += 2
            out.append(name)
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
    paren = 0
    i = 0
    while i < len(tokens):
        t = tokens[i]

        prev_is_colon = i > 0 and tokens[i-1] == ":"
        is_at_end = (t == "@" and len(cur) >= 2
                     and cur[-1] not in ("@", "&")
                     and re.fullmatch(r'[A-Za-z_]\w*', cur[-1]))
        prev_is_close_brace = i > 0 and tokens[i-1] == "}"
        prev_is_close_paren = i > 0 and tokens[i-1] == ")"
        prev_is_amp   = i > 0 and tokens[i-1] == "&"
        prev_is_def   = i > 0 and tokens[i-1] == "def"
        prev_is_mode  = i > 0 and tokens[i-1] == "mode"
        prev_is_as    = i > 0 and tokens[i-1] == "as"
        prev_is_eq    = i > 0 and tokens[i-1] == "="
        prev_is_lead  = (prev_is_mode or prev_is_as or prev_is_eq
                         or prev_is_amp or prev_is_def)
        in_marker = (cur and cur[0] in KEY_SYMBOL and len(cur) == 2
                     and cur[1] == "layer" and t != "{")
        marker_done = (cur and cur[0] in KEY_SYMBOL and len(cur) >= 2
                       and t == "{" and cur[1] == "layer")
        layer_block = (cur and cur[0] == "layer" and t == "{")
        marker_full = (cur and cur[0] in KEY_SYMBOL and len(cur) >= 3
                       and cur[1] == "layer" and t == "layer")

        is_starter = False
        if depth == 0 and paren == 0:
            if marker_done or marker_full:
                is_starter = True
            elif not prev_is_lead and not in_marker:
                next_is_brace = (i + 1 < len(tokens) and tokens[i+1] == "{")
                if not (t == "layer" and next_is_brace):
                    is_starter = (
                    (t in STMT_STARTERS and cur and not prev_is_colon) or
                    (t in KEY_SYMBOL and cur and not is_at_end) or
                    (i + 1 < len(tokens) and tokens[i+1] == ":" and cur) or
                    (i + 1 < len(tokens) and tokens[i+1] == "=" and cur and
                     re.fullmatch(r'[A-Za-z_]\w*', t) and
                     not (i > 0 and tokens[i-1] == ".")) or
                    (prev_is_close_paren
                     and re.fullmatch(r'[A-Za-z_]\w*', t) and cur
                     and not (i + 1 < len(tokens) and tokens[i+1] == "(")) or
                    (i > 0 and tokens[i-1] == "]" and cur
                     and re.fullmatch(r'[A-Za-z_]\w*', t)) or
                    (prev_is_close_brace
                     and re.fullmatch(r'[A-Za-z_]\w*', t) and cur
                     and t not in ("else", "elif"))
                )
        if is_starter:
            stmts.append(cur); cur = []

        if t == "{":
            depth += 1
        elif t == "}":
            depth = max(depth - 1, 0)

        if t == "(":
            paren += 1
        elif t == ")":
            paren = max(paren - 1, 0)

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