import openai
import asyncio

openai.api_key = "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"

import openai
import asyncio

openai.api_key = "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"

async def process_nlp_query(query: str):
    loop = asyncio.get_event_loop()

    def _fetch_response():
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": query}],
            max_tokens=100,
            n=1,
            stop=None,
            temperature=0.5,
        )
        return response

    try:
        response = await loop.run_in_executor(None, _fetch_response)
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"Error processing NLP query: {e}")
        raise e
