# 关键字（保留字，语义登记）
KEYWORDS = {"&", "return", "def", "len", "while", "if", "@",
            "print", "input", "mode", "int", "float", "string", "train",
            "layer"}

# 训练相关标记
TRAIN_KEY = {"train_finish", "layer"}

# 类型字
TYPE_KEY = {"int", "float", "train", "string"}

# 语句开头（关键字）
STMT_STARTERS = {"return", "def", "len", "while", "if",
                 "print", "input", "int", "float", "string", "train", "mode",
                 "layer"}

# 符号开头（& 标记、@ 修饰）
KEY_SYMBOL = {"&", "@"}

# 全局状态
FUNCTION_dictionary = {}
TYPE_dictionary = {"int": {}, "float": {}, "string": {}, "train": {}}
CLASS_dictionary = {}
CALL_STACK = []
last_return = {}
last_value = None
DECORATOR_STATE = {"pending": None}

# 正则
pattern = r'"[^"]*"|\d+\.?\d*|[A-Za-z_]\w*|[+\-*/()=:.{}<>@&]'

# 训练相关
LAYER_dictionary = {}
LAYER_STATE = {"pending_name": None}
TRAIN_STATE = {
    "pending_main": False,
    "pending_finish": False,
    "main": None,
    "finish_callbacks": [],
}