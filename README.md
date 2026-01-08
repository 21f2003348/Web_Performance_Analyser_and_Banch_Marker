# Web Performance Analyser and Benchmark Tool

Performance profiling and benchmarking toolkit for Python applications with Flask web profiling and system benchmarks.

## Overview

**Bench_Marker**: Benchmarking suite for file I/O, database access, HTTP requests, and JSON parsing.

**Performance_Analyser**: Flask Quiz Management System with integrated flask-profiler for web application performance monitoring.

## Installation

1. **Clone and navigate to the project**

   ```bash
   git clone <repository-url>
   cd Profiling_Technique_1
   ```

2. **Set up virtual environment and install dependencies**

   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```

3. **Initialize database** (for Performance Analyser)
   ```bash
   cd Performance_Analyser/quiz_management_system
   python seed.py
   ```

## Usage

### Running Benchmarks

```bash
# JSON Parsing
python -m Bench_Marker.runners.run_json_benchmark

# File I/O
python -m Bench_Marker.runners.run_fileio_benchmark

# Database Access
python -m Bench_Marker.runners.run_db_benchmark

# HTTP Client
python -m Bench_Marker.runners.run_http_benchmark
```

Results are saved in `Bench_Marker/results/<benchmark-type>/` with timestamps.

### Running Flask Application

```bash
cd Performance_Analyser/quiz_management_system
python app.py
```

- Main app: http://localhost:5000
- Profiler: http://localhost:5000/flask_profiler

### Features

**Quiz System**:

- Register/Login at `/register` and `/login`
- Admin: Add subjects, chapters, quizzes, questions
- Users: Take quizzes and view scores

**Profiling**:

- View request times and database queries
- Monitor performance metrics at `/flask_profiler`
- Analyze slow endpoints

## Configuration

**Benchmarks**: Edit `benchmark_file.json` for test parameters.

**Flask App**: Modify `app.py` for database and profiler settings:

```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.secret_key = 'your_secret_key'  # Change in production
```

## Results

- Benchmark results: `Bench_Marker/results/` (JSON format)
- Profiler data: `flask_profiler.sqlite`
- View results: `cat Bench_Marker/results/<type>/<file>.json`

## Troubleshooting

- **Import errors**: Run commands from project root with `-m` flag
- **Database locked**: Close other processes accessing the database
- **Port in use**: Change port in app.py or kill process on port 5000
- **Missing packages**: Run `pip install -r requirements.txt`

---

**RVCE | Operating Systems (3rd Semester) | January 2026**
