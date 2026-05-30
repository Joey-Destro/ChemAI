from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import json
import tempfile
import uuid
import shutil
from typing import Optional
from services.anki_service import create_standard_compounds_deck, create_pathway_deck

app = FastAPI(
    title="Anki Biochemistry Generator API",
    docs_url=None,   # Disable Swagger UI
    redoc_url=None   # Disable ReDoc
)

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RequestData(BaseModel):
    api_key: str
    mode: str  # 'compounds' or 'pathway'

def cleanup_dir(dirpath: str):
    try:
        if os.path.exists(dirpath):
            shutil.rmtree(dirpath)
    except Exception as e:
        print(f"Error cleaning up dir {dirpath}: {e}")

@app.post("/generate")
def generate_anki_deck(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    api_key: str = Form(...),
    mode: str = Form(...) # 'compounds' or 'pathway'
):
    if not api_key:
        raise HTTPException(status_code=400, detail="Gemini API key is required")

    if mode not in ['compounds', 'pathway']:
        raise HTTPException(status_code=400, detail="Invalid mode selected")

    # Read the file content (synchronous reading is safer here since the whole block is sync to avoid blocking loop)
    content = file.file.read()

    # Sanitize the filename to prevent path traversal
    filename = os.path.basename(file.filename) if file.filename else "upload.txt"

    # Create a temporary directory for processing
    tmp_dir = tempfile.mkdtemp()

    # Save the uploaded file temporarily
    file_path = os.path.join(tmp_dir, filename)
    with open(file_path, "wb") as f:
        f.write(content)

    deck_filepath = os.path.join(tmp_dir, f"{uuid.uuid4()}.apkg")

    try:
        if mode == 'compounds':
            deck_filepath = create_standard_compounds_deck(file_path, api_key, deck_filepath)
        elif mode == 'pathway':
            deck_filepath = create_pathway_deck(file_path, api_key, deck_filepath)

        # Add cleanup task to run after response is sent
        background_tasks.add_task(cleanup_dir, tmp_dir)

        return FileResponse(
            deck_filepath,
            media_type='application/octet-stream',
            filename=f"biochemistry_{mode}.apkg"
        )
    except Exception as e:
        # Cleanup on failure
        cleanup_dir(tmp_dir)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "ok"}
