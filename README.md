# SpeedProbe 🚀

A Python benchmarking tool that downloads files from a list of URLs using two strategies — **Sequential** and **Multi-Threaded** — and compares their performance.

## Features

- 📥 Downloads files from a user-supplied URL list
- ⚡ Benchmarks **Sequential** vs **Threaded** (10 workers) download speeds
- 🔁 Handles filename conflicts automatically (e.g., `file.jpg`, `file_1.jpg`, `file_2.jpg`)
- 🛡️ Graceful error handling for HTTP errors, timeouts, and connection issues
- 📊 Prints a full performance report with speedup factor

## Project Structure

```
SpeedProbe/
├── speedprobe.py       # Main script
├── urls.txt            # Sample URL list for testing
├── requirements.txt    # Python dependencies
├── .gitignore          # Files/folders excluded from Git
└── README.md           # This file
```

## Requirements

- Python 3.7+
- `requests` library

## Installation

```bash
# Clone the repository
git clone https://github.com/your-username/speedprobe.git
cd speedprobe

# (Recommended) Create a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
python speedprobe.py
```

You will be prompted to:
1. **Enter the path to your URL file** (e.g., `urls.txt`)
2. **Choose an output folder** — custom path or auto-generated default

### Example Session

```
  ==================================================
           ⚡ SpeedProbe — Download Benchmark
  ==================================================

Enter the path of URL file: urls.txt

Where should the files be saved?
[1] Enter a custom path
[2] Use default auto-generated folder (like 'downloads_default/')

Enter 1 or 2: 2

Defaulting to : downloads_default

Total URLs to process: 15
Target output directory: ./downloads_default/

[1/2] Running Sequential Download...
  -> 15 succeeded, 0 failed.
  -> Time taken: 12.45 seconds

[2/2] Running Threaded Download (Workers: 10)...
  -> 15 succeeded, 0 failed.
  -> Time taken: 2.31 seconds

==================================================
📊 PERFORMANCE REPORT
==================================================
Sequential Time : 12.45s
Threaded Time   : 2.31s
Speedup         : 5.39x faster
```

## URL File Format

The `urls.txt` file should contain **one URL per line**. Empty lines are ignored.

```
https://example.com/file1.jpg
https://example.com/file2.pdf
https://example.com/data.json
```

> ⚠️ **Note:** Lines starting with `#` are treated as URLs by default. Remove comment lines before running, or modify the script to skip them.

## Output

Downloaded files are saved into two folders:
- `<output_folder>_sequential/` — files from the sequential run
- `<output_folder>_threaded/` — files from the threaded run

## Architecture

| Class | Role |
|---|---|
| `DownloadEngine` | The **Worker** — handles the actual HTTP download and file writing |
| `BaseRunner` | The **Manager** — holds shared state (URLs, counts, timing) |
| `SequentialRunner` | **Strategy** — runs downloads one by one |
| `ThreadedRunner` | **Strategy** — runs downloads concurrently via `ThreadPoolExecutor` |

## License

MIT License — feel free to use and modify.
