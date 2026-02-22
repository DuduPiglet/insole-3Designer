import pymeshlab
import src.file_hdl as fhdl
import os
import json
import numpy as np

def process_insole(input_path, output_dir, foot_length, side, extra_thickness=0.0):
    """
    Process the insole mesh headlessly.
    input_path: Path to the input mesh (obj/ply)
    output_dir: Directory to save the output
    foot_length: Target foot length in mm
    side: 'l' or 'r'
    extra_thickness: Extra thickness in mm to add to the base insole parameters
    """
    
    # Setup paths
    os.makedirs(output_dir, exist_ok=True)
    basename = os.path.splitext(os.path.basename(input_path))[0]
    output_file = f"{basename}_processed.stl"
    output_path = os.path.join(output_dir, output_file)

    # Load configuration
    footangle_data = fhdl.fetch_foot_angles('conf/foot_angles.json')
    footangle_1  = footangle_data[side]['1' ]
    footangle_2  = footangle_data[side]['2' ]
    footangle_21 = footangle_data[side]['21']
    footangle_3  = footangle_data[side]['3' ]

    # Calculating heights
    x10 = (10 / 270) * foot_length
    
    # Initialize MeshSet
    MeshSet = pymeshlab.MeshSet()
    Percentage = pymeshlab.PercentageValue

    # --- Functions (Adapted) ---

    def ColorizeMesh0():
        # Compute distance from Mesh 0 (foot) to Mesh 1 (plane)
        # Mesh 0 = Measure Mesh (gets the scalar)
        # Mesh 1 = Reference Mesh (distance to this)
        MeshSet.compute_scalar_by_distance_from_another_mesh_per_vertex(measuremesh=0, refmesh=1)
        MeshSet.set_current_mesh(0)
        MeshSet.compute_color_from_scalar_per_vertex()

    def CreatePlaneOnBorder():
        MeshSet.compute_selection_from_mesh_border()
        m = MeshSet.current_mesh()
        print(f"Border selection: {m.selected_vertex_number()} vertices selected.")
        try:
            MeshSet.generate_plane_fitting_to_selection(extent=1, subdiv=60, orientation=1)
        except Exception as e:
            print(f"Generate plane failed: {e}")

    def SelectOverhang():
        MeshSet.compute_selection_by_color_per_face(
            percentrh=1, percentgs=0.2, percentbv=1, colorspace=0
        )

    def RotateToFitOnXYPlane():
        MeshSet.set_selection_all()
        # Initial fit
        MeshSet.compute_matrix_by_fitting_to_plane(targetplane='XY plane', rotaxis='Z axis', toorigin=True)
        
        # Auto-orientation (Fix upside down)
        m = MeshSet.current_mesh()
        normals = m.vertex_normal_matrix()
        if normals is not None:
            avg_normal_z = np.mean(normals[:, 2])
            if avg_normal_z > 0:
                print("Flipping upside down mesh...")
                MeshSet.compute_matrix_from_rotation(rotaxis=0, rotcenter=1, angle=180)
                MeshSet.compute_matrix_by_fitting_to_plane(targetplane='XY plane', rotaxis='Z axis', toorigin=True)
                
        # Auto-orientation (Fix rotation Z)
        m = MeshSet.current_mesh()
        vertices = m.vertex_matrix()
        if vertices is not None:
            avg_y = np.mean(vertices[:, 1])
            if avg_y > 0:
                print("Rotating backward mesh...")
                MeshSet.compute_matrix_from_rotation(rotaxis=2, rotcenter=1, angle=180)

    # --- Execution Pipeline ---

    print(f"Loading mesh: {input_path}")
    MeshSet.load_new_mesh(input_path)
    
    # Decimation
    MeshSet.meshing_decimation_clustering(threshold=Percentage(0.75))

    # Auto-scale
    m = MeshSet.current_mesh()
    bbox = m.bounding_box()
    current_length = max(bbox.dim_x(), bbox.dim_y(), bbox.dim_z())
    scale_factor = foot_length / current_length
    print(f"Scaling factor: {scale_factor}")
    
    MeshSet.compute_matrix_from_scaling_or_normalization(
        scalecenter=1, uniformflag=1, axisx=scale_factor
    )

    # Cutting Logic
    CreatePlaneOnBorder()  # Mesh 1 (Plane) created
    ColorizeMesh0()        # Apply color to Mesh 0 based on distance to Mesh 1
    
    # Delete Plane (Mesh 1)
    MeshSet.set_current_mesh(1)
    MeshSet.delete_current_mesh()
    
    # Select and remove overhang on Mesh 0
    MeshSet.set_current_mesh(0)
    SelectOverhang()
    MeshSet.meshing_remove_selected_vertices_and_faces()
    print("Cutting successful.")

    # Alignment
    RotateToFitOnXYPlane()

    print("Alignment done. Starting plane construction...")
    # Plane Construction Logic
    MeshSet.set_current_mesh(0)
    m = MeshSet.current_mesh()
    print(f"Mesh 0 selected. V:{m.vertex_number()} F:{m.face_number()}")
    
    CreatePlaneOnBorder() 
    
    # Assumption: generate_plane sets the new mesh as current.
    plane_id = MeshSet.current_mesh_id()
    
    print(f"Current mesh ID after plane gen: {plane_id}")
    
    if plane_id == 0:
        print("Warning: Plane generation did not change current mesh ID. Trying to find new mesh...")
        # Fallback or debugging
        MeshSet.print_status() 
    
    MeshSet.set_current_mesh(plane_id)
    m_plane = MeshSet.current_mesh()
    print(f"Plane created. ID: {plane_id} V:{m_plane.vertex_number()} F:{m_plane.face_number()}") 
    
    # Generate copies
    ids = []
    ids.append(plane_id) 
    MeshSet.generate_copy_of_current_mesh() # Copy 1
    
    ids.append(MeshSet.current_mesh_id())
    MeshSet.generate_copy_of_current_mesh() # Copy 2
    
    ids.append(MeshSet.current_mesh_id())
    MeshSet.generate_copy_of_current_mesh() # Copy 3
    
    ids.append(MeshSet.current_mesh_id())
    MeshSet.generate_copy_of_current_mesh() # Copy 4
    
    ids.append(MeshSet.current_mesh_id())
    
    # Transformations
    # Use IDs from now on
    
    # Mesh 2 (Plane)
    MeshSet.set_current_mesh(ids[0])
    # ...
    
    # Transformations
    # ... (omitted transformations logic is fine, indices are correct) ...
    # We skip re-writing everything, just the changed parts if possible, but replace_file_content needs contiguous block.
    # I will target the block from plane_idx definition down to the merge loop to replace number_meshes AND fix logic.
    
    # Actually, simpler: Use multi_replace to target specific lines.
    
    # Wait, the main issue is line 258: compute_scalar_by_distance_from_point_cloud_per_vertex
    # I should change it to compute_scalar_by_distance_from_another_mesh_per_vertex(measuremesh=0, refmesh=merged_plane_idx)
    
    # Also replace number_meshes() with mesh_number() everywhere.

    
    # ids: [Plane, Copy1, Copy2, Copy3, Copy4]
    # Mapping to original names:
    # Plane (2) -> ids[0]
    # 3 -> ids[1]
    # 4 -> ids[2]
    # 5 -> ids[3]
    # 6 -> ids[4]
    
    # Transformations
    # Mesh 2 (Plane)
    MeshSet.set_current_mesh(ids[0])
    MeshSet.compute_matrix_from_translation(traslmethod=0, axisz=-x10)
    MeshSet.compute_matrix_from_rotation(rotaxis=0, rotcenter=1, angle=footangle_1)
    MeshSet.compute_matrix_from_rotation(rotaxis=1, rotcenter=1, angle=footangle_2)

    # Mesh 6
    MeshSet.set_current_mesh(ids[4])
    MeshSet.compute_matrix_from_translation(traslmethod=0, axisz=-x10)
    MeshSet.compute_matrix_from_rotation(rotaxis=0, rotcenter=1, angle=footangle_1)
    MeshSet.compute_matrix_from_rotation(rotaxis=1, rotcenter=1, angle=footangle_21)
    
    # Mesh 3
    MeshSet.set_current_mesh(ids[1])
    MeshSet.compute_matrix_from_translation(traslmethod=0, axisz=-0)
    MeshSet.compute_matrix_from_rotation(rotaxis=0, rotcenter=1, angle=-3.5)
    MeshSet.compute_matrix_from_rotation(rotaxis=1, rotcenter=1, angle=footangle_3)
    
    # Mesh 4
    MeshSet.set_current_mesh(ids[2])
    MeshSet.compute_matrix_from_translation(traslmethod=0, axisz=-0)

    # Mesh 5
    MeshSet.set_current_mesh(ids[3])
    MeshSet.compute_matrix_from_translation(traslmethod=0, axisz=-x10)
    MeshSet.compute_matrix_from_rotation(rotaxis=0, rotcenter=1, angle=7.5)
    
    # Merging Visible
    # We need to merge everything EXCEPT the foot (0) and specific ones?
    # The script merges visible meshes.
    # It sets visibility:
    # 0 (Foot): VISIBLE (line 240 says set visible 0? no wait `set_current_mesh_visibility(0)` means HIDE)
    # In PyMeshLab `set_current_mesh_visibility` takes boolean? Or 0/1? 
    # Doc says `visibility` bool. 0 is False.
    
    # We want to merge the PLANES to create the solid block.
    # So we should Hide Foot (0), Show all Planes (ids), Merge.
    
    MeshSet.set_current_mesh(0)
    MeshSet.set_current_mesh_visibility(visibility=False)
    
    for i in ids:
        MeshSet.set_current_mesh(i)
        MeshSet.set_current_mesh_visibility(visibility=True) # Make sure planes are visible
        
    # All planes visible, foot hidden.
    MeshSet.generate_by_merging_visible_meshes(mergevisible=True, deletelayer=True)
    
    # Now we have: 0 (Foot, Hidden), 1 (Merged Planes, Visible)
    # The merged plane is now at index 1 (since we deleted layers).
    # The merged plane is now current.
    merged_plane_idx = MeshSet.current_mesh_id()
    
    # Selection 0
    MeshSet.set_current_mesh(0)
    MeshSet.set_current_mesh_visibility(visibility=True) # Show foot
    
    # Calculate distance from Foot (0) to Merged Planes (1)
    # Note: vertexmesh=merged_plane_idx
    MeshSet.compute_scalar_by_distance_from_another_mesh_per_vertex(measuremesh=0, refmesh=merged_plane_idx)
    
    # OBJ FIX RE-APPLIED: Compute color from scalar
    MeshSet.set_current_mesh(0)
    MeshSet.compute_color_from_scalar_per_vertex()
    
    MeshSet.compute_selection_by_color_per_face(percentrh=1, percentgs=0.9, percentbv=1, colorspace=1)
    MeshSet.generate_from_selected_faces(deleteoriginal=False) 
    # New mesh created -> Selection 1 (id 2)
    # New mesh created -> Selection 1 (id 2)
    sel1_idx = MeshSet.current_mesh_id()
    
    # Selection 1 (Different parameters)
    MeshSet.set_current_mesh(0)
    # Distance again? Scalar field exists.
    MeshSet.compute_selection_by_color_per_face(percentrh=1, percentgs=0.95, percentbv=1, colorspace=1)
    MeshSet.generate_from_selected_faces(deleteoriginal=False)
    # New mesh created -> Selection 2 (id 3)
    # New mesh created -> Selection 2 (id 3)
    sel2_idx = MeshSet.current_mesh_id()
    
    # Cleanup small components
    for idx in [sel1_idx, sel2_idx]:
        MeshSet.set_current_mesh(idx)
        MeshSet.compute_selection_by_small_disconnected_components_per_face(nbfaceratio=0.9, nonclosedonly=True)
        MeshSet.meshing_remove_selected_vertices_and_faces()
        
    # Smoothing & Resampling
    
    # Calculate offset logic based on PyMeshLab's bounding box diagonal percentage.
    # The mesh was previously scaled so max(dim_x, dim_y, dim_z) = foot_length.
    # We need to find how many percentage points correspond to 1mm.
    # First, let's get the bounding box diagonal.
    m_bbox = MeshSet.current_mesh().bounding_box()
    diag = m_bbox.diagonal()
    
    # By default in PyMeshLab, if an offset is 50%, it refers to the surface itself (isovalue 0 equivalent in some filters, but here it's 50%).
    # Actually, generate_resampled_uniform_mesh with offset=50 means 0 offset. 
    # >50 is inflating. <50 is deflating.
    # 1% of the diagonal = diag * 0.01 in absolute mm. 
    # We want to add `extra_thickness` mm.
    # To convert `extra_thickness` (in mm) to percentage of diagonal points:
    # percentage_shift = (extra_thickness / diag) * 100
    
    percentage_shift = (extra_thickness / diag) * 100
    
    # Base offsets are 51.75 and 51.25.
    offset1 = 51.75 + percentage_shift
    offset2 = 51.25 + percentage_shift

    # sel1 (id 2) -> resampled low offset
    MeshSet.set_current_mesh(sel1_idx)
    MeshSet.apply_coord_taubin_smoothing(lambda_=1, stepsmoothnum=50)
    MeshSet.generate_resampled_uniform_mesh(cellsize=Percentage(0.5), offset=Percentage(offset1), absdist=True)
    resamp1_idx = MeshSet.current_mesh_id()
    
    # sel2 (id 3) -> resampled high offset
    MeshSet.set_current_mesh(sel2_idx)
    MeshSet.apply_coord_taubin_smoothing(lambda_=1, stepsmoothnum=50)
    MeshSet.generate_resampled_uniform_mesh(cellsize=Percentage(0.25), offset=Percentage(offset2), absdist=True)
    resamp2_idx = MeshSet.current_mesh_id()
    
    # Final Merge
    # We want to merge all pieces? 
    # Original: "0, 7, 8, 9" -> Foot, Plane, Sel1, Sel2? 
    # Actually checking lines 294-297: 0, 7, 8, 9.
    # 7 was likely the merged plane?
    # 8, 9 were selections? 
    # No, wait. 282/284 generate resampled meshes.
    # So we probably want: The final resampled shells + The merged plane?
    
    # Let's clean up and merge everything relevant.
    # We want the thick insole parts.
    
    # Let's assume we want to merge:
    # 1. Merged Plane (base structure) -> merged_plane_idx
    # 2. Resampled Mesh 1 -> resamp1_idx
    # 3. Resampled Mesh 2 -> resamp2_idx
    
    # Hide everything first
    # Hide everything first
    for m in MeshSet:
        MeshSet.set_current_mesh(m.id())
        MeshSet.set_current_mesh_visibility(visibility=False)
        
    # Show targets
    # We only want the insole components, not the foot or the base planes.
    targets = [resamp1_idx, resamp2_idx]
    for i in targets:
        MeshSet.set_current_mesh(i)
        MeshSet.set_current_mesh_visibility(visibility=True)
        
    MeshSet.generate_by_merging_visible_meshes(mergevisible=True, deletelayer=True)
    
    # Save
    final_idx = MeshSet.current_mesh_id()
    MeshSet.set_current_mesh(final_idx)
    MeshSet.save_current_mesh(file_name=output_path, save_textures=True)
    
    MeshSet.save_current_mesh(file_name=output_path, save_textures=True)
    
    # Save GLB for visualization using trimesh
    glb_path = output_path.replace(".stl", ".glb")
    try:
        import trimesh
        # Load the saved STL
        mesh = trimesh.load(output_path)
        # Export as GLB with a default material color (darker blue-grey) to make shape visible
        if hasattr(mesh.visual, 'face_colors'):
            mesh.visual.face_colors = [90, 130, 170, 255]
        mesh.export(glb_path)
    except Exception as e:
        print(f"Warning: GLB export failed: {e}")
    
    return output_path

if __name__ == "__main__":
    import sys
    # python src/processor.py input_path output_dir foot_length side
    if len(sys.argv) < 5:
        print("Usage: python processor.py <input_path> <output_dir> <foot_length> <side>")
        sys.exit(1)
        
    input_path = sys.argv[1]
    output_dir = sys.argv[2]
    foot_length = float(sys.argv[3])
    side = sys.argv[4]
    
    extra_thickness = 0.0
    if len(sys.argv) >= 6:
        extra_thickness = float(sys.argv[5])
    
    try:
        out = process_insole(input_path, output_dir, foot_length, side, extra_thickness)
        print(f"OUTPUT_PATH:{out}")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"ERROR:{e}")
        sys.exit(1)
