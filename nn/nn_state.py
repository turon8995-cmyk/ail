LAYER_dictionary = {}
LAYER_STATE = {"pending_name": None}
TRAIN_STATE = {
    "pending_main": False,
    "pending_finish": False,
    "main": None,
    "finish_callbacks": [],
}
need_TRAIN_parameter = ["lr","batch","epochs"]
default_TRAIN = {"lr":0.01,"batch":20,"epochs":40}
TRAIN_class = {}
wife_SHAPE = {}#神经网络构成,根据样本数量
num_of_data = 0#训练样本
exercise = 0#训练次数