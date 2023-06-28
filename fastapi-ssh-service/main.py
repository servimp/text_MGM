import grpc
from ssh_service_pb2_grpc import add_SshServiceServicer_to_server, SshServiceServicer
from ssh_service_pb2 import RunCommandResponse, RemoveConnectionResponse
from business_logic import CommandRunner
import asyncio
import logging
import memcache

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
logger = logging.getLogger(__name__)

memcache_client = memcache.Client(['memcached:11211'], debug=0)

memcache_client.set("open_connections_counter", 0)

command_runner = CommandRunner(memcache_client)

class SshService(SshServiceServicer):
    async def RunCommand(self, request_iterator, context):
        async for request in request_iterator:
            user_id = request.user_id
            environment_id = request.environment_id
            command = request.command

            async def callback(command, line):
                await context.write(RunCommandResponse(command=command, line=line))

            # Use async for loop to iterate through the async generator
            async for _ in command_runner.run_command(user_id, environment_id, command, callback):
                pass  # You don't need to do anything here, as the callback is already called inside run_command

    async def RemoveConnection(self, request, context):
        user_id = request.user_id
        environment_id = request.environment_id

        await command_runner.remove_connection(user_id, environment_id)

        return RemoveConnectionResponse(status="success")            


async def serve():
    server = grpc.aio.server()
    add_SshServiceServicer_to_server(SshService(), server)
    server.add_insecure_port('[::]:50051')
    await server.start()
    await server.wait_for_termination()

if __name__ == '__main__':
    asyncio.run(serve())