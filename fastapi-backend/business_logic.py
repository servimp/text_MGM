from persistence import collection, create_text, find_texts_by_tags, update_text_tags, add_tags_to_text
from pydantic import BaseModel
from typing import List, Optional
# from openai_helper import process_nlp_query as process_query
from textblob import TextBlob
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer



class TextData(BaseModel):
    text: str
    tags: List[str] = []

def search_texts(query: str, texts: List[dict]) -> List[dict]:
    print(f"Received query: {query}")  # Add this line
    print(f"Received texts: {texts}")  # Add this line

    # Handle cases where the list is empty
    if not texts:
        return []

    query_blob = TextBlob(query)
    text_blobs = [TextBlob(text["text"]) for text in texts]
    
    # Combine query and text blobs for vectorization
    combined_blobs = [query] + [text.raw for text in text_blobs]
    
    # Vectorize the texts using TfidfVectorizer
    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform(combined_blobs)
    
    # Calculate cosine similarity between query and texts
    cosine_similarities = cosine_similarity(vectors[0:1], vectors[1:]).flatten()
    print(f"Cosine Similarities: {cosine_similarities}")  # Add this line
    
    # Create a list of tuples with the text dictionary and its similarity score
    scored_texts = [(text, score) for text, score in zip(texts, cosine_similarities)]
    
    # Sort texts by similarity score in descending order
    scored_texts.sort(key=lambda x: x[1], reverse=True)

    print(f"Texts with scores: {scored_texts}")
    
    # Return the sorted list of texts
    return [text for text, score in scored_texts]  

def get_texts():
    texts = []
    for text in collection.find():
        text['_id'] = str(text['_id'])
        texts.append(text)
    return texts

def add_text(text_data: TextData):
    return create_text(text_data)
'''
def get_texts_by_tags(tags: Optional[str] = None, search: Optional[str] = None):
    if not tags and not search:
        return []
    tag_list = tags.split(',') if tags else []
    return find_texts_by_tags(tag_list, search)
'''
'''
def get_texts_by_tags(tags: Optional[str] = None, search: Optional[str] = None):
    if not tags and not search:
        return []

    tag_list = tags.split(',') if tags else []
    texts = find_texts_by_tags(tag_list, search)

    print(f"Found texts before filtering: {texts}")  # Add this line

    if search:
        texts = search_texts(search, texts)

    print(f"Found texts after filtering: {texts}")  # Add this line

    return texts
    '''

def get_texts_by_tags(tags: Optional[str] = None, search: Optional[str] = None):
    if not tags and not search:
        return []

    tag_list = tags.split(',') if tags else []

    # Get texts filtered by tags
    texts = find_texts_by_tags(tag_list, None)  # Pass None for the search parameter

    print(f"Found texts before NLP filtering: {texts}")

    # If there is an NLP query, filter the texts further
    if search:
        texts = search_texts(search, texts)

    print(f"Found texts after NLP filtering: {texts}")

    return texts


    

def add_tags(text_id: str, tags: List[str]):
    return add_tags_to_text(text_id, tags)

def update_tags(text_id: str, tags: List[str]):
    return update_text_tags(text_id, tags)

def process_nlp_query(query: str):
    return process_query(query)