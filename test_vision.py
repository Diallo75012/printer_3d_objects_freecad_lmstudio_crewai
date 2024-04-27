# vision llm code
# Adapted from OpenAI's Vision example 
from openai import OpenAI
import base64
import requests

# Point to the local server
client = OpenAI(base_url="http://localhost:1235/v1", api_key="lm-studio")

# Read the image and encode it to base64:
base64_image = ""
try:
  image = open("/home/creditizens/Downloads/cube.png", "rb").read()
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
        Answer using markdown like '```python True ```' if it is True and the image is what the user requested (3D cube)
        Answer using markdown like '```python False: Image human check needed, doubts about the iamge ```' it is not whatthe user requested.
        Your answer should be short and concise Just use either of the two answers provided here.
      """,
    },
    {
      "role": "user",
      "content": [
        {"type": "text", "text": "do you see a 3D cube?"},
        {
          "type": "image_url",
          "image_url": {
            "url": f"data:image/jpeg;base64,{base64_image}"
          },
        },
      ],
    }
  ],
  max_tokens=80,
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
print("Vision Answer: ", vision_answer.split('```')[1].strip('python').strip())
