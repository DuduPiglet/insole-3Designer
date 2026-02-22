from fastapi import FastAPI, UploadFile, Form, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import shutil
import os
import uuid
from src.processor import process_insole

app = FastAPI()

# Mount static files (frontend)
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

UPLOAD_DIR = "uploads"
OUTPUT_DIR = "output"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

@app.get("/")
async def read_index():
    return FileResponse('static/index.html')

@app.post("/api/process")
async def process_file(
    file: UploadFile,
    foot_length: float = Form(...),
    side: str = Form(...),
    extra_thickness: float = Form(0.0)
):
    # Save input file
    file_id = str(uuid.uuid4())
    input_ext = os.path.splitext(file.filename)[1]
    input_path = os.path.join(UPLOAD_DIR, f"{file_id}{input_ext}")
    
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Process via subprocess to ensure PyMeshLab isolation/stability
    try:
        cmd = [
            "python3", "-m", "src.processor",
            input_path, OUTPUT_DIR, str(foot_length), side, str(extra_thickness)
        ]
        import subprocess
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"Processor failed: {result.stderr}")
            
        # Parse output for path
        output_path = None
        for line in result.stdout.splitlines():
            if line.startswith("OUTPUT_PATH:"):
                output_path = line.split("OUTPUT_PATH:")[1].strip()
                break
                
        if not output_path or not os.path.exists(output_path):
             raise Exception("Processor did not return a valid output path")

        # Return URL to download
        filename = os.path.basename(output_path)
        glb_filename = filename.replace(".stl", ".glb")
        
        # Convert INPUT to GLB for visualization if needed
        # We can use pymeshlab briefly here or just in the processor?
        # Better in processor? But processor is designed for the pipeline.
        # Let's add a small helper in web_app or rely on processor to return input_glb?
        # Actually processor doesn't return input_glb. 
        # But we can assume we want to visualize the INPUT.
        # Let's run a quick conversion using pymeshlab in subprocess for the INPUT too.
        # Or just use a simple script.
        
        input_glb_path = input_path + ".glb"
        if not os.path.exists(input_glb_path):
             # Convert using trimesh
             subprocess.run([
                 "python3", "-c", 
                 f"import trimesh\nm=trimesh.load('{input_path}', force='mesh')\n"
                 f"if hasattr(m, 'visual'):\n    m.visual.face_colors = [180, 180, 180, 255]\n"
                 f"m.export('{input_glb_path}')"
             ])
        
        return {
            "status": "success", 
            "url": f"/download/{filename}", 
            "glb_url": f"/download/{glb_filename}",
            "input_glb_url": f"/download_input/{os.path.basename(input_glb_path)}"
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}

@app.get("/download/{filename}")
async def download_file(filename: str):
    path = os.path.join(OUTPUT_DIR, filename)
    if os.path.exists(path):
        return FileResponse(path)
    return {"error": "File not found"}

@app.get("/download_input/{filename}")
async def download_input_file(filename: str):
    path = os.path.join(UPLOAD_DIR, filename)
    if os.path.exists(path):
        return FileResponse(path)
    return {"error": "File not found"}
