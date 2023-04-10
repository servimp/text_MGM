from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
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

client = MongoClient('mongodb://localhost:27017/')
db = client['text_management_app']
collection = db['texts']

class TextData(BaseModel):
    text: str

@app.post('/add_text/')
async def add_text(text_data: TextData):
    result = collection.insert_one(text_data.dict())
    return {"inserted_id": str(result.inserted_id)}

@app.get('/get_texts/')
async def get_texts():
    texts = []
    for text in collection.find():
        text['_id'] = str(text['_id'])
        texts.append(text)
    return texts
