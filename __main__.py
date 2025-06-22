import asyncio
from server import server
from response import CustomResponse
import handler

def main():
    asyncio.run(server.start_server())
	print(" Testing: pushing commit from iPad")

main()