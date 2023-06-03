from fastapi import FastAPI, Body, HTTPException, BackgroundTasks
import json
from fastapi.middleware.cors import CORSMiddleware
from uuid import UUID as _uuid, uuid4

from typing import List, Optional
from business_logic import add_text, get_texts_by_tags, add_tags, update_tags, get_texts, process_nlp_query, get_contexts_by_tags, add_context_tags, get_contexts
from persistence import drop_collection, get_all_texts, get_chat_context, create_chat_context, update_chat_context, update_context_tags, clone_and_update_context
from pydantic import BaseModel
from openai_helper import process_nlp_query
from fastapi.responses import StreamingResponse
from starlette.responses import Response
from datetime import datetime, timezone


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:8080','http://localhost:5173'],
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

@app.get('/get_contexts/')
async def get_contexts_route():
    return get_contexts()

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

@app.get('/get_contexts_by_tags_and_text/')
async def get_contexts_by_tags_route(tags: Optional[str] = None, search: Optional[str] = None):
    return get_contexts_by_tags(tags, search)

@app.patch('/add_context_tags/{context_id}')
async def add_context_tags_route(context_id: str, tags: List[str]):
    return add_context_tags(context_id, tags)

@app.patch('/update_context_tags/{context_id}')
async def update_context_tags_route(context_id: str, tags: List[str]):
    return update_context_tags(context_id, tags)


class NLPGPT4Response(BaseModel):
    response: str

async def get_gpt4_response(query: str) -> NLPGPT4Response:
    try:
        assistant_response = await process_nlp_query(query)
        return NLPGPT4Response(response=assistant_response)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class NLPQuery(BaseModel):
    query: str

@app.get("/process_nlp_query_stream/")
async def process_nlp_query_route(query: str, idChat: _uuid, model: str = "gpt-4"):
    # Convert idChat to string
    idChat = str(idChat)

    # Check if chat ID exists in the ctx_data collection
    chat_context = get_chat_context(idChat)
    if not chat_context:
        chat_context = create_chat_context(idChat)

    # Prepare user message for context
    user_message = {"role": "user", "content": query, "timestamp": datetime.now(timezone.utc).isoformat(), "model": model}
    
    # Add user message to context
    update_chat_context(idChat, [user_message])

    # Fetch the updated chat context
    chat_context = get_chat_context(idChat)

    # Create a generator for processing the response
    async def response_generator():
        # Initialize a variable to hold the assistant's response
        assistant_response = ""
        # Inside your response_generator function...
        async for response in process_nlp_query(query, chat_context["context"], model):  # Pass model to process_nlp_query
            print(f"Yielding response chunk to client: {response}")
            # Parse the response JSON
            response_json = json.loads(response)

            # Check if 'content' field is in the response - ss
            if 'content' in response_json.get('choices', [{}])[0].get('delta', {}):
                # Accumulate the assistant's response
                assistant_response += response_json['choices'][0]['delta']['content']

            # Yield the response chunk to the client
            yield response

        # After processing the whole stream, update the chat context in the database
        new_data = [{"role": "assistant", "content": assistant_response.strip(), "timestamp": datetime.now(timezone.utc).isoformat(), "model": model}]
        update_chat_context(idChat, new_data)

    # Prepare the streaming response
    response_stream = response_generator()
    response = StreamingResponse(response_stream, media_type="text/event-stream")
    response.headers['Connection'] = 'keep-alive'
    response.headers['Cache-Control'] = 'no-cache'

    return response


@app.patch('/clone_context/{chat_id}')
async def clone_context_route(chat_id: str):
    print(f"Received request to clone chat_id: {chat_id}")

    new_id = str(uuid4())  # use uuid4() to generate a new UUID
    print(f"Generated new_id for clone: {new_id}")

    additional_tags = ["bifurcation", chat_id]
    print(f"Additional tags for new document: {additional_tags}")

    new_doc = clone_and_update_context(chat_id, new_id, additional_tags)
    
    if new_doc is not None:
        print(f"Successfully cloned chat_id: {chat_id} to new_id: {new_id}")
        return new_doc
    else:
        print(f"Failed to clone chat_id: {chat_id}")
        raise HTTPException(status_code=404, detail="chat_id not found")



# Debugging end points
@app.post("/drop_collection/")
async def drop_collection_route():
    drop_collection()
    return {"status": "Collection dropped"}


@app.get("/get_all_texts/")
async def get_all_texts_route():
    return get_all_texts()

