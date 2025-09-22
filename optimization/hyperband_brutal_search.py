import numpy as np
from typing import Dict, Callable, Any, List, Set, Tuple

def hyperband_search(
    obj_func: Callable[[Dict[str, Any], float], float],
    param_space: Dict[str, Tuple[float, float]],
    *,
    max_iter: int = 1000,
    max_resource: int = 100,  # 對應 run_backtest 的 percentage
    eta: int = 3,  # 每輪保留比例
    int_params: Set[str] = None,
    seed: int = None,
    verbose: bool = False  # 是否印出優化過程
) -> Tuple[float, Dict[str, Any], List[Tuple[Dict[str, Any], float]]]:
    # best_score, best_params, history

    if seed is not None:
        np.random.seed(seed)
    int_params = int_params or set()
    history: List[Tuple[Dict[str, Any], float]] = []

    # Hyperband 的多輪資源分配
    s_max = int(np.log(max_resource) / np.log(eta))
    B = (s_max + 1) * max_iter  # 總資源

    best_score = -np.inf
    best_params: Dict[str, Any] = {}

    def _sample_param(name, space):
        if isinstance(space, tuple) and len(space) == 2:
            low, high = space
            if name in int_params:
                return int(np.random.randint(int(low), int(high) + 1))
            return float(np.random.uniform(low, high))
        else:
            return np.random.choice(space)

    for s in reversed(range(s_max + 1)):
        n = int(np.ceil(B / max_resource / (s + 1)) * eta ** s)  # 本輪候選數
        r = max_resource * eta ** (-s)  # 本輪最小資源
        # 生成初始參數組
        T = [{name: _sample_param(name, space) for name, space in param_space.items()} for _ in range(n)]

        while len(T) > 0:
            # 用當前資源測試所有組
            scores = []
            for t in T:
                score = obj_func(t, percentage=r)
                scores.append((t, score))
                history.append((t, score))
                if score > best_score:
                    best_score = score
                    best_params = t
                if verbose:
                    print(f"[Hyperband] params={t}, percentage={r}, score={score:.4f}")

            # 按分數排序，保留前 1/eta
            scores.sort(key=lambda x: x[1], reverse=True)
            n_keep = max(1, len(scores) // eta)
            T = [t for t, s in scores[:n_keep]]
            r *= eta  # 增加資源量
            if r > max_resource:
                break

    return best_score, best_params, history
