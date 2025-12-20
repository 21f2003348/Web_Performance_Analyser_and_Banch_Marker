import json
from Bench_Marker.core.benchmark_runner import benchmark_methods
from Bench_Marker.tasks.http_task import fetch_requests, fetch_httpx

methods = [
    ("requests", fetch_requests),
    ("httpx", fetch_httpx)
]

results = benchmark_methods(
    task_name="http_client_requests",
    methods=methods,
    data=None,
    runs=10
)

print(json.dumps(results, indent=2))
