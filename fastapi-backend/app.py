from fastapi import FastAPI, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from business_logic import add_text, get_texts_by_tags, add_tags, update_tags, get_texts
from pydantic import BaseModel
from openai_helper import process_nlp_query

app = FastAPI()

class NLPGPT4Response(BaseModel):
    response: str

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

async def get_gpt4_response(query: str) -> NLPGPT4Response:
    try:
        assistant_response = await process_nlp_query(query)
        return NLPGPT4Response(response=assistant_response)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/get_texts/')
async def get_texts_route():
    return get_texts()

@app.post('/add_text/')
async def add_text_route(text_data: TextData):
    return add_text(text_data)

@app.get('/get_texts_by_tags_and_text/')
async def get_texts_by_tags_route(tags: Optional[str] = None, search: Optional[str] = None):
    return get_texts_by_tags(tags, search)

@app.patch('/add_tags/{text_id}')
async def add_tags_route(text_id: str, tags: List[str]):
    return add_tags(text_id, tags)

@app.patch('/update_tags/{text_id}')
async def update_tags_route(text_id: str, tags: List[str]):
    return update_tags(text_id, tags)

class NLPQuery(BaseModel):
    query: str

@app.post("/process_nlp_query/", response_model=NLPGPT4Response)
async def process_nlp_query_route(nlp_query: NLPQuery):
    return await get_gpt4_response(nlp_query.query)

