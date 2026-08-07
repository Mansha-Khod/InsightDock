from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi import FastAPI,UploadFile,File
from pydantic import BaseModel
from src.pdf_loader   import extract_text
from src.chunker      import text_to_chunks
from src.embeddings   import generate_embeddings
from src.vector_store import build_index
from src.paths        import get_paths
from src.registry     import register_document

app=FastAPI(title='InsightDocl API')

app.mount('/static',StaticFiles(directory='static'),name='static')

@app.get("/")
async def serve_frontend():
    return FileResponse("static/index.html")

class QueryRequest(BaseModel):
    question:str
    doc_stems:list[str] | None=None
    mode:str='hybrid'

@app.post("/upload")
async def upload_document(file:UploadFile=File(...)):
    file_bytes=await file.read()
    paths=get_paths(file.filename,file_bytes)
    for key in ("pdf",'txt','chunks','embeddings','index'):
        paths[key].parent.mkdir(parents=True,exists_ok=True)
    with open(paths['pdf'],'wb') as f:
        f.write(file_bytes)
    stem=paths['pdf'].stem
    if not paths['index'].exists():
        extract_text(str(paths['pdf']),str(paths['text']))
        text_to_chunks(paths['text'].name,paths['chunk'].name)
        generate_embeddings(paths['chunks'].name,paths['embeddings'].name)
        build_index(paths['embeddings'].name,paths['index'].name)
        register_document(stem,file.filename)
        return {'stem':stem,"filename":file.filename}



@app.get("/documents")
async def list_documnets():
    pass

@app.post("/query")
async def query_documents(request:QueryRequest):
    pass

@app.get("/summary/{stem}")
async def get_summary(stem:str):
    pass

@app.get("/insights/{stem}")
async def get_insights(stem:str):
    pass