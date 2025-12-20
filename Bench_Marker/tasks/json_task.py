# tasks/json_task.py
import json

try:
    import ujson
except ImportError:
    ujson = None

try:
    import orjson
except ImportError:
    orjson = None


def parse_json_stdlib(data):
    return json.loads(data)


def parse_json_ujson(data):
    if not ujson:
        raise RuntimeError("ujson not installed")
    return ujson.loads(data)


def parse_json_orjson(data):
    if not orjson:
        raise RuntimeError("orjson not installed")
    return orjson.loads(data)
