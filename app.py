from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import os
import tempfile
import shutil
from typing import List, Dict, Any
import logging
from pathlib import Path
import uuid
from process_ocr_output import process_pdf_to_json

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Bank Statement Processor API",
    description="API for processing bank statements and extracting transaction data",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create uploads directory if it doesn't exist
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/api/process-statement", response_model=Dict[str, Any])
async def process_statement(file: UploadFile = File(...)):
    """
    Process a bank statement PDF and return the extracted transaction data.
    
    - **file**: The bank statement PDF file to process
    """
    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        # # Save the uploaded file temporarily
        # unique_filename = f"{uuid.uuid4()}_{file.filename}"
        # temp_file_path = os.path.join(UPLOAD_DIR, unique_filename)

        # with open(temp_file_path, "wb") as buffer:
        #     shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"Processing file: {file.file}")
        
        # Process the PDF
        result = process_pdf_to_json(file.file)
        
        if 'error' in result:
            raise HTTPException(status_code=400, detail=result['error'])
            
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "message": "Bank Statement Processor API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
