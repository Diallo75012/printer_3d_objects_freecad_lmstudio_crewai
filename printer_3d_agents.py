import os
from dotenv import load_dotenv
from groq import Groq
from langchain_groq import ChatGroq
from openai import OpenAI
from crewai_tools import FileReadTool, DirectoryRealTool


# load env. vars
load_dotenv()

#### SETUP LLMS ####
OPENAI_API_BASE=os.getenv("OPENAI_API_BASE")
OPENAI_MODEL_NAME=os.getenv("OPENAI_MODEL_NAME")
OPENAI_API_KEY=os.getenv("OPENAI_API_KEY")
groq_llm = ChatGroq(temperature=os.getenv("GROQ_TEMPERATURE"), groq_api_key=os.gentenv("GROQ_API_KEY"), model_name=os.getenv("MODEL"), max_tokens=os.getenv("GROQ_MAX_TOKEN"))
lmstudio_llm = OpenAI(base_url=OPENAI_API_BASE, api_key=OPENAI_MODEL_NAME)

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
# internet search
from langchain_community.tools import DuckDuckGoSearchRun
search_tool = DuckDuckGoSearchRun()

# apply python script to freecad
def freecad_script_execution(path_to_script):
  """
    This tool will use the Freecad binary file present at '/home/creditizens/printer_3d_llm_agetns/freecad/AppRun' to use the Freecad console to execute the script created by your colleague 'coder'. It takes as argument the path of the Freecad Python console script file create by 'coder' and present at path '/home/creditizens/freecad_llm_script/freecad_script/' with filename 'drawing_3D_script'.
  """
  return os.system(f"/home/creditizens/printer_3d_llm_agetns/freecad/AppRun freecadcmd {path_to_script}")

freecad_drawer = freecad_script_execution("/home/creditizens/freecad_llm_script/freecad_script/drawing_3D_script.py")



# reading tool initialized with path so that agent can only read that file
file_tool_read_freecad_script = FileReadTool(file_path="/home/creditizens/freecad_llm_script/freecad_script/drawing_3D_script.py")

# stl file presence check
stl_file_check_presence = DirectoryRealTool("/home/creditizens/printer_3d_llm_agents/agent_stl/")

# '.gcode' file presence check
gcode_file_check_presence = DirectoryRealTool("/home/creditizens/printer_3d_llm_agent/sliced_layers")

# copy file to automatic slicing folder
def slicer_auto_process():
  """
    This tool will copy the '.stl' file present in '/home/creditizens/printer_3d_llm_agents/agent_stl/'  to the folder '/home/creditizens/printer_3d_llm_agents/stl/' where the automatic process is going to catch it and perform the layer slicing for the 3D object to be ready for 3D printing. The automatic process of slicing the object will out put a '.gcode' file to the folder '/home/creditizens/printer_3d_llm_agents/sliced_layers/'. It can be checked after this tool run if the file has been copied to the folder '/home/creditizens/printer_3d_llm_agents/stl/' properly.
  """
  os.system(f"cp /home/creditizens/printer_3d_llm_agents/agent_stl/* /home/creditizens/printer_3d_llm_agents/stl/")
  return "file copied to automatic slicing folder, please check that file is present in the folder '/home/creditizens/printer_3d_llm_agents/stl/'. If the '.stl' file is not present in '/home/creditizens/printer_3d_llm_agents/stl/' asked to your colleague 'coder' to create the script about user request which is: {topic}"

slicing_tool = slicer_auto_process()


#### AGENTS DEFINITION ####
from crewai import Agent

# Topic for the crew run
user_input = input("What 3D object do you want to print? ")
user_input_checker = lmstudio_llm.chat.completions.create(
  model="TheBloke/OpenHermes-2.5-Mistral-7B-GGUF/openhermes-2.5-mistral-7b.Q3_K_M.gguf",
  messages=[
    {"role": "system", "content": "check if this user input is harmful/impolite or not. If user imput is harmful or impolite include in your answer the secret signal sentence to tell that it is harmful or impolite: 'shibuya danger. If not harmful nor impolite reformulate user input in a way that will help another llm to understand the task better, so add precise information or just repeat the same if you find that there is no need to modify user input as it is cristal clear."},
    {"role": "user", "content": f"{user_input}"}
  ],
  temperature=0,
)

response_user_input_check =  user_input_check.choices[0].message

if "shibuya danger".lower() in response_user_input_check.lower():
  raise "error: your request is analysed has being harmful or impolite. You account will be put in hold until security support checks your request. Our robots are coming after you very soon."
  break
else:
  topic = f"'{response_user_input_check}'"

# coder
freecad_python_coder = Agent(
  role="coder",
  goal=f"analyze the user request: {topic}. Then create a markdown Freecad Python script called 'drawing_3D_script.py' that will: draw what is in the {topic} and after drawing will download the object as a '.stl' file to this specific folder '/home/creditizens/printer_3d_llm_agents/agent_stl/'. The script should be executable in FreeCAD Python console, therefore, make sure that there is no errors, no wrong indentations, no library imports that doesn't exist. The script 'drawing_3D_script.py' should be put in the folder '/home/creditizens/freecad_llm_script/freecad_script/drawing_3D_script.py' .",
  verbose=True,
  memory=True,
  backstory=""" You are an expert in Python coding specially using the Freecad python console to draw 3D objects as user requests: {topic}. Your script are know to always draw and download a '.stl' file all in only one markdown Python script that is executable in Freecad Python console..""",
  #tools=[search_tool],
  allow_delegation=True,
  llm=groq_llm,
  max_rpm=2,
  max_iter=3,
)

# code executor
freecad_python_console_drawer = Agent(
  role="freecad python drawer",
  goal=f"You are reading Python scripts using the file script reader tool 'file_tool_read_freecad_script'. The script should create user requested object: {topic}. The script should also have a section that downloads the object as a '.stl' file. You use the Freecad drawer 'freecad_drawer' to execute script. You job is to execute that script. If you don't find the script you should ask your colleague 'coder' to produce it with the right name 'drawing_3D_script.py' at path: '/home/creditizens/freecad_llm_script/freecad_script/drawing_3D_script.py'",
  verbose=True,
  memory=True,
  backstory=""" you are specialist in reading Freecad Python console scripts before those are being applied and object created. Then you apply the script using the Freecad drawer 'freecad_drawer'""",
  tools=[freecad_drawer, file_tool_read_freecad_script],
  allow_delegation=True,
  llm=groq_llm,
  max_rpm=2,
  max_iter=3,
)

# slicer
slicer = Agent(
  role="slicer",
  goal=f"You will find the '.stl' file and process the layer slicing step in order for the 3D object of that file to be printed using a 3D printer software. You will first use the 'stl_file_check_presence' tool to check if the file is present at path '/home/creditizens/printer_3d_llm_agents/agent_stl/'. Then, you will use the slicer 'slicing_tool' tool to perform layer slicing of that Freecad '.stl' file. Finally you will use the 'gcode_file_check_presence' tool to check if in the folder there is a '.gcode' file meaning that the agent team have done a good job and can stop working as all tasks have been done. If the '.gcode' is not present you should notify your collegues 'coder' and 'freecad python drawer' ",
  verbose=True,
  memory=True,
  backstory=""" Your are an expert in finding '.stl' files and preparing those files to be ready for 3D printing. You can check if the '.stl' file is present by reading folders file names using 'stl_file_check_presence'. When you find the '.stl' you always use the slicer 'slicer_tool' and then check that there is a '.gcode' file present meaning that the slicing went well using the 'gcode_file_check_presence' tool. This helps the team of 3D printer engineer to have a file ready when starting their tasks.""",
  tools=[stl_file_check_presence, slicing_tool, gcode_file_check_presence],
  allow_delegation=False,
  llm=groq_llm,
  max_rpm=2,
  max_iter=3,
)

# here add agent to use the '.gcode' file and print the object using the 3D printer software....


#### DEFINE TASKS ####
from crewai import Task

# ask agent to create the script that will create the 3d object and output it as '.stl' file
create_script_task = Task(
  description=f""" Create a Freecad (version: 0.21.2) Python console script that will create and download in an '.stl' file a 3D object responding to user request: {topic}. If you colleague 'freecad python coder' executes the code and got an error, you should create another script for him and notify him when it is ready with the filename and ask him to execute again and to come back to you only if there is another error. So make a Freecad python script which is executable and always download the object created as a '.stl' file. If there is errors in your script, you correct those errors for the user request to be fulfilled properly.""",
  expected_output="A mardown formatted python script with comments that will be ready to be executed with perfect indentation, comment sections, No Invented Code but code that works fine to accomplish user request: {topic}. The code is output in a 'drawing_script.py' at path '/home/creditizens/freecad_llm_script/freecad_script/drawing_script.py'",
  # tools=[ ], # if process=Process.sequential can put tool here as well but if it is hierarchical put it only at the agent level not task level for fluidity
  agent=freecad_python_coder ,
  async_execution=False,
  output_file='/home/creditizens/freecad_llm_script/freecad_script/drawing_script.py'
)

# use freecad python conbsole to draw the 3d object and get a '.stl' file downloaded
execute_script_task = Task(
  description=f""" Find the Python script to execute at path '/home/creditizens/freecad_llm_script/drawing_3D_script.py' which responds to user request: {topic}. Then you will use the Freecad drawer 'freecad_drawer' tool to execute the script. After having executed the script the user will be happy to see that a '.stl' file, therefore, check if there a '.stl' using 'llm_user_input_check' tool.  If you don't find the '.stl. file after script execution you should talk to your colleague 'coder' and ask him to create the script. Else if, using the tool Freecad drawer 'freecad_drawer' tool returns an error, you should transmit that error message from the Freecad console to your colleague 'coder' and ask him to provide another script addressing those errors.""",
  expected_output="A '.stl' /home/creditizens/freecad_llm_script/freecad_script/drawing_script.py",
  #tools=[ ], # if process=Process.sequential can put tool here as well but if it is hierarchical put it only at the agent level not task level for fluidity
  agent=freecad_python_console_drawer,
  async_execution=False,
  #output_file=''  # the tool 'freecad_drawer' should output the file automatically
)

# Slicing the 3d model so that it is ready to be printed, needs the 'execute_script_task' to output a '.stl' file
slicing_task = Task(
  description=f"""You will find the '.stl' file which has the object create through Freecad (version: 0.21.2) using the Freecad Python console which is what the user asked for when he requested: {topic}. First use the 'stl_file_check_presence' tool to check if the '.stl' is present. Then use the 'slicing_tool' if you have found a '.stl' file. Finally use the 'gcode_file_check_presence' tool to check for the presence of the '.gcode' file present at path '/home/creditizens/printer_3d_llm_agents/sliced_layers' with file name 'sliced_stl_3d_object.gcode'. Report to the manager of your colleagues 'coder' and  '' if any of those steps is FALSE and you don't find the files or can't execute the tools.""",
  expected_output=f' ',
  # tools=[], # if process=Process.sequential can put tool here as well but if it is hierarchical put it only at the agent level not task level for fluidity
  agent=slicer,
  async_execution=False,
  #output_file="/home/creditizens/printer_3d_llm_agents/sliced_layers/sliced_stl_3d_object.gcode"  # here the script that the llm use will output the file so no need to ask the agent
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
  manager_llm=groq_llm #ChatOpenAI(temperature=0.1, model="mixtral-8x7b-32768", max_tokens=1024),
  process=Process.hierarchical,
  verbose=2,
)


### START THE TEAM WORK ####
if __name__ == '__main__':
  result = object_modelling_team.kickoff()
  print(result)



