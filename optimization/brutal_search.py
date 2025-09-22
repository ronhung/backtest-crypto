import numpy as np
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Union, Set


ParamSpace = Dict[str, Union[Tuple[float, float], Sequence[Any]]]


def _sample_param(name: str, space: Union[Tuple[float, float], Sequence[Any]],
                  int_params: Set[str]) -> Any:
    """從給定的參數空間抽樣一個參數值。"""
    # 類別型／清單空間
    if isinstance(space, (list, tuple)) and len(space) > 0 and not (
        isinstance(space, tuple) and len(space) == 2 and all(isinstance(v, (int, float)) for v in space)
    ):
        return np.random.choice(space)

    # 連續或整數區間 (low, high)
    assert isinstance(space, tuple) and len(space) == 2, f"參數 '{name}' 必須是數值區間 (low, high) 或 選項清單"
    low, high = space
    if name in int_params:
        # randint 為 [low, high)；若要含上界，需將 high 加 1
        high_inclusive = int(high) + 1
        return int(np.random.randint(int(low), high_inclusive))
    return float(np.random.uniform(low, high))


def brutal_search(
    obj_func: Callable[[Dict[str, Any]], float],
    param_space: ParamSpace,
    *,
    max_iter: int = 100,
    int_params: Optional[Set[str]] = None,
    seed: Optional[int] = None,
    patience: Optional[int] = None,
    greater_is_better: bool = True,
    verbose: bool = False,
    callback: Optional[Callable[[int, Dict[str, Any], float, Dict[str, Any], float], None]] = None,
) -> Tuple[float, Dict[str, Any], List[Tuple[Dict[str, Any], float]]]:
    """
    在參數空間上進行隨機（brutal）搜尋。

    參數:
        obj_func: 目標函數。接受參數字典，回傳分數（float）。
        param_space: 參數空間。每個參數對應 (low, high) 的數值區間或一個可選清單。
        max_iter: 隨機評估的最大迭代次數。
        int_params: 需以整數抽樣的參數名稱集合。
        seed: 隨機種子，用於結果可重現。
        patience: 若連續 N 次無改善則提前停止（None 表示不啟用）。
        greater_is_better: True 表示分數愈大愈好；False 表示愈小愈好。
        verbose: True 時印出進度資訊。
        callback: 可選的回呼函數：callback(iteration, params, score, best_params, best_score)。

    回傳:
        best_score, best_params, history（history 為 (params, score) 的列表）。
    """
    if seed is not None:
        np.random.seed(seed)

    int_params = int_params or set()
    history: List[Tuple[Dict[str, Any], float]] = []  # 紀錄每次抽樣的參數與分數

    best_score = -np.inf if greater_is_better else np.inf  # 目前最佳分數
    best_params: Dict[str, Any] = {}  # 目前最佳參數
    no_improve = 0  # 連續未改善次數

    for iteration in range(1, max_iter + 1):
        params: Dict[str, Any] = {}
        for name, space in param_space.items():  # 為每個參數抽樣
            params[name] = _sample_param(name, space, int_params)

        score = float(obj_func(params))
        history.append((params, score))

        improved = (score > best_score) if greater_is_better else (score < best_score)  # 是否改善
        if improved:
            best_score = score
            best_params = params
            no_improve = 0
        else:
            no_improve += 1

        if verbose and (iteration % max(1, max_iter // 10) == 0 or improved):  # 定期或改善時印出進度
            print(f"第 {iteration}/{max_iter} 次迭代 | 分數={score:.6f} | 最佳={best_score:.6f} | 參數={params}")

        if callback is not None:  # 外部回呼
            callback(iteration, params, score, best_params, best_score)

        if patience is not None and no_improve >= patience:
            if verbose:
                print(f"提前停止於第 {iteration} 次迭代（連續 {patience} 次無提升）")
            break

    return best_score, best_params, history

