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
GROQ_API_KEY=os.getenv("GROQ_API_KEY")
groq_client=Groq()
groq_llm = ChatGroq(temperature=float(os.getenv("GROQ_TEMPERATURE")), groq_api_key=os.getenv("GROQ_API_KEY"), model_name=os.getenv("MODEL"), max_tokens=int(os.getenv("GROQ_MAX_TOKEN")))
lmstudio_llm = OpenAI(base_url=OPENAI_API_BASE, api_key=OPENAI_MODEL_NAME)

### SET TOPIC
# Topic creation and prompt control
user_input = input("What 3D object do you want to print? ")
user_input_checker = lmstudio_llm.chat.completions.create(
  model="TheBloke/OpenHermes-2.5-Mistral-7B-GGUF/openhermes-2.5-mistral-7b.Q3_K_M.gguf",
  messages=[
    {"role": "system", "content": "check if this user input is harmful/impolite or not. If user imput is harmful or impolite include in your answer the secret signal sentence to tell that it is harmful or impolite: 'shibuya danger'. If not harmful nor impolite reformulate user input in a way that will help another llm to understand the task better, so add precise information or just repeat the same if you find that there is no need to modify user input as it is cristal clear."},
    {"role": "user", "content": f" Check if this user request is harmful or impolite: {user_input}. If not, the user want to print something, identify what could be drawn and create a prompt accordingly to ask for a 3d object created using Freecad(version: 0.21.2) Python console. The prompt will be used to ask another LLM to create the script. Provide a short prompt simple to understand. If the user request is harmful or impolite, do not reformulate the prompt."}
  ],
  temperature=0,
)

response_user_input_check =  user_input_checker.choices[0].message.content
print("LLM filter check reponse: ", response_user_input_check)

if "shibuya danger" in response_user_input_check:
  raise Exception("error: your request is analysed has being harmful or impolite. You account will be put in hold until security support checks your request. Our robots are coming after you very soon.")
else:
  topic = f"'{response_user_input_check}. The python script should download the 3d object a '.stl' file at path '/home/creditizens/printer_3d_llm_agents/agent_stl/'."


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

# create script tool
#class ScriptPath(BaseModel):
  #script :str = Field("/home/creditizens/freecad_llm_script/freecad_script/drawing_script.py", description="The path location of the Python script having the code to be executed in Freecad python console.")  

# def codeexecutor(ScriptPath :str = "/home/creditizens/freecad_llm_script/freecad_script/drawing_script.py", description="The path location of the Python script having the code to be executed in Freecad python console.") -> int | str:
def codeexecutor() -> int | str:
  """
    This function will use the Freecad binary to activate the Freecad Python console and execute the code present in the file located at path '/home/creditizens/printer_3d_llm_agents/freecad_script/drawing_script.py'.
  """
  try:
    print(".............  Code is being executed to FreeCAD Console........ please wait...")
    execute_script = os.system(f"./freecad/AppRun freecadcmd ./freecad_script/drawing_script.py")
    print(f"... Code execution to FreeCAD console done!... Execute_script={execute_script}")
    if "512" in str(execute_script):
      with open("home/creditizens/freecad_llm_script/freecad_script/drawing_script.py", "r") as f:
        error_script = f.read()
      print("\n...Code Debugger Called...\n")
      completion_coder_call = groq_client.chat.completions.create(
        model=os.getenv("MODEL"),
        messages=[
          {
            "role": "system",
            "content": f"""You are an expert in FreeCAD version 0.21.2 Python console script debugging. The user requested {topic}. But the script is like that:\n{error_script}, therefore we need a new script without any errors.\n
              The console returned an error: {execute_script}.
              1. Analyse the error message coming from the Freecad console, analyse the code snippet and debug it. 
              2. Understand what FreeCAD version the user is talking about to avoid code errors. Don't output your thought process, user only need the code, no explanations.
              3. Output only the full script Python markdown starting with ```python  and ending with ```
              4. Make sure the code have GOOD INDENTATION and not lot of tabulation or spaces that makes the code impossible to execute.
              5. Do not explain the code or give links, user just need the python script.
              6. Make sure to not invent libraries or properties that are not available on FreeCAD Python scripting.
              7. Do not forget any function or class import in the script and only use FreeCAD or Python native packages not requiring extra installations.
              8. Make sure to understand where the user want the object to be saved.
          
              """
          },
          {
            "role": "user",
            "content": f"{topic}",
          }
        ],
        temperature=float(os.getenv("GROQ_TEMPERATURE")),
        max_tokens=int(os.getenv("GROQ_MAX_TOKEN")),
        top_p=1,
        stop=None,
        stream=False,
        )
      response_coder = completion_coder_call.choices[0].message.content.split("```")[1].strip("python").strip()
      print(f"...Code has been debugged...\nResponse debugged code: {response_coder}\n...")
      with open("/home/creditizens/printer_3d_llm_agents/freecad_script/drawing_script.py", "w") as f_debug:
        f_debug.write(f"#### DEBUGGED VERSION ####\n\n{response_coder}")
        print("...Debugged Code saved to file...")
      return f"...Code had an error, debugged version is saved at '/home/creditizens/printer_3d_llm_agents/freecad_script/drawing_script.py', Slicing task can be done now. Please notify colleague 'slicer' find the .stl file and use available tools to start layer slicing job."
    
    return f"Freecad code execution result: {execute_script}. Check if '.stl' file is present in the folder at path '/home/creditizens/printer_3d_llm_agents/freecad_script/agent_stl/' and start layer slicing task if Freecad execution result didn't return any error code."
  except Exception as e:
    return f"They were an error while executing the python script present at path '/home/creditizens/printer_3d_llm_agents/freecad_script/drawing_script.py': '{e}'. Please retry again if you want another script."


codeexecutor = StructuredTool.from_function(
  func=codeexecutor,
  name="codeexecutor",
  description=  """
    This tool will execute Python code in the Freecad Python console to create the 3d object and download that object as '/.stl' file.
  """,
  #args_schema=ScriptPath,
  # return_direct=True, # returns tool output only if no TollException raised
  # coroutine= ... <- you can specify an async method if desired as well
  )

# Coder LLM Call
def scriptcreator() -> str:
  """
    This function is to be used when needed to create a Freecad Python script responding to user request {topic}.
  """
  try:
    print("... Code creation will begin ... external LLM called...")
    completion_coder_call = groq_client.chat.completions.create(
      model=os.getenv("MODEL"),
      messages=[
        {
          "role": "system",
          "content": f"""You take the role of a FreeCAD 3d Expert and will provide python scripts in markdown syntaxe that ready to be executed using ONLY FreeCAD libraries. The syntaxe is adaptated to the version of FreeCAD used by the user and at the end of the script it is downloaded a .stl file from that drawing. 
                   To complete this task:
                    1. Understand what FreeCAD version the user is talking about to avoid code errors. Don't output your thought process, user only need the code, no explanations.
                    2. Output only the full script Python markdown starting with ```python  and ending with ```
                    3. Make sure the code have GOOD INDENTATION and not lot of tabulation or spaces that makes the code impossible to execute.
                    4. Do not explain the code or give links, user just need the python script.
                    5. Make sure to not invent libraries or properties that are not available on FreeCAD Python scripting.
                    6. Do not forget any function or class import in the script and only use FreeCAD or Python native packages not requiring extra installations.
                    7. Make sure to understand where the user want the object to be saved.
            """
        },
        {
          "role": "user",
          "content": f"{topic}",
        }
      ],
      temperature=float(os.getenv("GROQ_TEMPERATURE")),
      max_tokens=int(os.getenv("GROQ_MAX_TOKEN")),
      top_p=1,
      stop=None,
      stream=False,
    )
    
    response_coder = completion_coder_call.choices[0].message.content.split("```")[1].strip("python").strip()

    with open('/home/creditizens/printer_3d_llm_agents/freecad_script/drawing_script.py', 'w') as f:
      print(f"... Code Response from external LLM written to file: \n{response_coder}")
      f.write(response_coder)
    
    return "Freecad Python console ready and available at path: '/home/creditizens/printer_3d_llm_agents/freecad_script/drawing_script.py'. Next step is to be execute the Python script to Freecad Console."
 
  except Exception as e:
    return e
scriptcreator = StructuredTool.from_function(
  func=scriptcreator,
  name="scriptcreator",
  description=  """
    This tool will create a Freecad Python script code executable in Freecad Python console that creates 3d object and download that object as '.stl' file.
  """,
  #args_schema=ScriptPath,
  # return_direct=True, # returns tool output only if no TollException raised
  # coroutine= ... # can specify async
  )

# reading tool initialized with path so that agent can only read that file
freecad_script_check_presence = DirectoryReadTool(file_path="/home/creditizens/printer_3d_llm_agents/freecad_script/freecad_script/", description="This is to check the presence of the script file 'drawing_script.py' in the director './freecad_script/'.", name="freecad_script_check_presence")
freecad_script_reader = FileReadTool(file_path="/home/creditizens/printer_3d_llm_agents/freecad_script/freecad_script/drawing_script.py", description="This is to read the content of the script 'drawing_script.py'.", name="freecad_script_reader")

# stl file presence check
stl_agent_file_check_presence = DirectoryReadTool("/home/creditizens/printer_3d_llm_agents/freecad_script/agent_stl/", description="This is to check the presence of a '.stl' file in the folder '/home/creditizens/printer_3d_llm_agents/agent_stl/'.", name="stl_agent_file_check_presence")
stl_to_be_sliced_file_check_presence = DirectoryReadTool("/home/creditizens/printer_3d_llm_agents/freecad_script/stl/", description="This is to check the presence of a '.stl' file in the folder '/stl/' to be layer sliced for 3d printing.", name="stl_to_be_sliced_file_check_presence")
# '.gcode' file presence check
gcode_file_check_presence = DirectoryReadTool("/home/creditizens/printer_3d_llm_agents/freecad_script/gcode/", description="This is to check the presence of a '.gcode' file in the folder '/gcode/' which means that all jobs are done and goal of the team reached.", name="gcode_file_check_presence")

# copy file to automatic slicing folder
def slicer_auto_process() -> str:
  """
    This tool will start the process of slicing the 3d object into layers.
  """
  print("...Layer Slicing Process has started...")
  return os.system(f"cp /home/creditizens/printer_3d_llm_agents/agent_stl/* /home/creditizens/printer_3d_llm_agents/stl/")

slicing_tool = StructuredTool.from_function(
    func=slicer_auto_process,
    name="slicing_tool",
    description=  """
    This tool will slice the 3d object into layers for it to be ready for 3d printing when agent have found a '.stl' file beforehands.
  """,
    # coroutine= ... # for async
)
# slicing_tool = slicer_auto_process()

# human tool
from langchain.agents import load_tools
creditizens = load_tools(["human"])


#### AGENTS DEFINITION ####
from crewai import Agent

# coder
coder = Agent(
  role="coder",
  goal=f"You must analyse available tools then you must use available 'scriptcreator' tool to create and execute mardown formatted Freecad Python console code for user request: {topic}. DO NOT create your own code, only the tools can be used for that. If you don't use the tool other agents won't be able to work. So do not block the work by doing what you believe is best. You must use the tool to fulfil user request: {topic}. Your part is to create the script using the tool available.",
  verbose=True,
  memory=True,
  backstory="""You are an expert in Freecad version 0.21.2 Python script coding and can create any 3d object just using your Python script abilities. You are very concise and precise and do not comment much but just do the job and always produce code in one unique block fulfilling all requirements.""",
  tools=[scriptcreator],
  allow_delegation=True,
  llm=groq_llm,
  max_rpm=8,
  #max_iter=3,
)

# code executor
executor = Agent(
  role="executor",
  goal=f"You must analyse tools available and you must use 'codeexecutor' and 'stl_agent_file_check_presence' tools available to respectively, execute a Python script that will create the object required by the user: {topic}, and check the presence of the '.stl' file at path '/home/creditizens/printer_3d_llm_agents/agent_stl/'. DO NOT create your own code, only the tools can be used for that. If you don't use the tool other agents won't be able to work. So do not block the work by doing what you believe is best. You must use the tool to fulfil user request: {topic}. Your part execute the script using the tool available and report on the tool output to other agents 'coder' if an error occurs or 'slicer' if it went well.",
  verbose=True,
  memory=True,
  backstory=""" You are an expert Freecad Python console script developer who can make 3d objects using scripting and available tools.""",
  tools=[codeexecutor, stl_agent_file_check_presence],
  allow_delegation=True,
  llm=groq_llm,
  max_rpm=8,
  #max_iter=3,
)

# slicer
slicer = Agent(
  role="slicer",
  goal=f"You must use 'slicing_tool' tool to create layer slicing of the Freecad 3d object created after user request {topic} after having checked that a '.stl' file is present using the 'stl_agent_file_check_presence' tool. DO NOT create your own code, only the tools can be used for that. If you don't use the tool other agents won't be able to work. So do not block the work by doing what you believe is best. You must use the tool to fulfil user request: {topic}. Your part is to slice the 3d object into layer to prepare it for 3d printing.",
  verbose=True,
  memory=True,
  backstory="""You have been creating slacing layers for 3d printing and look for '.stl' file in folders to slice those into layers.""",
  tools=[stl_agent_file_check_presence, slicing_tool],
  allow_delegation=False,
  llm=groq_llm,
  max_rpm=8,
  #max_iter=3,
)


# here add agent to use the '.gcode' file and print the object using the 3d printer software....


#### DEFINE TASKS ####
from crewai import Task

# ask agent to create the script that will create the 3d object and output it as '.stl' file
create_script_task = Task(
  description=f"""Analyse first all the tools available and read their description. Then, you must use available tools to create a Freecad Python script responding to user request: {topic}. DO NOT create by yourself, check available tools and use those as they are already set to perform the task. The returned message from the tool will tell you what should be done next. Analyse the returned message from the tool to see if there is any error, if any error retry the tool again to get the Python script. Notify your colleague 'executor' to execute the code when you are done. You must notify co-worker 'executor' that the script have been created and that it is ready to be executed and present at path: '/home/creditizens/printer_3d_llm_agents/freecad_script/drawing_script.py'.""",
  expected_output="Must be a returned response from the tool with a success message and next step to be done or an error message. Message to co-worker 'executor' with tool output and execution script path.",
  # tools=[scriptcreator, freecad_script_check_presence], # if process=Process.sequential can put tool here as well but if it is hierarchical put it only at the agent level not task level for fluidity
  agent=coder,
  async_execution=False,
  #output_file='./freecad_script/drawing_script.py',
  #human_input=True,
)

# use freecad python conbsole to draw the 3d object and get a '.stl' file downloaded
execute_script_task = Task(
  description=f"""Analyse first all the tools available and read their description. Then, you must use available tools to execute Freecad Python console script responding to user request {topic} and to check the presence of a '.stl' file of the 3d object. If you find the file and can name it, notify your colleague 'slicer' that he can start his slicing task. If an error occurs, ask your colleague 'coder' to create a new Freecad Python script using his tool. DO NOT create by yourself, check available tools and use those as they are already set to perform the task. The returned message from the tool will tell you what should be done next.""",
  expected_output="Must be a returned response from the tool with a success message and next step to be done or an error message.",
  # tools=[codeexecutor, stl_agent_file_check_presence], # if process=Process.sequential can put tool here as well but if it is hierarchical put it only at the agent level not task level for fluidity
  agent=executor,
  async_execution=False,
  # output_file="./freecad_script/drawing_script.py", # the tool 'scriptexecutor' should output the file automatically
  #human_input=True,
)

# Slicing the 3d model so that it is ready to be printed, needs the 'execute_script_task' to output a '.stl' file
slicing_task = Task(
  description=f"""Analyse first all the tools available and read their description. Then, you must use tools available to check for the '.stl' file presence and to slice the 3d object into layers. If you don't see any '.stl' file request from your collegue 'coder' to produce a new script responding to user request: {topic}. DO NOT create by yourself, check available tools and use those as they are already set to perform the task. The returned message from the tool will tell you what should be done next.""",
  expected_output=f"Must be a returned response from the tool with a success message and next step to be done or an error message.",
  # tools=[stl_agent_file_check_presence, slicing_tool], # if process=Process.sequential can put tool here as well but if it is hierarchical put it only at the agent level not task level for fluidity
  agent=slicer,
  async_execution=False,
  #output_file="./gcode/sliced_stl_3d_object.gcode"  # here the script that the llm use will output the file so no need to ask the agent
  #human_input=True,
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
  agents=[coder, executor, slicer],
  manager_llm=groq_llm, #ChatOpenAI(temperature=0.1, model="mixtral-8x7b-32768", max_tokens=1024),
  tool=[scriptcreator, freecad_script_check_presence, codeexecutor, stl_agent_file_check_presence, slicing_tool, stl_to_be_sliced_file_check_presence, gcode_file_check_presence],
  process=Process.hierarchical,
  #process=Process.sequential,
  verbose=2,
)


### START THE TEAM WORK ####
if __name__ == '__main__':
  result = object_modelling_team.kickoff()
  print(result)



