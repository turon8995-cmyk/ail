# 关键字
KEYWORDS = {"&", "return", "def", "len", "while", "if", "@",
            "print", "input", "mode", "int", "float", "string", "train",
            "layer", "import", "as",""}

# 训练相关标记
TRAIN_KEY = {"train_finish", "layer"}

# 类型字
TYPE_KEY = {"int", "float", "train", "string"}

# 语句开头
STMT_STARTERS = {"return", "def", "len", "while", "if",
                 "print", "input", "int", "float", "string", "train", "mode",
                 "layer", "import"}

# 符号开头
KEY_SYMBOL = {"&", "@"}

# 全局状态
FUNCTION_dictionary = {}
TYPE_dictionary = {"int": {}, "float": {}, "string": {}, "train": {}}
CLASS_dictionary = {}
CALL_STACK = []
last_return = {}
last_value = None
DECORATOR_STATE = {"pending": None}
IMPORT_STATE = {"files": [], "current": None, "root": None}
INSTANCE_STORE = {}
TRUE_WORDS = {"true", "True"}
FALSE_WORDS = {"false", "False"}

# 内置函数
import builtins

BUILTIN_FUNCTIONS = {}
for _name in ("abs", "bool", "chr", "dict", "float", "hash", "hex",
              "int", "len", "list", "max", "min", "oct", "ord", "print",
              "repr", "round", "set", "sorted", "str", "sum", "tuple", "type"):
    BUILTIN_FUNCTIONS[_name] = getattr(builtins, _name)

# 正则
pattern = r'"[^"]*"|\d+\.?\d*|[A-Za-z_]\w*|[+\-*/()=:.{}<>@&,\[\]!]'

