import asyncio
import signal

from hango import server
import hango.handler
async def main():
    server_obj = await server.init_server()
    print("Server is up and running.")
    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGINT, server_obj.close)
    await server_obj.wait_closed()
    print("The server has been closed.")
    

if __name__ == "__main__":
    asyncio.run(main())