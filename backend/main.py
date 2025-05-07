from fastapi import FastAPI, Request
import uvicorn
import base64
import tempfile
import fitz
import json

from backend.router import chain_with_memory
from backend.chains import parse_chain
from backend.database import init_db
from backend.helper import (
    store_resume, get_resume,
    store_parsed_resume, get_parsed_resume
)

from fastapi.responses import StreamingResponse

app = FastAPI()
init_db()

@app.post("/upload")
async def upload_resume(request: Request):
    """Extract text from uploaded resume"""

    data = await request.json()

    user_id = data["user_id"]
    base64_str = data["file"]

    # Decode base64
    file_bytes = base64.b64decode(base64_str)

    # Save to temporary PDF file
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_pdf:
        tmp_pdf.write(file_bytes)
        tmp_pdf_path = tmp_pdf.name

    # Extract text with PyMuPDF
    doc = fitz.open(tmp_pdf_path)
    resume_text = "\n".join([page.get_text() for page in doc])

    store_resume(user_id, resume_text)

    return {"status": "success"} 


@app.post("/parse")
async def parse_resume(request: Request):
    """Parse resume into JSON format with LLM"""
    
    data = await request.json()
    user_id = data["user_id"]

    resume_text = get_resume(user_id)

    result = parse_chain.invoke({'resume': resume_text})
    store_parsed_resume(user_id, json.dumps(result, indent=2))

    return {"status": "success"}


@app.post("/chat")
async def chat(request: Request):
    """Chat with user regarding the resume with memory enabled"""

    data = await request.json()

    user_id = data["user_id"]
    input = data["input"]

    resume_parsed = get_parsed_resume(user_id)
    resume_str_safe = resume_parsed.replace("{", "{{").replace("}", "}}")

    # Generator function to stream tokens
    def generator():
        for chunk in chain_with_memory.stream(
            {"input": input, "resume": resume_str_safe},
            config={"configurable": {"session_id": user_id}}
        ):
            yield chunk

    return StreamingResponse(generator(), media_type="text/plain")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)