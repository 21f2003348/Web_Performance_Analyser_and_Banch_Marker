# run_json_benchmark.py
import json
from benchmark_runner import benchmark_methods
from tasks.json_task import (
    parse_json_stdlib,
    parse_json_ujson,
    parse_json_orjson,
)

# Sample JSON payload (can scale size later)
data = json.dumps({
    "name": "Benchmark Test",
    "values": list(range(1000)),
    "nested": {"a": 1, "b": 2, "c": [1, 2, 3]}
})

methods = [
    ("json", parse_json_stdlib),
    ("ujson", parse_json_ujson),
    ("orjson", parse_json_orjson),
]

results = benchmark_methods(
    task_name="json_parsing",
    methods=methods,
    data=data,
    runs=20
)

print(json.dumps(results, indent=2))