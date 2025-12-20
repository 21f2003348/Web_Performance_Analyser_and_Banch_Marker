import json
from Bench_Marker.core.benchmark_runner import benchmark_methods
from Bench_Marker.tasks.json_task import (
    parse_json_stdlib,
    parse_json_ujson,
    parse_json_orjson
)

payload = json.dumps({
    "user": "benchmark",
    "values": list(range(5000)),
    "nested": {"a": 1, "b": 2, "c": [1, 2, 3]}
})

methods = [
    ("json", parse_json_stdlib),
    ("ujson", parse_json_ujson),
    ("orjson", parse_json_orjson)
]

results = benchmark_methods(
    task_name="json_parsing",
    methods=methods,
    data=payload,
    runs=20
)

print(json.dumps(results, indent=2))
