import subprocess
import threading
import os
import sys
import time

class FPSTracker:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.presentmon_path = os.path.join(self.base_dir, "PresentMon.exe")
        self.process_name = "Warframe.x64.exe"
        self.proc = None
        self.thread = None
        self.running = False
        self.frame_times = []
        self.last_fps = 0
        self.lock = threading.Lock()

    def start(self):
        if self.running:
            return

        if not os.path.exists(self.presentmon_path):
            print(f"[FPS] PresentMon.exe not found.")
            return

        # Use Absolute Path for taskkill to bypass embedded environment limits
        tk_path = r"C:\Windows\System32\taskkill.exe"
        try:
            subprocess.run(
                [tk_path, "/F", "/IM", "PresentMon.exe"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )
        except: pass

        # Switch back to STDOUT mode
        cmd = [
            self.presentmon_path,
            "--stop_existing_session",
            "--no_top",
            "--process_name", self.process_name,
            "--output_stdout"
        ]

        creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

        # Launch with a PIPE for communication
        self.proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, # Merge errors into the same pipe
            creationflags=creationflags,
            cwd=self.base_dir,
            env=os.environ
        )
        
        self.running = True
        self.thread = threading.Thread(target=self._read_stdout_loop, daemon=True)
        self.thread.start()
        print("[FPS] Tracker started (Binary Pipe mode).")

    def stop(self):
        self.running = False
        if self.proc:
            try: self.proc.terminate()
            except: pass
            self.proc = None

        tk_path = r"C:\Windows\System32\taskkill.exe"
        try:
            subprocess.run([tk_path, "/F", "/IM", "PresentMon.exe"], 
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except: pass

        if self.thread:
            self.thread.join(timeout=1)
            self.thread = None

        with self.lock:
            self.frame_times = []
            self.last_fps = 0

    def get_fps(self):
        with self.lock:
            if not self.frame_times:
                return self.last_fps
            
            avg_ms = sum(self.frame_times) / len(self.frame_times)
            self.frame_times = [] # Reset buffer for next interval
            
            if avg_ms > 0:
                self.last_fps = int(round(1000.0 / avg_ms))
            return self.last_fps

    def _read_stdout_loop(self):
        ms_idx = None
        # We read raw bytes to avoid the German character crash
        try:
            for raw_line in self.proc.stdout:
                if not self.running:
                    break

                # FORCE DECODE: Skip errors like 'ä' or 'ü' that break German Windows
                line = raw_line.decode("utf-8", errors="ignore").strip()
                if not line:
                    continue

                parts = line.split(",")

                # Find the MsBetweenPresents column dynamically
                if ms_idx is None:
                    for i, header in enumerate(parts):
                        if "msbetweenpresents" in header.lower():
                            ms_idx = i
                            break
                    continue

                if ms_idx is not None and len(parts) > ms_idx:
                    try:
                        ms = float(parts[ms_idx])
                        if ms > 0:
                            with self.lock:
                                self.frame_times.append(ms)
                    except ValueError:
                        pass
        except Exception as e:
            if self.running:
                print(f"[FPS] Pipe read error: {e}")