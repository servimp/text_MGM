from fastapi import FastAPI, Body, HTTPException, WebSocket, WebSocketDisconnect, status, Query, Request
import json
from fastapi.middleware.cors import CORSMiddleware
from uuid import UUID as _uuid, uuid4

from typing import List, Optional
from business_logic import add_text, get_texts_by_tags, add_tags, update_tags, get_texts, process_nlp_query, get_contexts_by_tags, add_context_tags, get_contexts, CommandRunner
from persistence import drop_collection, get_all_texts, get_chat_context, create_chat_context, update_chat_context, update_context_tags, clone_and_update_context
from pydantic import BaseModel
from openai_helper import process_nlp_query
from fastapi.responses import StreamingResponse, HTMLResponse
from starlette.responses import Response
from datetime import datetime, timezone
import kube_config
import pod_templates
import deployments
from utils_environment import cleanup_all_environments, cleanup_user_environment

from ssh_service_pb2 import RunCommandRequest, RemoveConnectionRequest
from ssh_service_pb2_grpc import SshServiceStub
import grpc
import asyncio
from asyncio import gather
import os
import memcache
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from keys_store import memcache_client


import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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


def increment_open_environments_counter():
    open_environments_counter = memcache_client.get("open_environments_counter")
    memcache_client.set("open_environments_counter", open_environments_counter + 1)


def decrement_open_environments_counter():
    open_environments_counter = memcache_client.get("open_environments_counter")
    memcache_client.set("open_environments_counter", open_environments_counter - 1)

def increment_open_environments_per_user(user_id: str, environment_id: str):
    open_environments_per_user = json.loads(memcache_client.get("open_environments_per_user"))
    if user_id not in open_environments_per_user:
        open_environments_per_user[user_id] = {"count": 0, "environments": {}}
    
    open_environments_per_user[user_id]["count"] += 1
    open_environments_per_user[user_id]["environments"][environment_id] = {"connection_defined": False}
    memcache_client.set("open_environments_per_user", json.dumps(open_environments_per_user))

def decrement_open_environments_per_user(user_id: str, environment_id: str):
    open_environments_per_user = json.loads(memcache_client.get("open_environments_per_user"))
    if user_id in open_environments_per_user:
        open_environments_per_user[user_id]["count"] -= 1
        del open_environments_per_user[user_id]["environments"][environment_id]
        memcache_client.set("open_environments_per_user", json.dumps(open_environments_per_user))    


@app.post("/start_environment")
async def start_environment(user_id: str, environment_name: str):
    # Load Kubernetes config
    kube_config.load_kube_config()

    # Generate and store SSH key pair for the user
    environment_id = str(uuid4())
    generate_and_store_ssh_key(user_id, environment_id)  # Call this before creating the pod template

    # Create a vcluster for the user
    # vcluster_name = f"vcluster-{user_id}"
    vcluster_name = f"vcluster-{user_id}-{environment_id}"
    kube_config.create_namespace('vcluster')
    kube_config.create_vcluster(vcluster_name, 'vcluster')

    # Create a Deployment in the vcluster
    template = pod_templates.ubuntu_pod_template(user_id, environment_name, environment_id, memcache_client)  # Pass environment_name
    deployment = deployments.create_deployment('vcluster', user_id, template, environment_id) 
    
    # Create a Service in the vcluster
    kube_config.create_service(user_id, 'vcluster', environment_id)  # Pass environment_id

    # Increment the open environments counter
    increment_open_environments_counter()
    # Increment the open environments per user structure
    increment_open_environments_per_user(user_id, environment_id)

    logger.info(f'Open environments counter: {memcache_client.get("open_environments_counter")}')
    open_environments_per_user_json = memcache_client.get("open_environments_per_user")
    logger.info(f"Open environments per user: {open_environments_per_user_json}")
    # Return the necessary details for the frontend to connect to the deployment
    return {
        "namespace": deployment.metadata.namespace,
        "pod_name": f"vcluster-{deployment.metadata.name}",
        "cluster_name": user_id,
        "environment_id": environment_id,
        # Add more data if needed
    }
    


def generate_and_store_ssh_key(user_id: str, environment_id: str):
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )

    public_key = private_key.public_key()

    public_key_string = public_key.public_bytes(
        encoding=serialization.Encoding.OpenSSH,
        format=serialization.PublicFormat.OpenSSH
        ).decode('utf-8')

    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    )

    print(f"Generated private key for user {user_id}, environment {environment_id}:\n{private_pem.decode('utf-8')}")

    key = f"connection:{user_id}:{environment_id}"
    value = {
        "private_key": private_pem.decode('utf-8'),
        "public_key": public_key_string
    }
    memcache_client.set(key, json.dumps(value))

    logger.info(f"Stored SSH keys for user {user_id}, environment {environment_id}: {value}")
    # log_memcache_contents(memcache_client)    


@app.get("/test_ssh/{user_id}/{environment_id}")
async def test_ssh(user_id: str, environment_id: str, commands: List[str] = Query([])):
    logger.info(f"Entered test_ssh: '{commands}', type: {type(commands)}")
    command_outputs = {}

    # Connect to the FastAPI SSH service using gRPC
    channel = grpc.aio.insecure_channel('ssh-service:50051')
    ssh_service = SshServiceStub(channel)

    # Define an asynchronous generator for sending commands
    async def send_commands():
        for command in commands:
            logger.info(f"Command at test_ssh: '{command}', type: {type(command)}")
            yield RunCommandRequest(user_id=user_id, environment_id=environment_id, command=command)

    # Define an asynchronous callback function for receiving command outputs
    async def on_command_output(command: str, line: str):
        command_outputs[command] = command_outputs.get(command, "") + line

    # Run each command using the gRPC client
    logger.info("Starting gRPC call")  # Add this logging statement
    call = ssh_service.RunCommand(send_commands())  # Pass the generator function to RunCommand
    async for response in call:
        logger.info(f"Received response from gRPC call: {response}")  # Add this logging statement
        await on_command_output(response.command, response.line)
    return {
        "command_outputs": command_outputs
    }


@app.post("/close_ssh_connection/{user_id}/{environment_id}")
async def close_ssh_connection(user_id: str, environment_id: str):
    channel = grpc.aio.insecure_channel('ssh-service:50051')
    stub = SshServiceStub(channel)
    request = RemoveConnectionRequest(user_id=user_id, environment_id=environment_id)
    response = await stub.RemoveConnection(request)
    await channel.close()

    if response.status == "success":
        # Remove the structure from the open environments structure and adjust the counter
        decrement_open_environments_per_user(user_id, environment_id)
        decrement_open_environments_counter()
        logger.info(f"SSH connection removed for user {user_id}, environment {environment_id}")
        # In case we want to delete all Docker and kubernetes resources of the environment
        # await cleanup_user_environment(user_id, environment_id)
        return {"status": "success"}
    else:
        logger.warning(f"Failed to remove SSH connection for user {user_id}, environment {environment_id}")
        raise HTTPException(status_code=500, detail="Failed to remove SSH connection")


@app.delete("/delete_environment/{user_id}/{environment_id}")
async def delete_environment_endpoint(user_id: str, environment_id: str):
    # Call your function
    await cleanup_user_environment(user_id, environment_id)
    return {"message": f"Environment {environment_id} for user {user_id} deleted"}


@app.post("/delete_all_environments")
async def delete_all_environments_endpoint():
    # Call your function
    cleanup_all_environments()
    return {"message": "All environments deleted"} 


@app.websocket("/ws/{user_id}/{environment_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str, environment_id: str):
    await websocket.accept()
    try:
        while True:
            command = await websocket.receive_text()
            # Send the command using the existing gRPC mechanism
            logger.info(f"Received command: '{command}', type: {type(command)}")
            command_outputs = await test_ssh(user_id, environment_id, commands=[command.strip()])
            # Send the output back to the frontend using WebSocket
            for output in command_outputs["command_outputs"].values():
                await websocket.send_text(output)

    except WebSocketDisconnect:
        pass