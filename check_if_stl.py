import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class Watcher:
  DIRECTORY_TO_WATCH = "/home/creditizens/printer_3d_llm_agents/stl/"

  def __init__(self):
    self.observer = Observer()

  def run(self):
    event_handler = Handler()
    self.observer.schedule(event_handler, self.DIRECTORY_TO_WATCH, recursive=True)
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
    if event.is_directory:
     return None

    elif event.event_type == 'created':
      # Take action when a file is created.
      print(f"Received created event - {event.src_path}.")
      # Assuming you have CuraEngine in your PATH or provide the full path to CuraEngine
      if event.src_path.endswith('.stl'):
        os.system(f"/home/creditizens/printer_3d_llm_agents/ultimaker/AppRun slice -v -p -j /home/creditizens/printer_3d_llm_agents/printer_profile/profile.json -o /home/creditizens/printer_3d_llm_agents/sliced_layers/sliced_stl_3d_object.gcode -l {event.src_path}")
        print(f"Slicing started for {event.src_path}")


if __name__ == '__main__':
  w = Watcher()
  w.run()
