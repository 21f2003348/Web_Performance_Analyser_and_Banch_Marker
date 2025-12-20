import time
import json
import os
import psutil
from statistics import mean
from datetime import datetime


process = psutil.Process()


def benchmark_methods(task_name, methods, data=None, runs=10):
    """
    Benchmark a list of methods performing the same task.

    Measures:
      - Execution time
      - CPU usage
      - Memory usage

    Prints best method for each metric based on averages.
    """

    results = {
        "task": task_name,
        "runs": runs,
        "timestamp": datetime.utcnow().isoformat(),
        "results": []
    }

    for name, func in methods:
        timings = []
        cpu_usages = []
        memory_usages = []

        for _ in range(runs):
            # CPU baseline
            process.cpu_percent(interval=None)

            mem_before = process.memory_info().rss
            start = time.perf_counter()

            func(data)

            end = time.perf_counter()
            mem_after = process.memory_info().rss
            cpu_after = process.cpu_percent(interval=None)

            timings.append(end - start)
            cpu_usages.append(cpu_after)
            memory_usages.append(mem_after - mem_before)

        results["results"].append({
            "method": name,
            "avg_time": mean(timings),
            "avg_cpu": mean(cpu_usages),
            "avg_memory_bytes": mean(memory_usages),
            "min_time": min(timings),
            "max_time": max(timings),
        })

    # Decide best methods
    best_time = min(results["results"], key=lambda x: x["avg_time"])
    best_cpu = min(results["results"], key=lambda x: x["avg_cpu"])
    best_memory = min(results["results"], key=lambda x: x["avg_memory_bytes"])

    results["best"] = {
        "time": best_time["method"],
        "cpu": best_cpu["method"],
        "memory": best_memory["method"],
    }

    # Print summary
    print("\n📊 Benchmark Summary")
    print("-" * 40)
    print(f"🏆 Fastest method       : {best_time['method']}")
    print(f"🧠 Lowest CPU usage     : {best_cpu['method']}")
    print(f"💾 Lowest memory usage  : {best_memory['method']}")
    print("-" * 40)

    save_results(task_name, results)

    return results


def save_results(task_name, results):
    """
    Save benchmark results under results/<task_name>/ directory.
    """

    base_dir = os.path.join(
        os.path.dirname(__file__),
        "..",
        "results",
        task_name
    )
    os.makedirs(base_dir, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"{task_name}_results_{timestamp}.json"
    filepath = os.path.join(base_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)

    print(f"[✓] Results saved to {filepath}")
