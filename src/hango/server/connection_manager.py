import asyncio

class ConnectionManager:
    def __init__(self, max_connections: int = 100):
        self.max_connections = max_connections
        self.active_connections: set = set()
        self._lock = asyncio.Lock()

    async def register(self, connection_id: str):
        await self._lock.acquire()
        try:
            if len(self.active_connections) < self.max_connections:
                self.active_connections.add(connection_id)
            else:
                raise ConnectionError("Maximum number of connections reached")
        finally:
            self._lock.release()
    
    async def deregister(self, connection_id: str):
        await self._lock.acquire()
        try:
            self.active_connections.discard(connection_id)
        finally:
            self._lock.release()
        
    def count(self) -> int:
        return len(self.active_connections)
    
    
