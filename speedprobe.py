import os
import sys                        
import requests
import concurrent.futures
import time
import threading
from urllib.parse import urlparse


class DownloadEngine():  # THE WORKER

    def __init__(self, output_dir):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.file_lock = threading.Lock()

    def _resolve_filename(self, url):

        path = urlparse(url).path
        filename = path.split("/")[-1] or "download"  
        name, ext = os.path.splitext(filename)

        with self.file_lock:
            filepath = os.path.join(self.output_dir, filename)
            count = 1
            while os.path.exists(filepath):
                new_filename = f"{name}_{count}{ext}"
                filepath = os.path.join(self.output_dir, new_filename)
                count += 1

            with open(filepath, 'a'):
                pass
        return filepath

    def download_single(self, url):
        filepath = self._resolve_filename(url)
        try:

            response = requests.get(url, stream=True, timeout=30)

            response.raise_for_status()

            with open(filepath, "wb") as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk: 
                        file.write(chunk)
            return True, ""

        except requests.exceptions.HTTPError as http_err:
            if os.path.exists(filepath) and os.path.getsize(filepath) == 0:
                os.remove(filepath)
            return False, f"[HTTP {http_err.response.status_code}] {url}"

        except requests.exceptions.Timeout:
            if os.path.exists(filepath) and os.path.getsize(filepath) == 0:
                os.remove(filepath)
            return False, f"[TIMEOUT] {url}"

        except requests.exceptions.ConnectionError:
            if os.path.exists(filepath) and os.path.getsize(filepath) == 0:
                os.remove(filepath)
            return False, f"[DNS/CONN ERROR] {url}"

        except requests.exceptions.RequestException as e:
            if os.path.exists(filepath) and os.path.getsize(filepath) == 0:
                os.remove(filepath)
            return False, f"[REQUEST ERROR] {url} -> {e}"


class BaseRunner:  # THE MANAGER

    def __init__(self, urls, engine):
        self.urls = urls
        self.engine = engine
        self.start_time = None
        self.end_time = None
        self.success_count = 0
        self.failed_count = 0
        self.failure_log = []


class SequentialRunner(BaseRunner):  # THE Execution Strategy

    def execute(self):
        self.totalfiles = len(self.urls)
        self.start_time = time.time()
        for url in self.urls:
            success, error_msg = self.engine.download_single(url)
            if success:
                self.success_count += 1
            else:
                self.failed_count += 1
                self.failure_log.append(error_msg)
        self.end_time = time.time()


class ThreadedRunner(BaseRunner):  # THE Execution Strategy

    def execute(self, max_workers):
        self.totalfiles = len(self.urls)
        self.start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(self.engine.download_single, url) for url in self.urls]
            for future in concurrent.futures.as_completed(futures):
                success, error_msg = future.result()
                if success:
                    self.success_count += 1
                else:
                    self.failed_count += 1
                    self.failure_log.append(error_msg)
        self.end_time = time.time()


if __name__ == "__main__":

    print("""\n
      ==================================================
               ⚡ SpeedProbe — Download Benchmark
      ==================================================
      \n""")

    try:
        target_file = input("Enter the path of URL file: ").strip()
        with open(target_file, "r") as f:
            urls = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"Error: File not found -> '{target_file}'")
        sys.exit(1)
    except PermissionError:
        print(f"Error: Permission denied -> '{target_file}'")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error while reading file: {e}")
        sys.exit(1)

    if not urls:
        print("Error: The URL file is empty or has no valid URLs. Exiting.")
        sys.exit(1)

    while True:
        print("\nWhere should the files be saved?")
        print("[1] Enter a custom path")
        print("[2] Use default auto-generated folder (like 'downloads_default/')\n")

        choice = input("Enter 1 or 2: ").strip()
        if choice == "1":
            output_folder = input("Enter your Custom folder Path: ").strip()
            if not output_folder:
                print("Folder path cannot be empty. Try again.\n")
                continue
            break
        elif choice == "2":
            output_folder = "downloads_default"
            print(f"\nDefaulting to : {output_folder}\n")
            break
        else:
            print("INVALID CHOICE : You must choose 1 or 2.\n")

    print(f"Total URLs to process: {len(urls)}")
    print(f"Target output directory: ./{output_folder}/\n")

    # --- SEQUENTIAL RUN ---
    print("[1/2] Running Sequential Download...")
    engine_seq = DownloadEngine(f"{output_folder}_sequential")
    seq_runner = SequentialRunner(urls, engine_seq)
    seq_runner.execute()

    seq_time = seq_runner.end_time - seq_runner.start_time
    print(f"  -> {seq_runner.success_count} succeeded, {seq_runner.failed_count} failed.")
    print(f"  -> Time taken: {seq_time:.2f} seconds\n")

    # --- THREADED RUN ---
    print("[2/2] Running Threaded Download (Workers: 10)...")
    engine_thread = DownloadEngine(f"{output_folder}_threaded")
    thread_runner = ThreadedRunner(urls, engine_thread)
    thread_runner.execute(max_workers=10)

    thread_time = thread_runner.end_time - thread_runner.start_time
    print(f"  -> {thread_runner.success_count} succeeded, {thread_runner.failed_count} failed.")
    print(f"  -> Time taken: {thread_time:.2f} seconds\n")

    speedup = seq_time / thread_time if thread_time > 0 else float('inf')

    print("==================================================")
    print("📊 PERFORMANCE REPORT")
    print("==================================================")
    print(f"Sequential Time : {seq_time:.2f}s")
    print(f"Threaded Time   : {thread_time:.2f}s")
    print(f"Speedup         : {speedup:.2f}x faster\n")

    # --- FAILURE LOG ---
    if seq_runner.failed_count > 0:
        print("==================================================")
        print(f"⚠️  FAILURE LOG ({seq_runner.failed_count} URLs failed)")
        print("==================================================")
        for error in seq_runner.failure_log:
            print(error)
        print()

    # --- SUCCESS SUMMARY ---
    print("==================================================")
    print("✅ SUCCESS SUMMARY")
    print("==================================================")
    print(f"Total files successfully saved: {thread_runner.success_count}")
    print(f"Check './{output_folder}/' to verify naming conflict resolution (e.g., README_1.md)")