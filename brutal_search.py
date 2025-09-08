import numpy as np


def brutal_search(obj_func, x0_range: dict, tol=1e-6, max_iter=100, int_params=None):
    """
    obj_func: 目標函數，接受 dict
    x0: 初始點 (dict)
    int_params: 必須是整數的參數名稱集合，例如 {"rsi_period"}
    """
    int_params = int_params or set()
    best_val = -np.inf
    best_params = None
    for iteration in range(max_iter):
        x0 = dict()
        for xk, (low, high) in x0_range.items():
            if xk in int_params:
                x0[xk] = np.random.randint(low, high+1)
            else:
                x0[xk] = np.random.uniform(low, high)
        val = obj_func(x0)
        if val > best_val:
            best_val = val
            best_params = x0
        
            
    return best_val, best_params


objective_function = lambda params: -(params["x"] - 1) ** 2 - (params["y"] - 2) ** 2

brutal_search(
    objective_function,
    x0_range = {
        "x": (0, 3),
        "y": (0, 3),
    },
    tol=1e-4,
    max_iter=100
)
