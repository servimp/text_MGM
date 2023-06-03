from pymongo import MongoClient
from bson.objectid import ObjectId
from dotenv import load_dotenv
import os

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# Create a new collection for storing the chat context
ctx_collection = db["ctx_data"]

def clone_and_update_context(chat_id, new_id, additional_tags):
    print(f"Received request to clone chat_id: {chat_id} to new_id: {new_id}")

    # Fetch the original document
    original = ctx_collection.find_one({"_id": chat_id})

    if original is not None:
        print(f"Original document with chat_id: {chat_id} found. Proceeding with clone.")

        # Create a new document based on the original document
        new_doc = original.copy()

        # Update the ID and add new tags
        new_doc["_id"] = new_id
        print(f"Updating _id to: {new_id}")

        if 'tags' in new_doc:
            new_doc["tags"].extend(additional_tags)
            print(f"Adding additional tags: {additional_tags} to existing tags: {new_doc['tags']}")
        else:
            new_doc["tags"] = additional_tags
            print(f"No existing tags found. Adding new tags: {additional_tags}")

        # Insert the new document into the collection
        result = ctx_collection.insert_one(new_doc)

        # Validate the insertion
        if result.inserted_id != new_id:
            print(f"Failed to insert document with id {new_id}")
            return None

        print(f"New document with _id: {new_id} successfully inserted.")
        
        # Retrieve and return the new document
        new_doc = ctx_collection.find_one({"_id": new_id})
        print(f"Returning new document: {new_doc}")
        return new_doc

    else:
        print(f"No document found with chat_id: {chat_id}")
        return None


def get_chat_context(chat_id):
    ctx = ctx_collection.find_one({"_id": chat_id})
    return ctx

def create_chat_context(chat_id):
    ctx_data = [{"role": "system", "content": "You are a helpful assistant."}]
    result = ctx_collection.insert_one({"_id": chat_id, "context": ctx_data})
    return {"_id": chat_id, "context": ctx_data}  # return a dictionary with the same structure as the inserted document

def update_chat_context(chat_id, new_data):
    ctx_collection.update_one({"_id": chat_id}, {"$push": {"context": {"$each": new_data}}})

def find_contexts_by_tags(tag_list, search):
    query = {}
    if tag_list:
        query["$or"] = [{"tags": tag} for tag in tag_list]

    if search:
        query["context.content"] = {"$regex": search, "$options": "i"}

    contexts = []
    for context in ctx_collection.find(query):
        context['_id'] = str(context['_id'])
        contexts.append(context)
    return contexts

def update_context_tags(context_id, tags):
    result = ctx_collection.update_one({"_id": context_id}, {"$set": {"tags": tags}})
    return {"modified_count": result.modified_count}

def create_text(text_data):
    result = collection.insert_one(text_data.dict())
    return {"inserted_id": str(result.inserted_id)}

def find_texts_by_tags(tag_list, search):

    print(f"TAGS QUE ESTAN LLEGANDO: {tag_list}")
    query = {}
    if tag_list:
        query["$or"] = [{"tags": tag} for tag in tag_list]
        print(f"Tags query: {query}")

    if search:
        query["text"] = {"$regex": search, "$options": "i"}
        print(f"Search query: {query}")

    texts = []
    for text in collection.find(query):
        text['_id'] = str(text['_id'])
        texts.append(text)
        
    print(f"Found texts in find_texts_by_tags: {texts}")

    return texts


def update_text_tags(text_id, tags):
    result = collection.update_one({"_id": ObjectId(text_id)}, {"$set": {"tags": tags}})
    return {"modified_count": result.modified_count}

def add_tags_to_text(text_id, tags):
    result = collection.update_one({"_id": ObjectId(text_id)}, {"$addToSet": {"tags": {"$each": tags}}})
    return {"modified_count": result.modified_count}

def add_tags_to_context(context_id, tags):
    result = ctx_collection.update_one({"_id": context_id}, {"$addToSet": {"tags": {"$each": tags}}})
    return {"modified_count": result.modified_count}

def drop_collection():
    collection.drop()

def get_all_texts():
    texts = []
    for text in collection.find():
        text['_id'] = str(text['_id'])
        texts.append(text)
    return texts