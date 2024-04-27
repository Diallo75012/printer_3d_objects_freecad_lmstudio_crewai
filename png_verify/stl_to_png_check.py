import vtk
import os


def render_stl_to_png(stl_file_path, output_image_path):
    # Create a reader for the STL file
    reader = vtk.vtkSTLReader()
    reader.SetFileName(stl_file_path)

    # Create a mapper for the STL data
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(reader.GetOutputPort())

    # Create an actor to hold the geometry
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(0.5, 0.5, 0.5)  # Color the object grey

    # Create a renderer and add the STL actor to it
    renderer = vtk.vtkRenderer()
    renderer.AddActor(actor)
    renderer.SetBackground(1, 1, 1)  # Background color: white

    # Create a render window
    render_window = vtk.vtkRenderWindow()
    render_window.AddRenderer(renderer)
    render_window.SetSize(800, 800)  # Set the size of the render window

    # Setup the camera to get a good view of the object
    camera = renderer.GetActiveCamera()
    camera.Azimuth(30)  # Rotate the camera horizontally 30 degrees
    camera.Elevation(20)  # Rotate the camera vertically 20 degrees
    renderer.ResetCamera()  # Automatically adjusts the camera settings based on the actor
    camera.Zoom(0.8)  # Zoom out slightly to ensure the whole object is visible

    # Render the scene to the render window
    render_window.Render()

    # Create a window to image filter to capture the image
    w2if = vtk.vtkWindowToImageFilter()
    w2if.SetInput(render_window)
    w2if.Update()

    # Create a PNG writer to write the image to a file
    writer = vtk.vtkPNGWriter()
    writer.SetFileName(output_image_path)
    writer.SetInputConnection(w2if.GetOutputPort())
    writer.Write()

for file in os.listdir("../stl/"):
  filename = os.fsdecode(file)
  if filename.endswith(".stl"):
    print(os.path.join("../stl/", filename))
    stl_file_path = f"{os.path.join('../stl/', filename)}"
output_image_path = "/home/creditizens/printer_3d_llm_agents/png_verify/object_3d.png"
render_stl_to_png(stl_file_path, output_image_path)

