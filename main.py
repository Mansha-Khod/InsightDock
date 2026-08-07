from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi import FastAPI,UploadFile,File
from pydantic import BaseModel

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
    pass

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