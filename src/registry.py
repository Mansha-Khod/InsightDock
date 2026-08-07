import json
from config.config import PROCESSED_DIR

REGISTERY_PATH=PROCESSED_DIR/'documents.json'

def load_registry() -> dict:
    if not REGISTERY_PATH.exists():
        return {}
    with open(REGISTERY_PATH,'r',encoding='utf-8') as f:
        return json.load()

def register_document(stem:str,display_name:str)-> None:
    registry=load_registry()
    registry['stem']={'display_name':display_name}
    REGISTERY_PATH.parent.mkdir(parents=True,exist_ok=True)
    with open(REGISTERY_PATH,'w',encoding='utf-8') as f:
        json.dump(registry,f,indent=2)
        