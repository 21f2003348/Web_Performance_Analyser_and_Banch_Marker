"""
Standalone profiler report app.
Usage:
  FLASK_PROFILER_DB=/path/to/flask_profiler.sqlite python profiler_report.py
  or python profiler_report.py
"""

from flask import Flask, render_template_string
import sqlite3
import os
import math
from collections import defaultdict

# ---------------- CONFIG ----------------
DB_PATH = os.environ.get("FLASK_PROFILER_DB", "flask_profiler.sqlite")
HOST = "127.0.0.1"
PORT = int(os.environ.get("PROFILER_REPORT_PORT", 5001))
DEBUG = os.environ.get("PROFILER_REPORT_DEBUG", "1").lower() in ("1", "true", "yes")

app = Flask(__name__)

# ---------------- HELPERS ----------------
def mean_std(arr):
    if not arr:
        return 0.0, 0.0
    mean = sum(arr) / len(arr)
    var = sum((x - mean) ** 2 for x in arr) / len(arr)
    return mean, math.sqrt(var)

def detect_profiler_table(cur):
    tables = [r[0] for r in cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()]
    if not tables:
        return None, "No tables found in profiler DB."

    for t in ("measurements", "requests", "profiles", "profile", "flask_profiler"):
        if t in tables:
            return t, None

    for t in tables:
        if any(k in t.lower() for k in ("measure", "profile", "request")):
            return t, None

    return None, f"Could not detect profiler table. Found: {tables}"

def parse_float(v):
    try:
        return float(v)
    except Exception:
        return None

# ---------------- AGGREGATION ----------------
def aggregate_rows(rows, path_col, method_col, elapsed_col):
    aggs = defaultdict(lambda: {"count": 0, "sum": 0.0, "min": None, "max": None})
    samples = []

    for r in rows:
        d = dict(r)
        path = d.get(path_col) or d.get("path") or d.get("name") or "UNKNOWN"
        method = d.get(method_col) or d.get("method") or "UNKNOWN"
        elapsed = parse_float(d.get(elapsed_col))

        key = (method, path)
        aggs[key]["count"] += 1

        if elapsed is not None:
            aggs[key]["sum"] += elapsed
            aggs[key]["min"] = elapsed if aggs[key]["min"] is None else min(aggs[key]["min"], elapsed)
            aggs[key]["max"] = elapsed if aggs[key]["max"] is None else max(aggs[key]["max"], elapsed)

        if len(samples) < 10:
            samples.append({k: str(v)[:200] for k, v in d.items()})

    return aggs, samples

def build_endpoints(aggs):
    endpoints = []
    for (method, path), v in aggs.items():
        avg = v["sum"] / v["count"] if v["sum"] else None
        endpoints.append({
            "method": method,
            "path": path,
            "count": v["count"],
            "avg": avg,
            "min": v["min"],
            "max": v["max"],
        })

    by_count = sorted(endpoints, key=lambda e: e["count"], reverse=True)
    by_avg = sorted([e for e in endpoints if e["avg"] is not None],
                    key=lambda e: e["avg"], reverse=True)
    by_max = sorted([e for e in endpoints if e["max"] is not None],
                    key=lambda e: e["max"], reverse=True)

    return endpoints, by_count, by_avg, by_max

# ---------------- THRESHOLDS ----------------
def calculate_thresholds(avg_vals, max_vals):
    mean_avg, std_avg = mean_std(avg_vals)
    sorted_max = sorted(max_vals)
    p95_index = int(0.95 * (len(sorted_max) - 1)) if sorted_max else 0
    p95_max = sorted_max[p95_index] if sorted_max else 0.0

    return {
        "mean_avg": mean_avg,
        "std_avg": std_avg,
        "avg_threshold": mean_avg + std_avg,
        "peak_threshold": max(1.0, p95_max),
        "min_calls": 3,
        "top_n": 5,
    }

# ---------------- BOTTLENECK LOGIC ----------------
def identify_bottlenecks(endpoints, endpoints_by_avg, thresholds):
    bottlenecks = []
    seen = set()

    def add(e, reason):
        key = (e["method"], e["path"])
        if key not in seen:
            bottlenecks.append({**e, "reason": reason})
            seen.add(key)

    for e in endpoints:
        if (
            e["avg"] is not None and
            e["count"] >= thresholds["min_calls"] and
            e["avg"] >= thresholds["avg_threshold"]
        ):
            add(e, "high_avg_latency")

    for e in endpoints:
        if e["max"] is not None and e["max"] >= thresholds["peak_threshold"]:
            add(e, "high_peak_latency")

    for e in endpoints_by_avg[:thresholds["top_n"]]:
        add(e, "candidate_slow_endpoint")

    return bottlenecks

# ---------------- LOAD DATA ----------------
def load_profiler_data(db_path):
    if not os.path.exists(db_path):
        return {"error": f"DB not found: {db_path}"}

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    table, error = detect_profiler_table(cur)
    if error:
        return {"error": error}

    cols = [r["name"] for r in cur.execute(f"PRAGMA table_info({table})").fetchall()]
    path_col = next((c for c in cols if "path" in c.lower()), None)
    method_col = next((c for c in cols if "method" in c.lower()), None)
    elapsed_col = next((c for c in cols if "elapsed" in c.lower() or "time" in c.lower()), None)

    rows = cur.execute(f"SELECT * FROM {table}").fetchall()
    aggs, samples = aggregate_rows(rows, path_col, method_col, elapsed_col)
    endpoints, by_count, by_avg, by_max = build_endpoints(aggs)

    avg_vals = [e["avg"] for e in endpoints if e["avg"] is not None]
    max_vals = [e["max"] for e in endpoints if e["max"] is not None]

    thresholds = calculate_thresholds(avg_vals, max_vals)
    bottlenecks = identify_bottlenecks(endpoints, by_avg, thresholds)

    conn.close()

    return {
        "table": table,
        "total_rows": len(rows),
        "overall_mean": thresholds["mean_avg"],
        "overall_std": thresholds["std_avg"],
        "endpoints_by_avg": by_avg,
        "endpoints_by_max": by_max,
        "bottlenecks": bottlenecks,
        "sample_rows": samples,
    }

# ---------------- TEMPLATE ----------------
TEMPLATE = """
<!doctype html>
<html>
<head>
  <title>Profiler Report</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    body { background:#f8f9fa; }
    .card { margin-bottom: 1rem; }
  </style>
</head>
<body>
<div class="container-fluid my-4">

<h2>Profiler Report</h2>
<p class="text-muted">DB: {{ db_path }} | Table: {{ data.table }}</p>

{% if data.error %}
<div class="alert alert-danger">{{ data.error }}</div>
{% else %}

<div class="alert alert-info">
Total requests: <strong>{{ data.total_rows }}</strong><br>
Mean avg latency: {{ "%.4f"|format(data.overall_mean) }} s
</div>

<h4>Bottlenecks & Candidates</h4>
<table class="table table-sm table-striped">
<thead>
<tr><th>Method</th><th>Endpoint</th><th>Count</th><th>Avg (s)</th><th>Max (s)</th><th>Reason</th></tr>
</thead>
<tbody>
{% for b in data.bottlenecks %}
<tr class="{% if 'candidate' in b.reason %}table-warning{% else %}table-danger{% endif %}">
<td>{{ b.method }}</td>
<td>{{ b.path }}</td>
<td>{{ b.count }}</td>
<td>{{ "%.4f"|format(b.avg) if b.avg else "N/A" }}</td>
<td>{{ "%.4f"|format(b.max) if b.max else "N/A" }}</td>
<td>{{ b.reason }}</td>
</tr>
{% endfor %}
</tbody>
</table>

<div class="row">
  <div class="col-md-6">
    <h5>Top Endpoints by Avg Latency</h5>
    <table class="table table-sm">
      <thead><tr><th>Method</th><th>Endpoint</th><th>Avg (s)</th></tr></thead>
      <tbody>
      {% for e in data.endpoints_by_avg[:10] %}
      <tr>
        <td>{{ e.method }}</td>
        <td>{{ e.path }}</td>
        <td>{{ "%.4f"|format(e.avg) }}</td>
      </tr>
      {% endfor %}
      </tbody>
    </table>
  </div>

  <div class="col-md-6">
    <h5>Top Endpoints by Max Latency</h5>
    <table class="table table-sm">
      <thead><tr><th>Method</th><th>Endpoint</th><th>Max (s)</th></tr></thead>
      <tbody>
      {% for e in data.endpoints_by_max[:10] %}
      <tr>
        <td>{{ e.method }}</td>
        <td>{{ e.path }}</td>
        <td>{{ "%.4f"|format(e.max) }}</td>
      </tr>
      {% endfor %}
      </tbody>
    </table>
  </div>
</div>

{% endif %}
</div>
</body>
</html>
"""

# ---------------- ROUTES ----------------
@app.route("/")
def index():
    data = load_profiler_data(DB_PATH)
    return render_template_string(TEMPLATE, data=data, db_path=DB_PATH)

@app.route("/health")
def health():
    return {"ok": True, "db_exists": os.path.exists(DB_PATH)}

# ---------------- RUN ----------------
if __name__ == "__main__":
    print(f"Profiler report running at http://{HOST}:{PORT}")
    app.run(host=HOST, port=PORT, debug=DEBUG)
