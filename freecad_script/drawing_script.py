#### DEBUGGED VERSION ####

import FreeCAD
import Part
import math

# Create a new document
doc = FreeCAD.newDocument()

# Define the length of a side
side_length = 33

# Create the vertices of the triangle
vertex1 = FreeCAD.Vector(0, 0, 0)
vertex2 = FreeCAD.Vector(side_length / 2, math.sqrt(3) / 2 * side_length, 0)
vertex3 = FreeCAD.Vector(side_length, 0, 0)

# Create the triangle
triangle = doc.addObject("Part::Feature", "Triangle")
triangle.Shape = Part.makePolygon([vertex1, vertex2, vertex3])

# Export the triangle as an STL file
doc.recompute()
file_path = "/home/creditizens/printer_3d_llm_agents/agent_stl/triangle.stl"
Part.export(triangle, file_path)