import json
from Bench_Marker.core.benchmark_runner import benchmark_methods
from Bench_Marker.tasks.fileio_task import write_stdlib, read_stdlib

payload = {"numbers": list(range(5000))}

methods = [
    ("write_json", write_stdlib),
    ("read_json", read_stdlib)
]

results = benchmark_methods(
    task_name="file_io",
    methods=methods,
    data=payload,
    runs=10
)

print(json.dumps(results, indent=2))
