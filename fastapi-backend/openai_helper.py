import openai
import asyncio
from dotenv import load_dotenv
import os
import json
load_dotenv()
from fastapi.responses import JSONResponse

API_KEY = os.getenv("OPENAI_API_KEY")

openai.api_key = API_KEY

async def process_nlp_query(query: str, chat_context: list, model: str = "gpt-4"):
    loop = asyncio.get_event_loop()

    # Remove timestamp and model from the context for the API request
    api_chat_context = []
    for message in chat_context:
        api_message = {"role": message["role"], "content": message["content"]}
        api_chat_context.append(api_message)

    msg_ctx = api_chat_context
    print(f"Query sent: {msg_ctx}")

    def _fetch_response():
        response = openai.ChatCompletion.create(
            model=model,  # use provided model here
            messages=api_chat_context,
            max_tokens=800,
            n=1,
            stop=None,
            temperature=0.5,
            stream=True,
        )
        return response

    try:
        response = await loop.run_in_executor(None, _fetch_response)
        for chunk in response:
            chunk_data = json.dumps(chunk) + "\n"
            print(f"Received chunk from OpenAI API: {chunk_data}")
            yield chunk_data
    except Exception as e:
        print(f"Error processing NLP query: {e}")
        raise e
