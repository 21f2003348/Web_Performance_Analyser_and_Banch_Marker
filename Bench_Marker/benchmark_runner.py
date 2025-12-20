# benchmark_runner.py
import time
import statistics
import tracemalloc
import psutil
import os

def benchmark_methods(task_name, methods, data, runs=10, warmup=2):
    """
    Generic benchmark runner:
    Measures time, memory, and CPU usage.

    Args:
        task_name (str)
        methods (list): [(method_name, callable)]
        data: input for methods
        runs (int)
        warmup (int)

    Returns:
        dict
    """
    process = psutil.Process(os.getpid())

    results = {
        "task": task_name,
        "runs": runs,
        "results": {}
    }

    for name, func in methods:
        timings = []
        memory_peaks = []
        cpu_usages = []

        # ---- Warm-up runs ----
        for _ in range(warmup):
            func(data)

        # ---- Measured runs ----
        for _ in range(runs):
            tracemalloc.start()

            cpu_before = process.cpu_times()
            start = time.perf_counter()

            func(data)

            end = time.perf_counter()
            cpu_after = process.cpu_times()

            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            elapsed = end - start
            cpu_time = (
                (cpu_after.user + cpu_after.system) -
                (cpu_before.user + cpu_before.system)
            )

            timings.append(elapsed)
            memory_peaks.append(peak / 1024)  # KB
            cpu_usages.append(cpu_time)

        results["results"][name] = {
            "time": {
                "avg": statistics.mean(timings),
                "min": min(timings),
                "max": max(timings)
            },
            "memory_kb": {
                "avg": statistics.mean(memory_peaks),
                "max": max(memory_peaks)
            },
            "cpu_seconds": {
                "avg": statistics.mean(cpu_usages),
                "max": max(cpu_usages)
            }
        }

    return results
