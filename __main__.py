import asyncio
from server import server

def main():
    asyncio.run(server.init_server())

if __name__ == "__main__":
    main()