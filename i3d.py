import src.term_args as targs
import conf.strings as text
import src.user_prompt as upr
import src.file_hdl as fhdl
from datetime import datetime
import conf.flags as flg
import json

# Disclaimer: I had no Idea what I was doing. I just coded this script to not have to do it all by hand in Meshlab
# Don't expect anything fancy really, but it "works" somehow. If it makes sense in a anatomical way is up to the debate!
# The output file is meant to be part of a orthotic insole, it is meant to be 3D printed in a suitable material.

import pymeshlab  # Meshlab
import polyscope  # 3D GUI         or import "as MeshSet"? I have no Idea.

# Implements execurion arguments.
args = targs.menu()

inputfile_list = fhdl.fetch_inputfiles(args['i'])
if (inputfile_list == None):
    print(text.texts['warn_no_inputfile'][args['l']] % args['i'])
    exit(1)
input_file = upr.prompt_inputfile(inputfile_list, lang=args['l'])
footlength = upr.prompt_footlength(lang=args['l'])
footlength_ml = upr.prompt_footlength_ml(lang=args['l'])
foot_choise = upr.prompt_foot_choise(lang=args['l'])
scale_factor = footlength / footlength_ml
if (flg.APPEND_DATETIME == 1):
    default_output_file = "%s_%s.stl" % (''.join(input_file.split('.')[0:-1]), datetime.now().strftime("%Y%m%d_%H%M%S"))
else:
    default_output_file = "%s.stl" % (''.join(input_file.split('.')[0:-1]))
output_file = upr.prompt_outputfile_name(lang=args['l'], default_output_filename=default_output_file)
print(text.texts['end_of_work'][args['l']] % (args['o'], output_file) + '\n')

footangle_data = fhdl.fetch_foot_angles('conf/foot_angles.json')
footangle_1  = footangle_data[foot_choise]['1' ]
footangle_2  = footangle_data[foot_choise]['2' ]
footangle_21 = footangle_data[foot_choise]['21'] # 0 for torsion cut, 7.5 normal.
footangle_3  = footangle_data[foot_choise]['3' ]

MeshSet = pymeshlab.MeshSet()     # Class containing all meshes.
Percentage = pymeshlab.Percentage # Something for percentage values at some point (no idea).
polyscope.set_up_dir("neg_z_up")  # Set "upwards" direction in polyscope.
polyscope.init()

# Begin declaration of functions.
def LoadMesh():                                             # Load Mesh and decrease number of faces.
  MeshSet.load_new_mesh("%s/%s" % (args['i'], input_file))
  MeshSet.meshing_decimation_clustering(threshold=Percentage(0.75))
  MeshSet.compute_matrix_from_scaling_or_normalization(scalecenter=1, uniformflag=1, axisx=scale_factor)
  # MeshSet.meshing_decimation_quadric_edge_collapse(targetfacenum=10000)
  return

'''
def PrintLenghtOfMeshSet():
    MeshSet.__getitem__(0)
    var = len(MeshSet)                                      # No idea, didn't work i guess. Don't need it anyway.
    print("Die Anzahl der Netzkörper beträgt:", var)
    return
'''

def ShowInPolyscope():                                      # Show what has happened in Polyscope (3D GUI).
    MeshSet.current_mesh()
    MeshSet.show_polyscope()
    return

def RotateToFitOnXYPlane():                                 # Rotate the Scan of the foot (negative Z up).
    MeshSet.set_selection_all()                             # No idea how it works, but it's alway negative z up for all scans I had, so...
    # MeshSet.compute_selection_from_mesh_border()
    MeshSet.compute_matrix_by_principal_axis
    MeshSet.compute_matrix_by_fitting_to_plane(targetplane="XY plane", toorigin=True)
    MeshSet.compute_matrix_by_principal_axis
    MeshSet.compute_matrix_by_fitting_to_plane(targetplane="XY plane", toorigin=True)
    return

def CreatePlaneOnBorder():                                  # Creates a plane that covers the whole scan. You will see why.
    MeshSet.compute_selection_from_mesh_border()
    MeshSet.generate_plane_fitting_to_selection(extent=1, subdiv=60, orientation=1)
    return

def ColorizeMesh0():                                        # Colorizes the mesh according to the euclidean distance to the plane.
    MeshSet.compute_scalar_by_distance_from_point_cloud_per_vertex(coloredmesh=0, vertexmesh=1)
    return

def SelectOverhang():                                       # Selects the unnecesary part of the scan to delete it afterwards.
    MeshSet.compute_selection_by_color_per_face(percentrh=1, percentgs=0.2, percentbv=1, colorspace=0)
    return

def MoveSelectedFacesToAnotherLayer():                      # For editing certain parts of the mesh.
    MeshSet.generate_from_selected_faces(deleteoriginal=True)
    return

def SaveCurrentMesh():                                      # For creating a printable file format.
    MeshSet.save_current_mesh(file_name="%s/%s" % (args['o'], output_file), save_textures=True)
    return
# End of declaration of the functions (not all are being used I guess).

# Calculating heights for the plane construct.
x70 = (70 / 270) * footlength
x60 = (60 / 270) * footlength
x50 = (50 / 270) * footlength
x40 = (40 / 270) * footlength # Some values, bullshit I guess.
x30 = (30 / 270) * footlength # This was for maintaining correct relative distances of the planes.
x20 = (20 / 270) * footlength
x10 = (10 / 270) * footlength # Only x10 is being used.
# End of calculations.

LoadMesh()
ShowInPolyscope()

# Begin cutting.
MeshSet.set_current_mesh(0)
CreatePlaneOnBorder()  # Remove imprint from overhang.
ColorizeMesh0()
MeshSet.set_current_mesh(1)
MeshSet.delete_current_mesh()
MeshSet.set_current_mesh(0)
SelectOverhang()
MeshSet.meshing_remove_selected_vertices_and_faces()
print("Cutting successful.")
# End cutting.

ShowInPolyscope()

RotateToFitOnXYPlane()

#MeshSet.save_current_mesh(file_name="Filmed and edited.stl", save_textures=True) # Uncomment here for saving just the aligned scan.

ShowInPolyscope()

# Start plane construct.
MeshSet.set_current_mesh(0)
CreatePlaneOnBorder()

MeshSet.set_current_mesh(2)
MeshSet.generate_copy_of_current_mesh() # 3
MeshSet.generate_copy_of_current_mesh() # 4
MeshSet.generate_copy_of_current_mesh() # 5
MeshSet.generate_copy_of_current_mesh() # 6

MeshSet.set_current_mesh(2)
MeshSet.compute_matrix_from_translation(traslmethod=0, axisz=-x10)
MeshSet.compute_matrix_from_rotation(rotaxis=0, rotcenter=1, angle=footangle_1)  # Front.
MeshSet.compute_matrix_from_rotation(rotaxis=1, rotcenter=1, angle=footangle_2)  # Front tilt.

MeshSet.set_current_mesh(6)
MeshSet.compute_matrix_from_translation(traslmethod=0, axisz=-x10)
MeshSet.compute_matrix_from_rotation(rotaxis=0, rotcenter=1, angle=footangle_1)  # Second front.
MeshSet.compute_matrix_from_rotation(rotaxis=1, rotcenter=1, angle=footangle_21) # Second front tilt.

MeshSet.set_current_mesh(3)
MeshSet.compute_matrix_from_translation(traslmethod=0, axisz=-0)
MeshSet.compute_matrix_from_rotation(rotaxis=0, rotcenter=1, angle=-3.5)    # Arc tilt.
MeshSet.compute_matrix_from_rotation(rotaxis=1, rotcenter=1, angle=footangle_3)  # Arc.

MeshSet.set_current_mesh(4)
MeshSet.compute_matrix_from_translation(traslmethod=0, axisz=-0)            # Base plane.
# MeshSet.compute_matrix_from_rotation(rotaxis=0, rotcenter=1, angle=-5)

MeshSet.set_current_mesh(5)
MeshSet.compute_matrix_from_translation(traslmethod=0, axisz=-x10)          # Heel.
MeshSet.compute_matrix_from_rotation(rotaxis=0, rotcenter=1, angle=7.5)

print("Planes contructed.")
# End plane construct.

ShowInPolyscope()                                                           # Here you will see what this is.

# Start selection 0.
MeshSet.set_current_mesh(0)
MeshSet.set_current_mesh_visibility(0)

MeshSet.generate_by_merging_visible_meshes(mergevisible=1, deletelayer=True)

MeshSet.set_current_mesh(0)
MeshSet.set_current_mesh_visibility(1)

MeshSet.compute_scalar_by_distance_from_point_cloud_per_vertex(coloredmesh=0, vertexmesh=7, radius=2*footlength)  #!radius
MeshSet.compute_selection_by_color_per_face(percentrh=1, percentgs=0.9, percentbv=1, colorspace=1)
MeshSet.generate_from_selected_faces(deleteoriginal=0)  # 8

print("Selection 0 made.")
# End selection 0.

ShowInPolyscope()                                                           # Here you will see what this is for.

# Start selection 1.
MeshSet.set_current_mesh(0)
MeshSet.set_current_mesh_visibility(1)

MeshSet.compute_scalar_by_distance_from_point_cloud_per_vertex(coloredmesh=0, vertexmesh=7, radius=2*footlength)  #!radius
MeshSet.compute_selection_by_color_per_face(percentrh=1, percentgs=0.95, percentbv=1, colorspace=1)
MeshSet.generate_from_selected_faces(deleteoriginal=0)  # 9

print("Selection 1 made.")
# End selection 1.                                                            # Same thing for different thickness.

ShowInPolyscope()

MeshSet.set_current_mesh(8)
MeshSet.compute_selection_by_small_disconnected_components_per_face(nbfaceratio=0.9, nonclosedonly=1)
MeshSet.meshing_remove_selected_vertices_and_faces()
MeshSet.set_current_mesh(9)
MeshSet.compute_selection_by_small_disconnected_components_per_face(nbfaceratio=0.9, nonclosedonly=1)
MeshSet.meshing_remove_selected_vertices_and_faces()
print("Excess selection removed.")

ShowInPolyscope()

# Start smoothing and volumetrisation.
MeshSet.set_current_mesh(8)
MeshSet.apply_coord_taubin_smoothing(lambda_=1, stepsmoothnum=50)
MeshSet.set_current_mesh(9)
MeshSet.apply_coord_taubin_smoothing(lambda_=1, stepsmoothnum=50)
print("Smoothing successfully.")
MeshSet.set_current_mesh(8)
MeshSet.generate_resampled_uniform_mesh(cellsize=Percentage(0.5), offset=Percentage(51.75), absdist=1)
MeshSet.set_current_mesh(9)
MeshSet.generate_resampled_uniform_mesh(cellsize=Percentage(0.25), offset=Percentage(51.25), absdist=1)
# End of smoothing and volumetrisation.

ShowInPolyscope()           # Just take a look, it will make sense from now on.

#Verbinden
MeshSet.set_current_mesh(0)
MeshSet.set_current_mesh_visibility(0)
MeshSet.set_current_mesh(7)
MeshSet.set_current_mesh_visibility(0)
MeshSet.set_current_mesh(8)
MeshSet.set_current_mesh_visibility(0)
MeshSet.set_current_mesh(9)
MeshSet.set_current_mesh_visibility(0)
MeshSet.generate_by_merging_visible_meshes(mergevisible=1, deletelayer=True)
MeshSet.set_current_mesh(0)
MeshSet.set_current_mesh_visibility(1)


print("Volumetric representation completed.")
MeshSet.set_current_mesh(12)
SaveCurrentMesh()
print("Save successful, open Polyscope.")
ShowInPolyscope()

'''
left_foot_sample.ply Meshlab value: 14.119 units; real life value: 282mm
right_foot_sample.ply Meshlab value: 14.006 units; real life value: 280mm
'''
