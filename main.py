from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import PlainTextResponse
from fastapi.concurrency import run_in_threadpool
from pathlib import Path
import tempfile, uuid, os

# Docling imports
from docling.document_converter import DocumentConverter

app = FastAPI()

@app.post("/convert_to_markdown/", response_class=PlainTextResponse)
async def convert_to_markdown(file: UploadFile = File(...)):
    # Save the uploaded file to a temporary path (Docling expects a filesystem path)
    ext = Path(file.filename).suffix  # preserve file extension if present
    if not ext:
        raise HTTPException(status_code=400, detail="File must have a valid extension")
    temp_path = Path(tempfile.gettempdir()) / f"{uuid.uuid4().hex}{ext}"
    try:
        with open(temp_path, "wb") as f:
            f.write(await file.read())

        # Run Docling conversion in a thread to avoid blocking
        converter = DocumentConverter()
        result = await run_in_threadpool(converter.convert, str(temp_path))

        # Extract markdown output
        markdown_output = result.document.export_to_markdown()

        return PlainTextResponse(markdown_output)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Conversion error: {e}")

    finally:
        # Clean up the temporary file
        if temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass
