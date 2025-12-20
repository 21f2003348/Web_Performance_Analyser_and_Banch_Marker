import json
from Bench_Marker.core.benchmark_runner import benchmark_methods
from Bench_Marker.tasks.db_task import setup_db, fetch_orm, fetch_core, fetch_raw

setup_db()

methods = [
    ("sqlalchemy_orm", fetch_orm),
    ("sqlalchemy_core", fetch_core),
    ("raw_sqlite", fetch_raw)
]

results = benchmark_methods(
    task_name="database_access",
    methods=methods,
    data=None,
    runs=10
)

print(json.dumps(results, indent=2))
