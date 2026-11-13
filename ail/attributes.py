# 关键字（保留字，语义登记）
KEYWORDS = {"&", "return", "def", "len", "while", "if", "@",
            "print", "input", "mode", "int", "float", "string", "train"}

# 训练相关标记
TRAIN_KEY = {"train_finish", "layer"}

# 类型字
TYPE_KEY = {"int", "float", "train", "string"}

# 语句开头（关键字）
STMT_STARTERS = {"return", "def", "len", "while", "if",
                 "print", "input", "int", "float", "string", "train", "mode"}

# 符号开头（& 标记、@ 修饰）
KEY_SYMBOL = {"&", "@"}

# 全局状态
FUNCTION_dictionary = {}
TYPE_dictionary = {"int": {}, "float": {}, "string": {}, "train": {}}
CLASS_dictionary = {}
LAYER_dictionary = {}          # &layer 存的层
CALL_STACK = []
last_return = {}               # @x 用，替代 AT_dictionary
pending_decorator = None       # @x/@x@ 暂存

# 正则
pattern = r'"[^"]*"|\d+\.?\d*|[A-Za-z_]\w*|[+\-*/()=:.{}<>@&]'