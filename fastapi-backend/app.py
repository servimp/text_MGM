from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from business_logic import add_text, get_texts_by_tags, add_tags, update_tags, get_texts
from pydantic import BaseModel

app = FastAPI()

# Add the CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:8080'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

class TextData(BaseModel):
    text: str
    tags: List[str] = []

@app.get('/get_texts/')
async def get_texts_route():
    return get_texts()

@app.post('/add_text/')
async def add_text_route(text_data: TextData):
    return add_text(text_data)

@app.get('/get_texts_by_tags/')
async def get_texts_by_tags_route(tags: Optional[str] = None):
    return get_texts_by_tags(tags)

@app.patch('/add_tags/{text_id}')
async def add_tags_route(text_id: str, tags: List[str]):
    return add_tags(text_id, tags)

@app.patch('/update_tags/{text_id}')
async def update_tags_route(text_id: str, tags: List[str]):
    return update_tags(text_id, tags)
