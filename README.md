## LLM 3D OBJECTS DRAWER AND LAYER SLICER FOR 3D PRINTING
This project uses LLMs to create 3D objects and then slice those objects so that they are ready to be 3D printed.
You just need to get output '.gcode' file and use it to print your 3D object. 
You can go in the folder 'printer_profile' and update it with your downloaded 'profile.json' corresponding to your 3D printer

Disclaimer: I did this project without any 3D printer that is why it stops to the generation of the sliced layers and there is no link done to 3D printer. 
See it in a positive way, you can customize the next step with your own compatible 3D printer.

# You will need:
- groq for llms
- openai for lm-studio
- langchain for the tools
- crewai and tools of crewai for the agent team work
- .env file with the environement variables: use the example_secrets_nvs.txt file as example

# how to run it
- git clone <this_repo>
- pip install -r requirements.txt
- run the watchdog file 'check_if_stl.py'
- run lm-studio and load your model (here I used TheBloke/mixtral7b)
- python3 agents_3d_printers.py

