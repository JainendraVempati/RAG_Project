from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import os

# Import our project modules
from rag import create_vector_store, ask_question
from schemas import Question
from database import (
    document_exists,
    save_document,
    get_all_documents,
    get_document as get_document_from_db,   
                                             
                                             
)


app = FastAPI()



os.makedirs("uploads", exist_ok=True)
os.makedirs("faiss_index", exist_ok=True)  

app.mount("/static", StaticFiles(directory="static"), name="static")


templates = Jinja2Templates(directory="templates")




@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    # Check duplicate
    if document_exists(file.filename):
        return {
            "message": "Document already exists. Using the existing index.",
            "filename": file.filename
        }

    # Save uploaded file
    file_path = os.path.join("uploads", file.filename)

    content = await file.read()

    with open(file_path, "wb") as f:
        f.write(content)

    print("\nDocument Saved Successfully")

    faiss_path = f"faiss_index/{file.filename.split('.')[0]}"

   
    try:
        total_pages, total_chunks = create_vector_store(file_path, faiss_path)
    except Exception as e:
        print(e) 
        return {
            "message": "Failed to process the document."
        }

    # Saving metadata 
    save_document(
        filename=file.filename,
        filepath=file_path,
        faiss_path=faiss_path,
        pages=total_pages,
        chunks=total_chunks
    )

    return {
        "message": "Document uploaded and indexed successfully.",
        "filename": file.filename,
        "total_pages": total_pages,
        "total_chunks": total_chunks
    }



@app.post("/ask")
async def ask(data: Question):

    doc = get_document_from_db(data.filename)

    if doc is None:
        return {
            "status": "document_not_found",
            "message": "The selected document is not available.",
            "allow_web_search": True
        }

    answer = ask_question(
        data.question,
        data.mode,
        doc["faiss_path"]
    )

    return {
        "status": "ok",
        "answer": answer
    }


@app.get("/documents")
async def get_documents():
    """
    Returns all uploaded documents stored in MongoDB.
    """

    docs = get_all_documents()

    return docs


@app.get("/document/{filename}")
async def get_document(filename: str):

    doc = get_document_from_db(filename)

    if doc is None:
        return {
            "message": "Document not found."
        }

    return doc