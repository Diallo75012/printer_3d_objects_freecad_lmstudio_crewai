#### DEBUGGED VERSION ####

import FreeCAD
import Part
import os

# Create a new document
doc = FreeCAD.newDocument()

# Create a cube with sides of 23 cm
cube = doc.addObject("Part::Box", "Cube")
cube.Length = 230  # Changed to millimeters
cube.Width = 230  # Changed to millimeters
cube.Height = 230  # Changed to millimeters

# Export the cube as an STL file
file_path = "/home/creditizens/printer_3d_llm_agents/agent_stl/"
file_name = "cube.stl"
file_path_and_name = os.path.join(file_path, file_name)
doc.recompute()
Part.export(doc.Objects[0], file_path_and_name, "STL20")

# Close the document
doc.close()