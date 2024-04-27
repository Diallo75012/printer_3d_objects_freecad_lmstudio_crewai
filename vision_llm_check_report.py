import time
import os
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class Watcher:
    DIRECTORY_TO_WATCH = "/home/creditizens/printer_3d_llm_agents/png_verify/"

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
        if event.is_directory or not event.src_path.endswith('.png'):
            return None

        if event.event_type == 'created':
            print(f"Received created event - {event.src_path}.")
            Handler.vision_png_check(event.src_path)

    @staticmethod
    def vision_png_check(file_path):
      import base64
      import requests
      client = OpenAI(base_url="http://localhost:1235/v1", api_key="lm-studio")
      base64_image = ""
      try:
        image = open(file_path, "rb").read()
        base64_image = base64.b64encode(image).decode("utf-8")
      except:
        print("Couldn't read the image. Make sure the path is correct and the file exists.")
        exit()

      completion = client.chat.completions.create(
        model="billborkowski/llava-NousResearch_Nous-Hermes-2-Vision-GGUF/NousResearch_Nous-Hermes-2-Vision-GGUF_Q4_0.gguf",
        messages=[
          {
            "role": "system",
            "content": f"""
              This is a chat between the assistant and the user.
              The assistant is helping the user comparing user initial request to create a 3D cube to what it is seen in the image.
              Answer using markdown like '```python ```' and describe the image that you see. 
              Your answer should be short and concise Just use either of the two answers provided here.
            """,
          },
          {
            "role": "user",
            "content": [
              {"type": "text", "text": "What do you see in this image? I should be 3D object but I need to know what it look like to be before printing it to not waste resources by printing the wrong object."},
              {
                "type": "image_url",
                "image_url": {
                  "url": f"data:image/jpeg;base64,{base64_image}"
                },
              },
            ],
          }
        ],
        max_tokens=120,
        stream=True
      )
      count = 1
      vision_answer = ""
      for chunk in completion:
        print(f"Chunk{count}")
        count += 1
        if chunk.choices[0].delta.content:
          print(chunk.choices[0].delta.content, end="", flush=True)
          vision_answer += chunk.choices[0].delta.content
      final_answer = vision_answer.split('```')[1].strip('python').strip()
      with open("/home/creditizens/printer_3d_llm_agents/png_verify/vision_report.txt", "w") as report:
        report.write(f"{final_answer}")
      print("Vision Answer: ", final_answer)
      print(f"""After all agents jobs done and our assistant vision LLM review of the final object, it has responded that"\n- {final_answer}.\n\nNow all jobs are done, please act according to what is the final result of the job done by the agent team. All jobs done!\n\n""")
      return f"""After all agents jobs done and our assistant vision LLM review of the final object, it has responded that"\n- {final_answer}.\n\nNow all jobs are done, please act according to what is the final result of the job done by the agent team. All jobs done!\n\n"""
      

if __name__ == '__main__':
    w = Watcher()
    w.run()
