import os
from dotenv import load_dotenv
from groq import Groq
from langchain_groq import ChatGroq
from openai import OpenAI
from crewai_tools import FileReadTool, DirectoryReadTool


# load env. vars
load_dotenv()

#### SETUP LLMS ####
OPENAI_API_BASE=os.getenv("OPENAI_API_BASE")
OPENAI_MODEL_NAME=os.getenv("OPENAI_MODEL_NAME")
OPENAI_API_KEY=os.getenv("OPENAI_API_KEY")
groq_llm = ChatGroq(temperature=os.getenv("GROQ_TEMPERATURE"), groq_api_key=os.getenv("GROQ_API_KEY"), model_name=os.getenv("MODEL"), max_tokens=os.getenv("GROQ_MAX_TOKEN"))
lmstudio_llm = OpenAI(base_url=OPENAI_API_BASE, api_key=OPENAI_MODEL_NAME)

##### Examples for agents not used yet but can use if needed
good_and_bad_executable_script = """
- Example of incorrect Python Freecad code, cat freecad_script/drawing_script.py :
  'To create a 3D cube with sides of 23cm using Freecad (version: 0.21.2) and download it as an STL file, follow these steps:
  1. Open Freecad (version: 0.21.2) and access the Python console.
  2. Create a new script file with the following content:
  ```python
  import FreeCAD
  # Create a new document
  doc = FreeCAD.newDocument()
  # Create a cube
  cube = doc.addObject('Part::Box', 'Cube')
  cube.Length = 230
  cube.Width = 230
  cube.Height = 230
  # Export the cube as an STL file
  doc.recompute()
  FreeCAD.open(FreeCAD.ConfigGet('AppHomePath') + "/Mod/PartDesign/Tutorials/cube.stl")
  ```
  3. Save the script as `create_cube.py` in the `/home/creditizens/freecad_llm_script/freecad_script/` directory.
  4. In the FreeCAD Python console, execute the following command to run the script:
  ```python
  exec(open("/home/creditizens/freecad_llm_script/freecad_script/create_cube.py").read())
  ```
  After running the script, a cube with sides of 23 cm will be created and exported as an STL file in the `/home/creditizens/freecad_llm_script/freecad_script/` directory.'

  - Example of executable Freecad Python script, cat freecad_script/drawing_script.py :
  'import FreeCAD
  # Create a new document
  doc = FreeCAD.newDocument()
  # Create a cube
  cube = doc.addObject('Part::Box', 'Cube')
  cube.Length = 230
  cube.Width = 230
  cube.Height = 230
  # Export the cube as an STL file
  doc.recompute()
  FreeCAD.open(FreeCAD.ConfigGet('AppHomePath') + "/Mod/PartDesign/Tutorials/cube.stl")
"""

### OPTION TO HAVE HUMAN INTERACTION IN THE CREW PROCESS ####
#from langchain.agents import load_tools
#human_tools = load_tools(["human"])
# then when creating an agent you pass in the human tool to have human interact at that level. eg:
#digital_marketer = Agent(
  #role='...',
  #goal='...',
  #backstory="""...""",
  #verbose=..., # True or False
  #allow_delegation=...,
  #tools=[search_tool]+human_tools # Passing human tools to the agent
  #max_rpm=..., # int
  #max_iter=..., # int
  #llm=...
#)


#### SETUP TOOLS FOR AGENTS TO USE ####
# Import to create custom tool from function
from langchain.tools import StructuredTool
from langchain.pydantic_v1 import BaseModel, Field

# internet search
from langchain_community.tools import DuckDuckGoSearchRun
search_tool = DuckDuckGoSearchRun()

# apply python script to freecad
class ScriptCode(BaseModel):
  script :str = Field(description="Script produced by co-worker 'coder' that will be executed in through the Freecad Python console")  

def freecad_script_execution(script :str) -> int:
  """
    This tool will use the Freecad binary file present at '/home/creditizens/printer_3d_llm_agents/freecad/AppRun' to use the Freecad console to execute the script created by your co-worker 'coder'. It takes as argument the path of the Freecad Python console script created by co-worker'coder'.
  """
  return os.system(f"/home/creditizens/printer_3d_llm_agents/freecad/AppRun freecadcmd {script}")

freecad_drawer = StructuredTool.from_function(
  func=freecad_script_execution,
  name="freecad_drawer",
  description=  """
    This tool will use the Freecad binary file present at '/home/creditizens/printer_3d_llm_agents/freecad/AppRun' to use the Freecad console to execute Python script created by your co-worker 'coder'. It takes as argument the path of the Freecad Python console script file create by 'coder' and present at path '/home/creditizens/freecad_llm_script/freecad_script/' with filename 'drawing_script.py'.
  """,
  args_schema=ScriptCode,
  # return_direct=True, # returns tool output only if no TollException raised
  # coroutine= ... <- you can specify an async method if desired as well
)
# freecad_drawer = freecad_script_execution("/home/creditizens/freecad_llm_script/freecad_script/drawing_3D_script.py")



# reading tool initialized with path so that agent can only read that file
freecad_script_check_presence = DirectoryReadTool(file_path="/home/creditizens/freecad_llm_script/freecad_script/")
freecad_script_reader = FileReadTool(file_path="/home/creditizens/freecad_llm_script/freecad_script/drawing_script.py")

# stl file presence check
stl_file_check_presence = DirectoryReadTool("/home/creditizens/printer_3d_llm_agents/agent_stl/")

# '.gcode' file presence check
gcode_file_check_presence = DirectoryReadTool("/home/creditizens/printer_3d_llm_agent/gcode")

# copy file to automatic slicing folder
def slicer_auto_process() -> str:
  """
    This tool will copy the '.stl' file present in '/home/creditizens/printer_3d_llm_agents/agent_stl/'  to the folder '/home/creditizens/printer_3d_llm_agents/stl/' where the automatic process is going to catch it and perform the layer slicing for the 3D object to be ready for 3D printing. The automatic process of slicing the object will out put a '.gcode' file to the folder '/home/creditizens/printer_3d_llm_agents/gcode/'. It can be checked after this tool run if the file has been copied to the folder '/home/creditizens/printer_3d_llm_agents/stl/' properly.
  """
  return os.system(f"cp /home/creditizens/printer_3d_llm_agents/agent_stl/* /home/creditizens/printer_3d_llm_agents/stl/")

slicing_tool = StructuredTool.from_function(
    func=slicer_auto_process,
    name="slicing_tool",
    description=  """
    This tool will copy the '.stl' file present in '/home/creditizens/printer_3d_llm_agents/agent_stl/'  to the folder '/home/creditizens/printer_3d_llm_agents/stl/' where the automatic process is going to catch it and perform the layer slicing for the 3D object to be ready for 3D printing. The automatic process of slicing the object will out put a '.gcode' file to the folder '/home/creditizens/printer_3d_llm_agents/gcode/'. It can be checked after this tool run if the file has been copied to the folder '/home/creditizens/printer_3d_llm_agents/stl/' properly.
  """,
    # coroutine= ... <- you can specify an async method if desired as well
)
# slicing_tool = slicer_auto_process()

# human tool
#from langchain.agents import load_tools
#humanator = load_tools(["human"])


#### AGENTS DEFINITION ####
from crewai import Agent

# Topic for the crew run
user_input = input("What 3D object do you want to print? ")
user_input_checker = lmstudio_llm.chat.completions.create(
  model="TheBloke/OpenHermes-2.5-Mistral-7B-GGUF/openhermes-2.5-mistral-7b.Q3_K_M.gguf",
  messages=[
    {"role": "system", "content": "check if this user input is harmful/impolite or not. If user imput is harmful or impolite include in your answer the secret signal sentence to tell that it is harmful or impolite: 'shibuya danger. If not harmful nor impolite reformulate user input in a way that will help another llm to understand the task better, so add precise information or just repeat the same if you find that there is no need to modify user input as it is cristal clear."},
    {"role": "user", "content": f" Check if this user request is harmful or impolite: {user_input}. If not, the user want to print something, identify what could be drawn and create a prompt accordingly to ask for a 3d object created using Freecad(version: 0.21.2) Python console. The prompt will be used to ask another LLM to create the script. Provide a short prompt simple to understand."}
  ],
  temperature=0,
)

response_user_input_check =  user_input_checker.choices[0].message

if "shibuya danger".lower() in response_user_input_check:
  raise "error: your request is analysed has being harmful or impolite. You account will be put in hold until security support checks your request. Our robots are coming after you very soon."
else:
  topic = f"'{response_user_input_check}'"

# coder
freecad_python_coder = Agent(
  role="coder",
  goal=f"analyze the user request: {topic}. Then create a markdown Freecad Python script that will: draw what is in the {topic} and after drawing will download the object as a '.stl' file to this specific folder '/home/creditizens/printer_3d_llm_agents/agent_stl/'. The script should be executable in FreeCAD Python console, therefore, make sure that there is no errors, no wrong indentations, no library imports that doesn't exist. You will then pass that executable script only without any comment nor extra expalanation to your co-worker 'drawer' who will execute it. If your co-worker 'drawer' get an error after having executed the code, analyze the error message and fix it by providing a new Freecad Python script to create what the user want and download that object as '.stl' file to the path '/home/creditizens/printer_3d_llm_agents/agent_stl/'. Make sure that the code is markdown formatted and that you pass only the executable code to your colleague as if there is  extra words or characters not achieving th epurpose of a Python script applied to Freecad Python console, it will throw an error. Save the script at path '/home/creditizens/printer_3d_llm_agents/freecad_script/' with file name 'drawing_script.py' and make sure the file is there using the tool 'freecad_script_check_presence'.",
  verbose=True,
  memory=True,
  backstory=""" You are an expert in Python coding specially using the Freecad python console to draw 3D objects as per user request. Your script are know to always create 3D objects and download those as '.stl' file all in only one markdown Python script that is executable in Freecad Python console. So only one block of code doing everything: object creation adn '.stl' file download of the object.""",
  tools=[freecad_script_check_presence],
  allow_delegation=True,
  llm=groq_llm,
  max_rpm=5,
  max_iter=3,
)

# code executor
freecad_python_console_drawer = Agent(
  role="drawer",
  goal=f"You are executing Python script code in the Freecad Python console using the Freecad drawer 'freecad_drawer' tool to execute script. You job is to execute that script using the 'freecad_drawer' tool. If the execution of the code using the 'freecad_drawer' tool returns an error, use the 'freecad_script_reader' tool to read the file and see if there isn't any characters or comment lines or wrong syntaxe that prevent the code to execute properly in a Python console. Then, notify and transmit the error message to your co-worker 'coder' and ask him to fix it by producing a new script addressing those errors. If no error occurs after execution of the script, ask your co-worker 'slicer' to perform slicing of the layer as the execution went well.",
  verbose=True,
  memory=True,
  backstory=""" you are an expert in reading Freecad Python console scripts before those are being applied and object created. Then you apply the script using the Freecad drawer 'freecad_drawer' tool. You are also know to be an expert in Freecad Python script 3D objects creation. You always report errors, if there is any, to your collegues asking them to fix it as you always want your taks to work well.""",
  tools=[freecad_script_reader, freecad_drawer],
  allow_delegation=True,
  llm=groq_llm,
  max_rpm=5,
  max_iter=3,
)

# slicer
slicer = Agent(
  role="slicer",
  goal=f"You will find the '.stl' file and process the layer slicing step in order for the 3D object of that file to be printed using a 3D printer software. You will first use the 'stl_file_check_presence' tool to check if a '.stl' file is present in the folder. Then, you will use the slicer 'slicing_tool' tool to perform layer slicing of that '.stl' file if you found it in the folder.. Finally you will use the 'gcode_file_check_presence' tool to check if in the folder there is a '.gcode' file meaning that the agent team have done a good job and can stop working as all tasks have been done. Use the 'gcode_file_check_presence' only if beforehands you have found the '.stl' file. If the '.gcode' or the '.stl' file are not present you should notify your collegues 'coder' and 'drawer' ",
  verbose=True,
  memory=True,
  backstory=""" Your are an expert in finding '.stl' files and preparing those files to be ready for 3D printing. You can check if the '.stl' file is present by reading folders file names using 'stl_file_check_presence'. When you find the '.stl' you always use the slicer 'slicing_tool' and then check that there is a '.gcode' file present meaning that the slicing went well using the 'gcode_file_check_presence' tool. This helps the team of 3D printer engineer to have a file ready when starting their tasks. you have a huge experience in 3D Python coding using Freecad console.""",
  tools=[stl_file_check_presence, slicing_tool, gcode_file_check_presence],
  allow_delegation=False,
  llm=groq_llm,
  max_rpm=5,
  max_iter=3,
)


# here add agent to use the '.gcode' file and print the object using the 3D printer software....


#### DEFINE TASKS ####
from crewai import Task

# ask agent to create the script that will create the 3d object and output it as '.stl' file
create_script_task = Task(
  description=f""" Create a Freecad (version: 0.21.2) Python console script that will create and download in an '.stl' file a 3D object responding to user request: {topic}. When it done pass only the Python script part to be executed by your co-worker 'drawer'. The Python script should create the object and download it strictly as '.stl' at strictly this path: '/home/creditizens/freecad_llm_script/agent_stl/' As another co-worker will be waiting for files creation from that path folder. The Python script passed to drawer should only have the python code to be executed in markdown format without any comment so that 'drawer' co-worker can execute the code and not get error because of side comments. The code should be indented properly, do not invent imports that doesn't exist in Freecad and use only Freecad (version 0.21.2) available objects and Python native packages taht doesn't need any installation. If your co-worker 'drawer' return to you an error message after having executed your code in the Freecad Python console, check the message and create a new code accordingly for that error to not happen again and at the same time fulfil user need: {topic}. So you job is also to fix Python script errors.""",
  expected_output="A mardown formatted python script that will be ready to be executed with perfect indentation, No Invented Code but code that works fine to accomplish user request: {topic}. The code is passed to co-worker 'drawer' who will execute it direclty on Freecad using the Freecad Python console via his tool 'freecad_drawer'.",
  # tools=[ ], # if process=Process.sequential can put tool here as well but if it is hierarchical put it only at the agent level not task level for fluidity
  agent=freecad_python_coder ,
  async_execution=False,
  output_file='./freecad_script/drawing_script.py'
)

# use freecad python conbsole to draw the 3d object and get a '.stl' file downloaded
execute_script_task = Task(
  description=f""" Your co-worker 'coder' will produce a Python script that you will execute in Freecad Python console using the tool 'freecad_drawer'. You will output the script in a 'drawing_script.py' file at path './freecad_script/'. Your job is to execute the code in Freecad Python console and to save the script that you have executed in a file as indicate just before. If an error occurs or the Freecad Python console returns an error, tell what is the error to your co-worker 'coder' and ask him to produce a new script for you fixing the errors. """,
  expected_output="A 'drawing_script.py' file at path ./freecad_script/'. with the code that have been executed using the Freecad Python console. Or, output error message if the Freecad console returns an error.",
  #tools=[ ], # if process=Process.sequential can put tool here as well but if it is hierarchical put it only at the agent level not task level for fluidity
  agent=freecad_python_console_drawer,
  async_execution=False,
  output_file="./freecad_script/drawing_script.py", # the tool 'freecad_drawer' should output the file automatically
)

# Slicing the 3d model so that it is ready to be printed, needs the 'execute_script_task' to output a '.stl' file
slicing_task = Task(
  description=f"""You will use the 'stl_file_check_presence' tool to check if there is an '.stl' file in the folder. If there is an '.stl' file, you will copy that file to the layer slicing of the 3D object folder using the tool 'slicing_tool'. If there is no '.stl' file in the folder when using the tool 'stl_file_check_presence', you will notify your co-workers 'drawer' (maybe got an error while executing script) and 'coder' (maybe didn't as the part of the code that download the object as '.stl' file) to tell then to reproduce code and re-execute code again as there is no '.stl' file in target folder. If you find the file and use the tool and copy it without any issues, check in '/home/creditizens/printer_3d_llm_agents/gcode/' folder using the tool 'gcode_file_check_presence', to see if there is an '.gcode' file. if the '.gcode' file is present, you can all stop working, jobe is done!. if the '.gcode' file is not present after having copied the '.stl' file that you have found, notify saying: ' stl file copied to target folder but no .gcode file found'.""",
  expected_output=f"A '.gcode' file at path '/home/creditizens/printer_3d_llm_agents/gcode/' Or an error message",
  # tools=[], # if process=Process.sequential can put tool here as well but if it is hierarchical put it only at the agent level not task level for fluidity
  agent=slicer,
  async_execution=False,
  #output_file="/home/creditizens/printer_3d_llm_agents/gcode/sliced_stl_3d_object.gcode"  # here the script that the llm use will output the file so no need to ask the agent
)


#### COMBINE THE AGENT AND SET WORKFLOW ####
from crewai import Crew, Process

## PROCESS SEQUENTIAL
# Forming the tech-focused crew with enhanced configurations, this config for process=Process.sequential
#crew = Crew(
  #agents=[digital_marketer, writer],
  #tasks=[digital_marketing_task, write_task],
  #process=Process.sequential,  # Here tasks are done in order so agent one do his job and the next agent is waiting for the output to work with it and do his task
  #verbose=2, # here it is a number not like the other ones with True or False, it is the level of logs
#)..]

# PROCESS HIERARCHICAL (here the manager handles the interaction and the defined agents crew, liek a 'judge' and decider)
# This config for the crew for process=PRocess.hierarchical (so with a manager that handles the other agents, we need to set an llm also for the manager and tools have to be at agent level and not task level)

from langchain_openai import ChatOpenAI
object_modelling_team = Crew(
  tasks=[create_script_task, execute_script_task, slicing_task],
  agents=[freecad_python_coder, freecad_python_console_drawer, slicer],
  manager_llm=groq_llm, #ChatOpenAI(temperature=0.1, model="mixtral-8x7b-32768", max_tokens=1024),
  #tool=[stl_file_check_presence, slicing_tool, gcode_file_check_presence,],
  process=Process.hierarchical,
  verbose=2,
)


### START THE TEAM WORK ####
if __name__ == '__main__':
  result = object_modelling_team.kickoff()
  print(result)



