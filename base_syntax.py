import re
from attributes import pattern, STMT_STARTERS, KEY_SYMBOL

_IDENT = re.compile(r'[A-Za-z_]\w*')
_DOTTED = re.compile(r'[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*')
_STRING = re.compile(r'"[^"]*"')
_NUMBER = re.compile(r'\d+\.?\d*')


def is_ident(t):
    return _IDENT.fullmatch(t) is not None


def is_dotted(t):
    return _DOTTED.fullmatch(t) is not None


def is_string_token(t):
    return _STRING.fullmatch(t) is not None


def is_number_token(t):
    return _NUMBER.fullmatch(t) is not None
_COMMENT = re.compile(r'//[^\n]*')
_TOKEN = re.compile(pattern)
_PAIRS = {"=": "==", "!": "!=", ">": ">=", "<": "<="}


#切词元
def tokenize(text):
    #去 // 注释
    text = _COMMENT.sub('', text)
    raw = _TOKEN.findall(text)
    out, i, n = [], 0, len(raw)
    while i < n:
        t = raw[i]
        if i + 1 < n and raw[i+1] == "=" and t in _PAIRS:
            out.append(_PAIRS[t])
            i += 2
            continue
        out.append(t)
        i += 1
    return out
#把类token和并
def merge_dotted(tokens):
    if "." not in tokens:
        return tokens
    out, i = [], 0
    n = len(tokens)
    while i < n:
        t = tokens[i]
        if (i + 2 < n and tokens[i+1] == "." and _IDENT.fullmatch(t)
                and _IDENT.fullmatch(tokens[i+2])):
            name = t + "." + tokens[i+2]
            i += 3
            while (i + 1 < n and tokens[i] == "."
                   and _IDENT.fullmatch(tokens[i+1])):
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
                     and is_ident(cur[-1]))
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
                     and cur[1] == "layer_auto" and t != "{")
        marker_done = (cur and cur[0] in KEY_SYMBOL and len(cur) >= 2
                       and t == "{" and cur[1] == "layer_auto")
        layer_block = (cur and cur[0] == "layer_auto" and t == "{")
        marker_full = (cur and cur[0] in KEY_SYMBOL and len(cur) >= 3
                       and cur[1] == "layer_auto" and t == "layer_auto")

        is_starter = False
        if depth == 0 and paren == 0:
            if marker_done or marker_full:
                is_starter = True
            elif not prev_is_lead and not in_marker:
                next_is_brace = (i + 1 < len(tokens) and tokens[i+1] == "{")
                if not (t == "layer_auto" and next_is_brace):
                    is_starter = (
                    (t in STMT_STARTERS and cur and not prev_is_colon) or
                    (t in KEY_SYMBOL and cur and not is_at_end) or
                    (i + 1 < len(tokens) and tokens[i+1] == ":" and cur) or
                    (i + 1 < len(tokens) and tokens[i+1] == "=" and cur and
                     is_ident(t) and
                     not (i > 0 and tokens[i-1] == ".")) or
                    (prev_is_close_paren and is_ident(t) and cur
                     and not (i + 1 < len(tokens) and tokens[i+1] == "(")) or
                    (i > 0 and tokens[i-1] == "]" and cur and is_ident(t)) or
                    (prev_is_close_brace and is_ident(t) and cur
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