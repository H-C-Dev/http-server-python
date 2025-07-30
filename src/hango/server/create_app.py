from hango.server import Server
from hango.core import ServiceContainer
from .connection_manager import ConnectionManager
from hango.routing import RouteToHandler
from hango.utils import ServeFile
from hango.middleware import MiddlewareChain

PORT=8080

class CreateApp:
    def __init__(self, host="0.0.0.0", port=PORT, backlog=5, max_connections=100, concurrency_model=''):
        self.host = host
        self.port = port
        self.backlog = backlog
        self.connection_manager = ConnectionManager(max_connections)
        self._router = RouteToHandler()
        self._serve_file = ServeFile()
        self._middlewares = MiddlewareChain()
        self.concurrency_model = concurrency_model

    def create_container_and_server(self):
        container = ServiceContainer()
        container.register(ConnectionManager, self.connection_manager)
        container.register(RouteToHandler, self._router)
        container.register(ServeFile, self._serve_file)
        container.register(MiddlewareChain, self._middlewares)
        server = Server(host=self.host, port=self.port, container=container, backlog=self.backlog, concurrency_model=self.concurrency_model)
        return server



def app(host="0.0.0.0", port=PORT, backlog=5, max_connections=100, concurrency_model=''):
    app = CreateApp(host=host, port=port,backlog=backlog, max_connections=max_connections, concurrency_model=concurrency_model)
    server = app.create_container_and_server()
    return server