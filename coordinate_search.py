import numpy as np
from scipy.optimize import minimize_scalar


def coordinate_search(obj_func, x0: dict, tol=1e-6, max_iter=100, int_params=None, positive_params=None):
    """
    obj_func: 目標函數，接受 dict
    x0: 初始點 (dict)
    int_params: 必須是整數的參數名稱集合，例如 {"rsi_period"}
    """
    x = x0.copy()
    keys = list(x.keys())
    int_params = int_params or set()
    positive_params = positive_params or set()
    for iteration in range(max_iter):
        x_old = x.copy()
        
        for k in keys:
            # 定義沿第 k 個方向的一維函數
            if k not in int_params:
                x[k] *= np.random.uniform(0.99, 1.01)
            def f_line(alpha):
                x_new = x.copy()
                val = x[k] + alpha
                if k in int_params:
                    val = int(round(val))  # 轉成整數
                if k in positive_params:
                    if val < 0:
                        val = 0
                x_new[k] = val
                return -1 *obj_func(x_new)
            
            res = minimize_scalar(f_line, bounds=(0, 1), method='bounded')
            val = x[k] + res.x
            if k in int_params:
                val = int(round(val))
                if val < 1:
                    val = 1
            x[k] = val
        
        # 收斂判斷
        diff = np.linalg.norm([x[k] - x_old[k] for k in keys])
        if diff < tol:
            break
            
    return x, obj_func(x)


if __name__ == "__main__":
    # 測試函數：f(x, y) = (x-1)^2 + (y-2)^2
    def test_func(params):
        return (params["x"] - 1) ** 2 + (params["y"] - 2) ** 2

    x0 = {"x": 0, "y": 0}  # 初始點
    best_params, best_val = coordinate_search(test_func, x0)

    print("最佳參數:", best_params)
    print("最佳函數值:", best_val)
