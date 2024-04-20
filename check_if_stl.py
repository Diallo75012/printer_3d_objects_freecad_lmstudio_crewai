import time
import os
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class Watcher:
    DIRECTORY_TO_WATCH = "/home/creditizens/printer_3d_llm_agents/stl/"

    def __init__(self):
        self.observer = Observer()

    def run(self):
        event_handler = Handler()
        self.observer.schedule(event_handler, self.DIRECTORY_TO_WATCH, recursive=False)
        self.observer.start()
        try:
            while True:
                time.sleep(5)
        except:
            self.observer.stop()
            print("Observer Stopped")
        self.observer.join()

class Handler(FileSystemEventHandler):

    @staticmethod
    def on_any_event(event):
        if event.is_directory or not event.src_path.endswith('.stl'):
            return None

        if event.event_type == 'created':
            print(f"Received created event - {event.src_path}.")
            Handler.slice_file(event.src_path)

    @staticmethod
    def slice_file(file_path):
        base_name = os.path.basename(file_path)
        output_file = f"/home/creditizens/printer_3d_llm_agents/gcode/{base_name.replace('.stl', '.gcode')}"
        command = ["slic3r", "--layer-height", "0.2", "--fill-density", "20%", "--output", output_file, file_path]
        try:
            slicing_process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if slicing_process.returncode == 0:
                print(f"Slicing completed successfully for {file_path}")
            else:
                print(f"returncode: {slicing_process.returncode}; stdout: {slicing_process.stdout}; stderr: {slicing_process.stderr}.")
                print(f"Slicing failed for {file_path}")
        except Exception as e:
            print(f"An error occurred while slicing {file_path}: {e}")

if __name__ == '__main__':
    w = Watcher()
    w.run()
