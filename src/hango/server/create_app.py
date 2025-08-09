from hango.server import Server
from hango.core import ServiceContainer, PORT, HOST, REDIS_HOST, REDIS_PORT
from .connection_manager import ConnectionManager
from hango.routing import RouteToHandler
from hango.utils import ServeFile
from hango.middleware import MiddlewareChain
from hango.session import SessionStore
import redis

_server_instance = None

class CreateApp:
    def __init__(self, host=HOST, port=PORT, backlog=5, max_connections=100, concurrency_model='', cache=''):
        self.host = host
        self.port = port
        self.backlog = backlog
        self.connection_manager = ConnectionManager(max_connections)
        self._router = RouteToHandler()
        self._serve_file = ServeFile()
        self.concurrency_model = concurrency_model
        self.cache = cache
        session_store = SessionStore()
        self._middlewares = MiddlewareChain(session_store=session_store)
        # self._middlewares.add_default_middlewares()

    def create_container_and_server(self):
        container = ServiceContainer()
        container.register(ConnectionManager, self.connection_manager)
        container.register(RouteToHandler, self._router)
        container.register(ServeFile, self._serve_file)
        container.register(MiddlewareChain, self._middlewares)
        container.get(MiddlewareChain).add_default_middlewares()
        server = Server(host=self.host, port=self.port, container=container, backlog=self.backlog, concurrency_model=self.concurrency_model)
        if self.cache == 'redis':
            r = redis.asyncio.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)
            container.register('cache', r)
        return server



# def app(host=HOST, port=PORT, backlog=5, max_connections=100, concurrency_model='', cache=''):
#     app = CreateApp(host=host, port=port,backlog=backlog, max_connections=max_connections, concurrency_model=concurrency_model, cache=cache)
#     server = app.create_container_and_server()
#     print("SERVER INIT")
#     return server


def app(host=HOST, port=PORT, backlog=5, max_connections=100, concurrency_model='', cache=''):
    global _server_instance
    if _server_instance is None:
        creator = CreateApp(
            host=host,
            port=port,
            backlog=backlog,
            max_connections=max_connections,
            concurrency_model=concurrency_model,
            cache=cache
        )
        _server_instance = creator.create_container_and_server()
    return _server_instance