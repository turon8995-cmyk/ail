from nn.nn_state import *
def get_valve_nn(class_name, member, default=None):
    try:
        return TRAIN_class[class_name][member]["value"]
    except (KeyError, TypeError):
        return default