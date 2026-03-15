import os
import subprocess
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import shutil

from process_data import extract_frame_by_time

app = FastAPI(title="Dynamic Belt Position API")

# Allow CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "templates" / "DATA"
XSENSOR_DIR = DATA_DIR / "XSENSOR"

class ProcessResponse(BaseModel):
    message: str
    vertical_distances_path: str
    output_dir: str

@app.post("/api/run", response_model=ProcessResponse)
async def run_pipeline(
    time_frame: float = Form(...),
    master_file: UploadFile = File(...)
):
    try:
        # 1. Save uploaded master file locally
        upload_dir = BASE_DIR / "tmp_uploads"
        upload_dir.mkdir(exist_ok=True)
        master_path = upload_dir / master_file.filename
        
        with open(master_path, "wb") as f:
            shutil.copyfileobj(master_file.file, f)
            
        # 2. Extract frame to XSENSOR folder
        XSENSOR_DIR.mkdir(parents=True, exist_ok=True)
        # Clear previous XSENSOR frame CSVs if needed
        for csv_file in XSENSOR_DIR.glob("*.csv"):
            csv_file.unlink()
            
        extracted_csv_path = extract_frame_by_time(str(master_path), time_frame, str(XSENSOR_DIR))
        
        # 3. Run Pipeline subprocess
        # python src/belt_position/main.py --test-id "web_run" --data-path templates/DATA
        print(f"Frame extracted to {extracted_csv_path}. Running pipeline...")
        cmd = [
            "python", "-m", "belt_position.main",
            "--test-id", "web_run",
            "--data-path", str(DATA_DIR)
        ]
        
        result = subprocess.run(cmd, cwd=str(BASE_DIR), capture_output=True, text=True)
        
        if result.returncode != 0:
            print("Pipeline output:", result.stdout)
            print("Pipeline errors:", result.stderr)
            raise HTTPException(status_code=500, detail=f"Pipeline failed: {result.stderr}")
            
        # 4. Construct Response pointing to output files
        excel_dir = DATA_DIR / "PROCESSED" # Wait, main.py saves vertical_distances to DATA_PROCESSED.
        # But wait, looking at main.py: save_path = cfg.DATA_PROCESSED / "vertical_distances.xlsx"
        # and animation to cfg.DATA_ROOT_DIR / "EXCEL" / "belt_position_animation.mp4" (actually create_belt_position_animations)
        
        return ProcessResponse(
            message="Pipeline completed successfully",
            vertical_distances_path="/api/download/vertical_distances.xlsx",
            output_dir="/api/download/animation"
        )
        
    except ValueError as val_e:
        raise HTTPException(status_code=400, detail=str(val_e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup uploaded file
        if 'master_path' in locals() and master_path.exists():
            master_path.unlink()

@app.get("/api/download/{filename}")
async def download_output(filename: str):
    # Depending on filename, serve from PROCESSED or EXCEL
    if filename == "vertical_distances.xlsx":
        path = DATA_DIR / "PROCESSED" / filename
    elif filename == "animation":
        # It's an mp4 or gif, wait let's check what `create_belt_position_animations` generates.
        # It typically generates an mp4
        path = DATA_DIR / "EXCEL" / "belt_position_animation.mp4"
        if not path.exists():
            path = DATA_DIR / "EXCEL" / "belt_position_animation.gif"
    else:
        raise HTTPException(status_code=404, detail="File not found")
        
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"File {filename} not generated yet.")
        
    return FileResponse(path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
