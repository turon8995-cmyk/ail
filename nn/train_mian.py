import numpy as np
from nn.nn_state import *
from nn.nn_tools import *

_X = np.array([
    [0, 0],
    [0, 1],
    [1, 0],
    [1, 1],
], dtype=np.float32)

_y = np.array([0, 1, 1, 0], dtype=np.int64)

N = 1000
idx = np.random.randint(0, 4, size=N)
_X = _X[idx]
_y = _y[idx]


def build_mlp(layer_sizes):
    weights, biases = [], []
    for in_dim, out_dim in layer_sizes:
        W = np.random.randn(in_dim, out_dim) * np.sqrt(2.0 / in_dim)
        b = np.zeros((1, out_dim))
        weights.append(W)
        biases.append(b)
    return weights, biases


def relu(x):
    return np.maximum(0, x)


def relu_grad(x):
    return (x > 0).astype(x.dtype)


def softmax(x):
    x = x - x.max(axis=1, keepdims=True)
    e = np.exp(x)
    return e / e.sum(axis=1, keepdims=True)


def forward(X, weights, biases):
    acts, pre_acts = [X], []
    a = X
    L = len(weights)
    for i in range(L):
        z = a @ weights[i] + biases[i]
        pre_acts.append(z)
        a = relu(z) if i < L - 1 else softmax(z)
        acts.append(a)
    return acts, pre_acts


def cross_entropy(y_pred, y_true):
    n = y_pred.shape[0]
    correct = y_pred[np.arange(n), y_true]
    return -np.mean(np.log(correct + 1e-12))


def backward(acts, pre_acts, weights, y_true):
    L = len(weights)
    n = acts[0].shape[0]
    dWs, dbs = [None] * L, [None] * L

    dz = acts[-1].copy()
    dz[np.arange(n), y_true] -= 1
    dz /= n

    for i in reversed(range(L)):
        dWs[i] = acts[i].T @ dz
        dbs[i] = dz.sum(axis=0, keepdims=True)
        if i > 0:
            da = dz @ weights[i].T
            dz = da * relu_grad(pre_acts[i - 1])
    return dWs, dbs


def train(layer_sizes, result, X, y):
    lr     = float(result["lr"])
    batch  = int(result["batch"])
    epochs = int(result["epochs"])
    X = np.asarray(X, dtype=np.float32)
    y = np.asarray(y, dtype=np.int64).reshape(-1)
    N = X.shape[0]

    weights, biases = build_mlp(layer_sizes)

    for epoch in range(epochs):
        idx = np.random.permutation(N)
        X_shuf, y_shuf = X[idx], y[idx]
        total_loss, steps = 0.0, 0

        for start in range(0, N, batch):
            xb = X_shuf[start:start + batch]
            yb = y_shuf[start:start + batch]

            acts, pre_acts = forward(xb, weights, biases)
            total_loss += cross_entropy(acts[-1], yb)
            steps += 1

            dWs, dbs = backward(acts, pre_acts, weights, yb)
            for i in range(len(weights)):
                weights[i] -= lr * dWs[i]
                biases[i] -= lr * dbs[i]

        print(f"epoch {epoch + 1}/{epochs}  loss={total_loss / steps:.4f}")

    return weights, biases


def predict(X, weights, biases):
    a = np.asarray(X, dtype=np.float32)
    L = len(weights)
    for i in range(L):
        z = a @ weights[i] + biases[i]
        a = relu(z) if i < L - 1 else softmax(z)
    return a

def handle(weights, biases):
    probs = predict(_X, weights, biases)
    acc = (probs.argmax(axis=1) == _y).mean()
    return acc

def main(layer_class, train_class, need=None):
    result = {}
    need = need or need_TRAIN_parameter
    for name in need:
        value = get_valve_nn(train_class, name)
        if value is None:
            if name not in default_TRAIN:
                raise KeyError(f"参数 {name} 既未在类中定义，也无默认值")
            value = default_TRAIN[name]
        result[name] = value

    weights, biases = train(LAYER_dictionary[layer_class], result, _X, _y)
    return handle(weights, biases)