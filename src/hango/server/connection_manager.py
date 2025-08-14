import asyncio

class ConnectionManager:
    def __init__(self, max_connections: int = 100):
        self.max_connections = max_connections
        self.active_connections: set[int] = set()
        self._writers: dict[int, asyncio.StreamWriter] = {}  
        self._lock = asyncio.Lock()

    async def register(self, connection_id: int):
        async with self._lock:
            if len(self.active_connections) < self.max_connections:
                self.active_connections.add(connection_id)
            else:
                raise ConnectionError("Maximum number of connections reached")

    async def register_writer(self, connection_id: int, writer: asyncio.StreamWriter):
        async with self._lock:
            self._writers[connection_id] = writer

    async def deregister(self, connection_id: int):
        async with self._lock:
            self.active_connections.discard(connection_id)
            self._writers.pop(connection_id, None)

    def count(self) -> int:
        return len(self.active_connections)

    async def close_all(self):
        async with self._lock:
            writers = list(self._writers.values())
            self._writers.clear()
            self.active_connections.clear()

        for w in writers:
            try:
                transport = getattr(w, "transport", None)
                if transport and hasattr(transport, "abort"):
                    transport.abort()
                else:
                    w.close()
            except Exception:
                pass