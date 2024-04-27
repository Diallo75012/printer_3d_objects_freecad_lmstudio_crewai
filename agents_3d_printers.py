import os
from dotenv import load_dotenv
from groq import Groq
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from openai import OpenAI
from crewai_tools import FileReadTool, DirectoryReadTool


# load env. vars
load_dotenv()

#### SETUP LLMS ####
LM_OPENAI_API_BASE=os.getenv("LM_OPENAI_API_BASE")
LM_OPENAI_MODEL_NAME=os.getenv("LM_OPENAI_MODEL_NAME")
LM_OPENAI_API_KEY=os.getenv("LM_OPENAI_API_KEY")
GROQ_API_KEY=os.getenv("GROQ_API_KEY")
groq_client=Groq()
groq_llm_mixtral_7b = ChatGroq(temperature=float(os.getenv("GROQ_TEMPERATURE")), groq_api_key=os.getenv("GROQ_API_KEY"), model_name=os.getenv("MODEL_MIXTRAL_7B"),
max_tokens=int(os.getenv("GROQ_MAX_TOKEN")))
groq_llm_llama3_70b = ChatGroq(temperature=float(os.getenv("GROQ_TEMPERATURE")), groq_api_key=os.getenv("GROQ_API_KEY"), model_name=os.getenv("MODEL_LLAMA3_70B"), max_tokens=int(os.getenv("GROQ_MAX_TOKEN")))
lmstudio_llm = OpenAI(base_url=LM_OPENAI_API_BASE, api_key=LM_OPENAI_MODEL_NAME)
openai_llm = ChatOpenAI() #OpenAI()

### SET TOPIC
# Topic creation and prompt control
user_input = input("What 3D object do you want to print? ")
# for lmstudio:
user_input_checker = lmstudio_llm.chat.completions.create(
  model="TheBloke/OpenHermes-2.5-Mistral-7B-GGUF/openhermes-2.5-mistral-7b.Q3_K_M.gguf",
# for openaillm:
#user_input_checker = openai_llm.chat.completions.create(
  #model="gpt-3.5-turbo-1106",
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
  #script :str = Field("/home/creditizens/printer_3d_llm_agents/freecad_script/drawing_script.py", description="The path location of the Python script having the code to be executed in Freecad python console.")  

# def codeexecutor(ScriptPath :str = "/home/creditizens/printer_3d_llm_agents/freecad_script/drawing_script.py", description="The path location of the Python script having the code to be executed in Freecad python console.") -> int | str:
def codeexecutor() -> int | str:
  """
    This function will use the Freecad binary to activate the Freecad Python console and execute the code present in the file located at path '/home/creditizens/printer_3d_llm_agents/freecad_script/drawing_script.py'.
  """
  print(".............  Code is being executed to FreeCAD Console........ please wait...")
  import subprocess
  # Command setup
  command = ["/home/creditizens/printer_3d_llm_agents/freecad/AppRun", "freecadcmd", "/home/creditizens/printer_3d_llm_agents/freecad_script/drawing_script.py"]
  # Execute the command
  # execute_script = os.system(f"./freecad/AppRun freecadcmd ./freecad_script/drawing_script.py")
  execute_script_process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
  execution_error = execute_script_process.stderr
  print("Errors:", execution_error)
  if "Exception while processing file" in str(execute_script_process.stderr):
    print(f"... Code execution to FreeCAD console done!... Execute_script={execute_script_process}\nHad an error ... therefore ... calling again eternal LLM to fix error and provide new script address the error: {execute_script_process.stderr}...")
    with open("home/creditizens/freecad_llm_script/freecad_script/drawing_script.py", "r") as f:
      script_that_failed = f.read()
    print("\n...Code Debugger Called...\n")
    # for groq client llm:
    completion_coder_call = groq_client.chat.completions.create(
      model=os.getenv("MODEL"),
    # for openai client llm:
    #completion_coder_call = openai_llm.chat.completions.create(
      #model="gpt-3.5-turbo-1106",
      messages=[
        {
          "role": "system",
          "content": f"""You are an expert in FreeCAD version 0.21.2 Python console script debugging. The user requested {topic}. But the script causing the error in the Freecad Python console:\n'{script_that_failed}'\n
            The console returned an error: {execution_error}. therefore we need a new script without any errors:\n
            1. Analyse the error message coming from the Freecad console, analyse the code snippet and debug it and change the code completely, something is wrong about the previous code.
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
      print("...Debugged Code saved to file... script fix will now be executed...")
    # Command setup
    command = ["/home/creditizens/printer_3d_llm_agents/freecad/AppRun", "freecadcmd", "/home/creditizens/printer_3d_llm_agents/freecad_script/drawing_script.py"]
    # Execute the command
    # execute_script = os.system(f"./freecad/AppRun freecadcmd ./freecad_script/drawing_script.py")
    execute_script_fix_process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    print("Exit Code:", execute_script_fix_process.returncode)
    print("Output:", execute_script_fix_process.stdout)
    execution_fix_error = execute_script_fix_process.stderr
    print("Errors:", execution_fix_error)
    if "Exception while processing file" in str(execute_script_fix_process.stderr):
      return "... script had an error but couldn't be fixed, this is the message of the second error: {execution_fix_error}. Ask 'coder' to keep trying to create script using this ONLY tool again and not to create his own code."
    return f"...Code had an error, debugged version is saved at '/home/creditizens/printer_3d_llm_agents/freecad_script/drawing_script.py', Slicing task can be done now. Please notify colleague 'slicer' find the .stl file and use available tools to start layer slicing job."
  return f"Freecad code execution result: {execute_script_process}. Check if '.stl' file is present in the folder at path '/home/creditizens/printer_3d_llm_agents/freecad_script/agent_stl/' and start layer slicing task."


codeexecutor = StructuredTool.from_function(
  func=codeexecutor,
  name="codeexecutor",
  description=  """
    This tool will execute Python code in the Freecad Python console to create the 3d object and download that object as '/.stl' file. I already know where the script file is saved and will execute it.
  """,
  #args_schema=ScriptPath,
  # return_direct=True, # returns tool output only if no TollException raised
  # coroutine= ... <- you can specify an async method if desired as well
  )

# Coder LLM Call
def scriptcreator() -> str:
  """
    This creates a Freecad Python script and execute it in the Freecad Python console, responding to user request {topic}.
  """
  try:
    print("... Code creation will begin ... LLM called...")
    # for groq client llm
    completion_coder_call = groq_client.chat.completions.create(
      model=os.getenv("MODEL"),
    #completion_coder_call = openai_llm.chat.completions.create(
      #model="gpt-3.5-turbo-1106",
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
      temperature=float(os.getenv("GROQ_TEMPERATURE")), # 0.1
      max_tokens=int(os.getenv("GROQ_MAX_TOKEN")), # 1024
      top_p=1,
      stop=None,
      stream=False,
    )
    
    response_coder = completion_coder_call.choices[0].message.content.split("```")[1].strip("python").strip()

    with open('/home/creditizens/printer_3d_llm_agents/freecad_script/drawing_script.py', 'w') as f:
      print(f"... Code Response from external LLM written to file: \n{response_coder}")
      f.write(response_coder)
      
    print(".............  Code is being executed to FreeCAD Console........ please wait...")
    import subprocess
    # Command setup
    command = ["/home/creditizens/printer_3d_llm_agents/freecad/AppRun", "freecadcmd", "/home/creditizens/printer_3d_llm_agents/freecad_script/drawing_script.py"]
    # Execute the command
    # execute_script = os.system(f"./freecad/AppRun freecadcmd ./freecad_script/drawing_script.py")
    execute_script_process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    execution_error = execute_script_process.stderr
    print("Errors:", execution_error)
    if "Exception while processing file" in str(execute_script_process.stderr):
      print(f"... Code execution to FreeCAD console done!... Execute_script={execute_script_process}\nHad an error ... therefore ... calling again eternal LLM to fix error and provide new script address the error: {execute_script_process.stderr}...")
      with open("/home/creditizens/printer_3d_llm_agents/freecad_script/drawing_script.py", "r") as f:
        script_that_failed = f.read()
      print("\n...Code Debugger Called...\n")
      # for lmstudioclient llm to fix the code if any issue:
      print(".... calling LLM to fix code ....")
      completion_fixcode_call = groq_client.chat.completions.create(
        model=os.getenv("MODEL"),
      # for openai client llm:
      #completion_coder_call = openai_llm.chat.completions.create(
        #model="gpt-3.5-turbo-1106",
        messages=[
          {
            "role": "system",
            "content": f"""You are an expert in FreeCAD version 0.21.2 Python console script debugging. The user requested {topic}. But the script causing the error in the Freecad Python console:\n'{script_that_failed}'\n
              The console returned an error: {execution_error}. therefore we need a new script without any errors:\n
              1. Analyse the error message coming from the Freecad console, analyse the code snippet and debug it and change the code completely, something is wrong about the previous code.
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
      response_code_fixed = completion_fixcode_call.choices[0].message.content.split("```")[1].strip("python").strip()
      print(f"...Code has been debugged...\nResponse debugged code: {response_coder}\n...")
      with open("/home/creditizens/printer_3d_llm_agents/freecad_script/drawing_script.py", "w") as f_debug:
        f_debug.write(f"#### DEBUGGED VERSION ####\n\n{response_code_fixed}")
        print("...Debugged Code saved to file...")
      fix_command = ["/home/creditizens/printer_3d_llm_agents/freecad/AppRun", "freecadcmd", "/home/creditizens/printer_3d_llm_agents/freecad_script/drawing_script.py"]
      execute_script_fix_process = subprocess.run(fix_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
      print("Errors:", execute_script_fix_process.stderr)
      return f"...Code had an error, debugged version is saved at '/home/creditizens/printer_3d_llm_agents/freecad_script/drawing_script.py', Slicing task can be done now. Please notify colleague 'slicer' find the .stl file and use available tools to start layer slicing job."
    return f"Freecad code execution result: {execute_script_process}. Check if '.stl' file is present in the folder at path '/home/creditizens/printer_3d_llm_agents/freecad_script/agent_stl/' and start layer slicing task."
    #return f" # Freecad Python console ready and available at path: '/home/creditizens/printer_3d_llm_agents/freecad_script/drawing_script.py'. Next step is to be execute the Python script to Freecad Console.\n{response_coder}"
 
  except Exception as e:
    return e

scriptcreator = StructuredTool.from_function(
  func=scriptcreator,
  name="scriptcreator",
  description=  """
    This tool will create a Freecad Python script code executable in Freecad Python console and execute it to create 3D object and download that object as '.stl' file. This tool MUST be used when wanting to create a Freecad Python script. It doesn't take any parameter as it already as the user request. Therefore, just use this when you want to create and execute Python script to Freecad Python console.
  """,
  #args_schema=ScriptPath,
  # return_direct=True, # returns tool output only if no TollException raised
  # coroutine= ... # can specify async
  )

# stl to png tool
def pngconverter() -> str:
  """
    This function will convert .stl file to .png file to have a 2D version of the 3D object requested by the user so that user can verify that the object is corresponding to his request when he said: {topic}.
  """
  for f in os.listdir("../stl/"):
    filename = os.fsdecode(f)
    if filename.endswith(".stl"):
      try:
        print("............. STL file is being converted to PNG ....... please wait...")
        import subprocess
        command = ["python3", "/home/creditizens/printer_3d_llm_agents/png_verify/stl_to_png_check.py"]
        execute_script_process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        execution_error = execute_script_process.stderr
        print("Error: ", execution_error)
        # can put here a vision LLM check of the png file or use watchdog as well for the png_verify folder to call vision LLM and get the response sent to user via notification on the vision LLM result
        return "Agent team have completed their work, STL file has been convert to PNG please verify that it is what you wanted to print. Image present in the folder '/verify_png/'.\n ***** Now vision LLM will check the image, please act according to its response *****\n**** It is an asynchronus Job: please wait until vision LLM complete his small mini report on what he sees****\n**** report will be available in the file located at path: /home/creditizens/printer_3d_llm_agents/png_verify/vision_report.txt ****"
      except Exception as e:
        return e

pngconverter = StructuredTool.from_function(
  func=pngconverter,
  name="pngconverter",
  description=  """
    This tool will convert any .stl file to a .png file so that user can verify that the 3D object is what was requested in {topic}. It is a way to have a visual check of how the 3D object looks like. It should be the last step of the process after all other tasks have been done.
  """,
  #args_schema=ScriptPath,
  # return_direct=True, # returns tool output only if no TollException raised
  # coroutine= ... # can specify async
  )

# reading tool initialized with path so that agent can only read that file
freecad_script_check_presence = DirectoryReadTool(file_path="/home/creditizens/printer_3d_llm_agents/freecad_script/freecad_script/", description="This is to check the presence of the script file 'drawing_script.py' in the director './freecad_script/'.", name="freecad_script_check_presence")
freecad_script_reader = FileReadTool(file_path="/home/creditizens/printer_3d_llm_agents/freecad_script/freecad_script/drawing_script.py", description="This is to read the content of the script 'drawing_script.py'.", name="freecad_script_reader")

# stl file presence check
stl_agent_file_check_presence = DirectoryReadTool("/home/creditizens/printer_3d_llm_agents/freecad_script/agent_stl/", description="This is to check the presence of an '.stl' file in the folder '/home/creditizens/printer_3d_llm_agents/agent_stl/'.", name="stl_agent_file_check_presence")
stl_to_be_sliced_file_check_presence = DirectoryReadTool("/home/creditizens/printer_3d_llm_agents/freecad_script/stl/", description="This is to check the presence of a '.stl' file in the folder '/stl/' to be layer sliced for 3d printing.", name="stl_to_be_sliced_file_check_presence")
# '.gcode' file presence check
gcode_file_check_presence = DirectoryReadTool("/home/creditizens/printer_3d_llm_agents/freecad_script/gcode/", description="This is to check the presence of a '.gcode' file in the folder '/gcode/' which means that all jobs are done and goal of the team reached.", name="gcode_file_check_presence")

# check vision LLM report presence "/home/creditizens/printer_3d_llm_agents/png_verify/vision_report.txt"
vision_llm_check_png_report = DirectoryReadTool("/home/creditizens/printer_3d_llm_agents/png_verify/", description="This is to check the presence of a '.txt' file in the folder '/png_verify/' which means that all jobs are done and goal of the team reached.", name="vision_llm_check_png_report")

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
  goal=f"You must analyse available tools then you must use available 'scriptcreator' tool to create and execute mardown formatted Freecad Python console code for user request: {topic}. DO NOT create your own code as the tools is automated and will do it. You must use the tool to fulfil user request: {topic}. Your part is to create the script using the tool available that will create the script and execute the script in Freecad Python console. Keep using the tool to create and execute the script until you find the .stl file in the folder using the tool available for to check the .stl files folder meaning that your goal is reached.",
  verbose=True,
  memory=True,
  backstory="""You are an expert in Freecad version 0.21.2 Python script coding and can create any 3d object just using your Python script abilities. You are very concise and precise and do not comment much but just do the job and always produce code in one unique block fulfilling all requirements.""",
  tools=[scriptcreator, stl_agent_file_check_presence],
  allow_delegation=True,
  llm=groq_llm_mixtral_7b,
  #llm=openai_llm,
  max_rpm=7,
  max_iter=5,
)

# code executor
#executor = Agent(
  #role="executor",
  #goal=f"You must analyse tools available and you must use available 'codeexecutor' and 'stl_agent_file_check_presence' tools available to respectively, execute a Python script that will create the object required by the user: {topic}, and check the presence of any file at path '/home/creditizens/printer_3d_llm_agents/agent_stl/'. DO NOT create your own code, only the tools can be used for that. If you don't use the tool other agents won't be able to work. So do not block the work by doing what you believe is best. You must use the tool to fulfil user request: {topic}. Your part execute the script using the tool available and report on the tool output to other agents 'coder' if an error occurs or 'slicer' if it went well. After this task co-worker 'slicer' can start his job when you have found a file in the '/home/creditizens/printer_3d_llm_agents/agent_stl/' folder.",
  #verbose=True,
  #memory=True,
  #backstory=""" You are an expert Freecad Python console script developer who can make 3d objects using scripting and available tools.""",
  #tools=[codeexecutor, stl_agent_file_check_presence],
  #allow_delegation=True,
  #llm=groq_llm,
  #llm=openai_llm,
  #max_rpm=6,
  #max_iter=3,
#)

# slicer
slicer = Agent(
  role="slicer",
  goal=f"You MUST use 'slicing_tool' tool to create layer slicing of the Freecad 3d object created after user request {topic}. DO NOT create your own code, only the tools can be used for that. If you don't use the tool other agents won't be able to work. So do not block the work by doing what you believe is best. You MUST use the tool to fulfil user request: {topic}. Your part is to slice the 3d object into layer to prepare it for 3d printing.",
  verbose=True,
  memory=True,
  backstory="""You have been creating slicing layers for 3d printing and you are an expert.""",
  tools=[slicing_tool],
  allow_delegation=False,
  llm=groq_llm_mixtral_7b,
  #llm=openai_llm,
  max_rpm=5,
  max_iter=3,
)

# converter for human verification
converter = Agent(
  role="converter",
  goal=f"You MUST use 'pngconverter' tool to convert STL file to PNG file for human visual verification of the created 3D object. DO NOT create your own code, only the tools can be used for that. If you don't use the tool other agents won't be able to work. So do not block the work by doing what you believe is best. You MUST use the tool to fulfil user request: {topic}. Your part is to convert the STL file to a PNG one.",
  verbose=True,
  memory=True,
  backstory="""You are an expert in converting STL files to PNG using tools available.""",
  tools=[pngconverter, vision_llm_check_png_report],
  allow_delegation=False,
  llm=groq_llm_mixtral_7b,
  #llm=openai_llm,
  max_rpm=5,
  max_iter=3,
)

# here add agent to use the '.gcode' file and print the object using the 3d printer software....


#### DEFINE TASKS ####
from crewai import Task

# ask agent to create the script that will create the 3d object and output it as '.stl' file
create_script_task = Task(
  description=f"""Analyse first all the tools available and read their description. Then, you MUST use available tools to create and execute a Freecad Python script responding to user request: {topic}. DO NOT create by yourself, check available tools and use those as they are already set to perform the task. The returned message from the tool will tell you what should be done next. Analyse the returned message from the tool to see if there is any error, if any error affecting the script to download the /stl file, retry the tool again to re-create another Python script.""",
  expected_output="MUST be a returned response from the tool with a success message and next step to be done or an error message.",
  # tools=[scriptcreator, freecad_script_check_presence], # if process=Process.sequential can put tool here as well but if it is hierarchical put it only at the agent level not task level for fluidity
  #tool=[scriptcreator],
  agent=coder,
  async_execution=False,
  #output_file='./freecad_script/drawing_script.py',
  #human_input=True,
)

# use freecad python conbsole to draw the 3d object and get a '.stl' file downloaded
#execute_script_task = Task(
  #description=f"""Analyse first all the tools available and read their description. Then, you must use available tools to execute Freecad Python console script responding to user request {topic} and to check the presence of a '.stl' file of the 3d object. If you find the file and can name it, notify your colleague 'slicer' that he can start his slicing task. If an error occurs, ask your colleague 'coder' to create a new Freecad Python script using his tool. DO NOT create by yourself, check available tools and use those as they are already set to perform the task. The returned message from the tool will tell you what should be done next.""",
  #expected_output="Must be a returned response from the tool with a success message and next step to be done or an error message.",
  # tools=[codeexecutor, stl_agent_file_check_presence], # if process=Process.sequential can put tool here as well but if it is hierarchical put it only at the agent level not task level for fluidity
  #agent=executor,
  #async_execution=False,
  # output_file="./freecad_script/drawing_script.py", # the tool 'scriptexecutor' should output the file automatically
  #human_input=True,
#)

# Slicing the 3d model so that it is ready to be printed, needs the 'execute_script_task' to output a '.stl' file
slicing_task = Task(
  description=f"""Analyse first all the tools available and read their description. Then, you MUST use tools available to slice the 3d object into layers responding to user request: {topic}. DO NOT create by yourself, check available tools and use those as they are already set to perform the task. The returned message from the tool will tell you what should be done next. When you can't use the tool ask for a script to be created by 'coder' probably the execution of th escript in Freecad Python console didn't download any 'stl file.""",
  expected_output=f"MUST be a returned response from the tool with a success message and next step to be done or an error message.",
  # tools=[stl_agent_file_check_presence, slicing_tool], # if process=Process.sequential can put tool here as well but if it is hierarchical put it only at the agent level not task level for fluidity
  #tool=[slicing_tool],
  agent=slicer,
  async_execution=False,
  #output_file="./gcode/sliced_stl_3d_object.gcode"  # here the script that the llm use will output the file so no need to ask the agent
  #human_input=True,
)

# Converting STL file to PNG task
pngconverting = Task(
  description=f"""Analyse first all the tools available and read their description. Then, you MUST use tools available to STL file to PNG for the user to be able to do human visual verification of the object created before 3D printing it to not waste resources by creating the wrong object. DO NOT create by yourself, check available tools and use those as they are already set to perform the task. The returned message from the tool will tell you what should be done next.""",
  expected_output=f"MUST be a returned response from the tool with a success message. When you can't use the tool ask for a script to be created by 'coder' probably the execution of th escript in Freecad Python console didn't download any 'stl file or 'slicer' couldn't slice any .stl file.",
  # tools=[stl_agent_file_check_presence, slicing_tool], # if process=Process.sequential can put tool here as well but if it is hierarchical put it only at the agent level not task level for fluidity
  #tool=[slicing_tool],
  agent=converter,
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

# from langchain_openai import ChatOpenAI
object_modelling_team = Crew(
  tasks=[create_script_task, slicing_task, pngconverting],
  agents=[coder, slicer, converter],
  # groq manager
  manager_llm=groq_llm_mixtral_7b, #ChatOpenAI(temperature=0.1, model="mixtral-8x7b-32768", max_tokens=1024),
  # openai manager
  #manager_llm=openai_llm,
  # tool=[scriptcreator, freecad_script_check_presence, codeexecutor, stl_agent_file_check_presence, slicing_tool, stl_to_be_sliced_file_check_presence, gcode_file_check_presence],
  process=Process.hierarchical,
  #process=Process.sequential,
  verbose=2,
)


### START THE TEAM WORK ####
if __name__ == '__main__':
  result = object_modelling_team.kickoff()
  print(result)



