from persistence import collection, ctx_collection, create_text, find_texts_by_tags, update_text_tags, add_tags_to_text, find_contexts_by_tags, update_context_tags, add_tags_to_context
from pydantic import BaseModel
from typing import List, Optional
from kubernetes import client
from kubernetes import config as kube_config
from kubernetes.stream import stream
from textblob import TextBlob
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from openai_helper import process_nlp_query as process_query
from uuid import UUID as _uuid, uuid4

import paramiko
import asyncssh, asyncio
import json
import time
import io
from io import StringIO

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

class CommandRunner:
    def __init__(self, memcache_client):
        self.memcache_client = memcache_client
        self.connections = {}  # Store SSH connections
        kube_config.load_kube_config()

    def store_connection(self, user_id, environment_id, connection_data):
        key = f"connection:{user_id}:{environment_id}"
        self.memcache_client.set(key, json.dumps(connection_data))
        # logger.info(f"Stored connection data for user {user_id}, environment {environment_id}: {connection_data}")

    def get_connection(self, user_id, environment_id):
        key = f"connection:{user_id}:{environment_id}"
        # log_memcache_contents(self.memcache_client)   
        connection_data = self.memcache_client.get(key)
        if connection_data is not None:
            connection_data = json.loads(connection_data)

            # Get the latest IP and port
            service_ip, service_port = self.get_service_ip(user_id, environment_id)

            # Update the connection data with the latest IP and port
            connection_data["ip"] = service_ip
            connection_data["port"] = service_port

            return connection_data
        return None

    def delete_connection(self, user_id, environment_id):
        key = f"connection:{user_id}:{environment_id}"
        self.memcache_client.delete(key)

    def increment_open_connections(self, user_id):
        key = f"open_connections:{user_id}"
        self.memcache_client.incr(key, 1)

    def decrement_open_connections(self, user_id):
        key = f"open_connections:{user_id}"
        self.memcache_client.decr(key, 1)

    def get_open_connections(self, user_id):
        key = f"open_connections:{user_id}"
        open_connections = self.memcache_client.get(key)
        if open_connections is not None:
            return int(open_connections)
        return 0

    def get_service_ip(self, user_id: str, environment_id: str):
        kube_client = client.CoreV1Api()
        service_name = f"user-vcluster-{str(user_id)}-{environment_id}"
        host_cluster_namespace = 'vcluster'
        service = kube_client.read_namespaced_service(name=service_name, namespace=host_cluster_namespace)
        if service:
            node_port = service.spec.ports[0].node_port
            nodes = kube_client.list_node()
            node_ip = nodes.items[0].status.addresses[0].address
            return node_ip, node_port
        else:
            raise Exception(f"No service found for user {user_id}")

    async def connect_to_ssh(self, user_id, environment_id, service_ip, service_port):
        connection_key = f"client:{user_id}:{environment_id}"
        logger.info(f"Connection key set at connect_to_ssh {user_id}, environment: {environment_id}")
        logger.info(f"Check self connections 0: {self.connections}")
        if connection_key in self.connections:
            logger.info(f"Existing connection for user: {user_id}, environment: {environment_id}")
            return self.connections[connection_key]["process"]

        key = f"connection:{user_id}:{environment_id}"
        ssh_key_data = json.loads(self.memcache_client.get(key))
        private_key_str = ssh_key_data["private_key"]
        key = asyncssh.import_private_key(private_key_str)

        try:
            logger.info(f"Check self connections 1: {self.connections}")
            conn = await asyncssh.connect(service_ip, port=service_port, username="root", client_keys=[key], known_hosts=None)
            logger.info(f"Connected to SSH server at {service_ip}")

            # Increment open connections for the user
            self.increment_open_connections(user_id)

            # Update the existing connection data with the new information
            connection_data = {
                "private_key": ssh_key_data["private_key"],
                "public_key": ssh_key_data["public_key"],
                "ip": service_ip,
                "port": service_port,
            }
            self.store_connection(user_id, environment_id, connection_data)

            # Create a process and store it in the connections dictionary
            process = await conn.create_process('bash')
            self.connections[connection_key] = {"conn": conn, "process": process}
            logger.info(f"Saved connection key: {connection_key}")
            return process

        except Exception as e:
            print(f"Failed to connect to SSH server: {e}")
            raise e

    async def run_command(self, user_id: str, environment_id: str, command: str, ssh_user: str = None, ssh_key: str = None):
        try:
            # Connect to the environment using SSH
            service_ip, service_port = self.get_service_ip(user_id, environment_id)
            process = await self.connect_to_ssh(user_id, environment_id, service_ip, service_port)

            # Send command
            end_of_command_marker = f"END_OF_COMMAND_{uuid4().hex}"
            process.stdin.write(f"{command}; echo {end_of_command_marker}\n")
            await process.stdin.drain()

            # Get output in real-time
            output = ""
            async for line in process.stdout:
                if end_of_command_marker in line:
                    break
                print(line.strip())  # Process the output in real-time
                output += line
                yield line

        except Exception as e:
            logger.error(f"Failed to run command: {e}")
            yield str(e)

    async def close_connection(self, user_id: str, environment_id: str):
        connection_key = f"client:{user_id}:{environment_id}"
        logger.info(f"Connection to delete: {connection_key} in {self.connections}")
        if connection_key in self.connections:
            conn = self.connections[connection_key]["conn"]
            process = self.connections[connection_key]["process"]

            # Send an exit command to the process
            process.stdin.write("exit\n")
            await process.stdin.drain()

            # Close the process stdin
            process.stdin.close()

            # Close the SSH connection
            conn.close()
            await conn.wait_closed()

            # Remove the connection from the dictionary
            del self.connections[connection_key]

            # Decrement open connections for the user
            self.decrement_open_connections(user_id)

            # Delete connection data
            self.delete_connection(user_id, environment_id)

            logger.info(f"Connection deleted for user: {user_id}, environment: {environment_id}")
        else:
            logger.error(f"No connection data found for user: {user_id}, environment: {environment_id}")

