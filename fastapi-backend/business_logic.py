from persistence import collection, ctx_collection, create_text, find_texts_by_tags, update_text_tags, add_tags_to_text, find_contexts_by_tags, update_context_tags, add_tags_to_context
from pydantic import BaseModel
from typing import List, Optional
# from openai_helper import process_nlp_query as process_query
from textblob import TextBlob
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from openai_helper import process_nlp_query as process_query

class TextData(BaseModel):
    text: str
    tags: List[str] = []

def search_contexts(query: str, contexts: List[dict]) -> List[dict]:
    # Handle cases where the list is empty
    if not contexts:
        return []

    # Combine all 'content' from each 'context' into a single string for each document
    combined_contents = [' '.join([content_dict['content'] for content_dict in context["context"]]) for context in contexts]

    query_blob = TextBlob(query)
    content_blobs = [TextBlob(content) for content in combined_contents]
    
    # Combine query and content blobs for vectorization
    combined_blobs = [query] + [content.raw for content in content_blobs]
    
    # Vectorize the texts using TfidfVectorizer
    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform(combined_blobs)
    
    # Calculate cosine similarity between query and contents
    cosine_similarities = cosine_similarity(vectors[0:1], vectors[1:]).flatten()
    
    # Create a list of tuples with the context dictionary and its similarity score
    scored_contexts = [(context, score) for context, score in zip(contexts, cosine_similarities)]
    
    # Sort contexts by similarity score in descending order
    scored_contexts.sort(key=lambda x: x[1], reverse=True)
    
    # Return the sorted list of contexts
    return [context for context, score in scored_contexts]


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

def get_contexts():
    contexts = []
    for context in ctx_collection.find():
        context['_id'] = str(context['_id'])
        contexts.append(context)
    return contexts

def add_text(text_data: TextData):
    return create_text(text_data)

def get_texts_by_tags(tags: Optional[str] = None, search: Optional[str] = None):
    if not tags and not search:
        return []

    tag_list = [tag.strip() for tag in tags.split(',')] if tags else []

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

# def update_context_tags(context_id: str, tags: List[str]):
  #  return update_context_tags(context_id, tags)

def add_context_tags(context_id: str, tags: List[str]):
    return add_tags_to_context(context_id, tags)

def get_contexts_by_tags(tags: Optional[str] = None, search: Optional[str] = None):
    if not tags and not search:
        return []

    tag_list = [tag.strip() for tag in tags.split(',')] if tags else []

    # Get contexts filtered by tags
    contexts = find_contexts_by_tags(tag_list, None)  # Pass None for the search parameter

    # If there is an NLP query, filter the contexts further
    if search:
        contexts = search_contexts(search, contexts)

    return contexts


