from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi import FastAPI

app=FastAPI()

app.mount('/static',StaticFiles(directory='static'),name='static')

@app.get("/")
async def serve_frontend():
    return FileResponse("static/index.html")
