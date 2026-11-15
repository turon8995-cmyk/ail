import numpy as np
from nn.nn_state import *
from tools import *
def relu(x):
    return np.maximum(0, x)


def softmax(x):
    x = x - np.max(x, axis=1, keepdims=True)
    e = np.exp(x)
    return e / np.sum(e, axis=1, keepdims=True)
def forward(self, x, activate=True):
    
    z = x @ self.w + self.b
    return relu(z) if activate else z

class Layer:
    def __init__(self, inputs, outputs):
        self.w = np.random.randn(inputs, outputs) * np.sqrt(2.0 / inputs)
        self.b = np.zeros((1, outputs))
    #activate=(i != n-1)
    def forward(self, x, activate=True):
        z = x @ self.w + self.b
        return relu(z) if activate else z


def make_layers(shape):
    return [Layer(shape[i], shape[i + 1]) for i in range(len(shape) - 1)]


if __name__ == "__main__":
    wife_SHAPE = [3, 2, 5]
    layers = make_layers(wife_SHAPE)

    x = np.random.randn(4, 3)
    n = len(layers)
    for i, ly in enumerate(layers):
        x = ly.forward(x, activate=(i != n - 1))
    out = softmax(x)
    print(out.shape)
