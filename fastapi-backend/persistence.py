from pymongo import MongoClient
from bson.objectid import ObjectId

client = MongoClient('mongodb://localhost:27017/')
db = client['text_management_app']
collection = db['texts']

def create_text(text_data):
    result = collection.insert_one(text_data.dict())
    return {"inserted_id": str(result.inserted_id)}

def find_texts_by_tags(tag_list):
    texts = []
    for text in collection.find({"tags": {"$in": tag_list}}):
        text['_id'] = str(text['_id'])
        texts.append(text)
    return texts

def update_text_tags(text_id, tags):
    result = collection.update_one({"_id": ObjectId(text_id)}, {"$set": {"tags": tags}})
    return {"modified_count": result.modified_count}

def add_tags_to_text(text_id, tags):
    result = collection.update_one({"_id": ObjectId(text_id)}, {"$addToSet": {"tags": {"$each": tags}}})
    return {"modified_count": result.modified_count}
