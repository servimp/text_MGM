from persistence import collection, create_text, find_texts_by_tags, update_text_tags, add_tags_to_text
from pydantic import BaseModel
from typing import List, Optional
from openai_helper import process_nlp_query as process_query


class TextData(BaseModel):
    text: str
    tags: List[str] = []

def get_texts():
    texts = []
    for text in collection.find():
        text['_id'] = str(text['_id'])
        texts.append(text)
    return texts

def add_text(text_data: TextData):
    return create_text(text_data)

def get_texts_by_tags(tags: Optional[str] = None, search: Optional[str] = None):
    if not tags and not search:
        return []
    tag_list = tags.split(',') if tags else []
    return find_texts_by_tags(tag_list, search)

def add_tags(text_id: str, tags: List[str]):
    return add_tags_to_text(text_id, tags)

def update_tags(text_id: str, tags: List[str]):
    return update_text_tags(text_id, tags)

def process_nlp_query(query: str):
    return process_query(query)