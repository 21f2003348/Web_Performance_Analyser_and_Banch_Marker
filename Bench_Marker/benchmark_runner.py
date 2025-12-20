# benchmark_runner.py
import time
import statistics

def benchmark_methods(task_name, methods, data, runs=10, warmup=2):
    """
    Generic benchmark runner (time-only).

    Args:
        task_name (str): Name of the task (e.g. 'json_parsing')
        methods (list): [(method_name, callable), ...]
        data: Input passed to each method
        runs (int): Number of measured runs
        warmup (int): Warm-up runs (not measured)

    Returns:
        dict: Structured benchmark results
    """
    results = {
        "task": task_name,
        "runs": runs,
        "results": {}
    }

    for name, func in methods:
        timings = []

        # ---- Warm-up runs (important for fairness) ----
        for _ in range(warmup):
            func(data)

        # ---- Measured runs ----
        for _ in range(runs):
            start = time.perf_counter()
            func(data)
            end = time.perf_counter()
            timings.append(end - start)

        results["results"][name] = {
            "avg_time": statistics.mean(timings),
            "min_time": min(timings),
            "max_time": max(timings)
        }

    return results
