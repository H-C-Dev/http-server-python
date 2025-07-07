import asyncio
from server import server
import handler
def main():
    asyncio.run(server.init_server())

if __name__ == "__main__":
    main()