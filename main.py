from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi import FastAPI,UploadFile,File
from pydantic import BaseModel
from src.pdf_loader   import extract_text
from src.chunker      import text_to_chunks
from src.embeddings   import generate_embeddings
from src.vector_store import build_index
from src.paths        import get_paths ,get_paths as _get_paths
from src.registry     import register_document,load_registry
from src.rag          import ask_gemini_multi
from src.executive_summary import generate_executive_summary
from src.key_points   import generate_key_points


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


def _get_paths_for_stem(stem:str)->dict:
    from config.config import REPORTS_DIR, PROCESSED_DIR, EMBEDDINGS_DIR, MODELS_DIR
    return {
        "pdf":        REPORTS_DIR    / f"{stem}.pdf",
        "txt":        PROCESSED_DIR  / f"{stem}.txt",
        "chunks":     PROCESSED_DIR  / f"{stem}_chunks.json",
        "embeddings": EMBEDDINGS_DIR / f"{stem}_embeddings.npy",
        "index":      MODELS_DIR     / f"{stem}.index",
    }

@app.get("/documents")
async def list_documnets():
    pass

@app.post("/query")
async def query_documents(request:QueryRequest):
    registry=load_registry()
    stems=request.doc_stems or list(registry.keys())
    docs_for_search=[
        {'paths':_get_paths_for_stem(s),'display_name':registry[s]['display_name']}
        for s in stems if s in registry

    ]
    answer,sources=ask_gemini_multi(
        query=request.question,
        docs=docs_for_search,
        mode=request.mode,
    )
    return {'answer':answer,'sources':sources}

@app.get("/summary/{stem}")
async def get_summary(stem:str):
    registry=load_registry()
    if stem not in registry:
        return {"error":"documnet not found"}
    paths=get_insights(stem)
    summary=generate_executive_summary(txt_path=paths['txt'].name)
    return {'stem':stem,'summary':summary}

@app.get("/insights/{stem}")
async def get_insights(stem:str):
    registry = load_registry()
    if stem not in registry:
        return {"error": "document not found"}
    paths = _get_paths_for_stem(stem)
    key_points = generate_key_points(txt_path=paths["txt"].name)
    return {"stem": stem, "key_points": key_points}