import asyncssh
import json
import logging
from uuid import uuid4
from kube_config import load_kube_config
from kubernetes import client
from typing import Callable, Awaitable

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
logger = logging.getLogger(__name__)

class CommandRunner:
    def __init__(self, memcache_client):
        self.memcache_client = memcache_client
        self.connections = {}  # Store SSH connections
        load_kube_config()

    def increment_open_connections_counter(self):
        open_connections_counter = self.memcache_client.get("open_connections_counter")
        self.memcache_client.set("open_connections_counter", open_connections_counter + 1)

    def decrement_open_connections_counter(self):
        open_connections_counter = self.memcache_client.get("open_connections_counter")
        self.memcache_client.set("open_connections_counter", open_connections_counter - 1)    

    def set_connection_defined(self, user_id: str, environment_id: str, connection_defined: bool):
            open_environments_per_user = json.loads(self.memcache_client.get("open_environments_per_user"))
            if user_id in open_environments_per_user:
                open_environments_per_user[user_id]["environments"][environment_id]["connection_defined"] = connection_defined
                self.memcache_client.set("open_environments_per_user", json.dumps(open_environments_per_user))

    def delete_connection(self, user_id, environment_id):
        key = f"connection:{user_id}:{environment_id}"
        self.memcache_client.delete(key)

    async def connect_to_ssh(self, user_id, environment_id, service_ip, service_port):
        connection_key = f"client:{user_id}:{environment_id}"
        logger.info(f"Connection key set at connect_to_ssh {user_id}, environment: {environment_id}")
        logger.info(f"Check self connections 0: {self.connections}")
        if connection_key in self.connections:
            logger.info(f"Process RETRIEVED at run command")
            return self.connections[connection_key]["process"]

        key = f"connection:{user_id}:{environment_id}"
        ssh_key_data = json.loads(self.memcache_client.get(key))
        private_key_str = ssh_key_data["private_key"]
        key = asyncssh.import_private_key(private_key_str)

        try:
            logger.info(f"Check self connections 1: {self.connections}")
            conn = await asyncssh.connect(service_ip, port=service_port, username="root", client_keys=[key], known_hosts=None)
            logger.info(f"Connected to SSH server at {service_ip}")

            # Create a process and store it in the connections dictionary
            process = await conn.create_process('bash')
            self.connections[connection_key] = {"conn": conn, "process": process}
            logger.info(f"Saved connection key: {connection_key}")
            # Add the process to the open connections counter
            self.increment_open_connections_counter()
            # Set the connection_defined flag for the environment
            self.set_connection_defined(user_id, environment_id, True)
            logger.info(f'Open connections counter: {self.memcache_client.get("open_connections_counter")}')
            open_environments_per_user_json = self.memcache_client.get("open_environments_per_user")
            logger.info(f"Open environments per user: {open_environments_per_user_json}")
            logger.info(f"Process CREATED at run command")


            return process

        except Exception as e:
            print(f"Failed to connect to SSH server: {e}")
            raise e
    

    async def run_command(self, user_id: str, environment_id: str, command: str, callback: Callable[[str, str], Awaitable[None]]):
        try:
            # Connect to the environment using SSH
            service_ip, service_port = self.get_service_ip(user_id, environment_id)
            process = await self.connect_to_ssh(user_id, environment_id, service_ip, service_port)

            # Send command
            end_of_command_marker = f"END_OF_COMMAND_{uuid4().hex}"
            process.stdin.write(f"{command}; echo {end_of_command_marker}\n")
            await process.stdin.drain()

            # Get output in real-time
            async for line in process.stdout:
                # logger.info(f"Lines generated at print loop")
                if end_of_command_marker in line:
                    break
                print(line.strip())  # Process the output in real-time
                await callback(command, line)  # Call the callback function with the command and output line

        except Exception as e:
            logger.info(f"Error in run_command: {e}")  # Add this print statement
            logger.info(f"user_id: {user_id}, environment_id: {environment_id}")  # Add this print statement
            key = f"connection:{user_id}:{environment_id}"
            ssh_key_data = json.loads(self.memcache_client.get(key))
            logger.info(f"ssh_key_data: {ssh_key_data}")  # Add this print statement
            logger.error(f"Failed to run command: {e}")
            yield str(e)

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
        
    async def remove_connection(self, user_id: str, environment_id: str):
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
            self.decrement_open_connections_counter()

            # Delete connection data
            self.delete_connection(user_id, environment_id)

            logger.info(f"Connection deleted for user: {user_id}, environment: {environment_id}")
        else:
            logger.error(f"No connection data found for user: {user_id}, environment: {environment_id}")    