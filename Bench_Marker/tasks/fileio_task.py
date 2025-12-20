import json
import os

FILE_PATH = "Bench_Marker/tasks/Files/benchmark_file.json"

def write_stdlib(data):
    with open(FILE_PATH, "w") as f:
        json.dump(data, f)

def read_stdlib(_):
    with open(FILE_PATH) as f:
        return json.load(f)
