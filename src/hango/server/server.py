import asyncio
from hango.custom_http import HTTPError, MethodNotAllowed, InternalServerError, BadRequest, HTTPRequestParser, Response, EarlyHintsResponse, Request
from hango.core import ContentType, MethodType, HOST
from hango.routing import RouteToHandler
from hango.utils import ServeFile
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from typing import Tuple, Any
from hango.middleware import MiddlewareChain
from .connection_manager import ConnectionManager
import signal
import ssl

ENABLE_HTTPS = False
PORT=8080
HTTPS_PORT = 8443
CERT_FILE = "server.crt"
KEY_FILE = "server.key"
DEV = True



class HTTPServer:
    def __init__(self, host, port, container, backlog=5):
        self.host = host
        self.port = port
        self.backlog = backlog
        self.container = container
        self._shutting_down = False

    def _build_ssl_context(self) -> ssl.SSLContext:
        if CERT_FILE and KEY_FILE:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.load_cert_chain(certfile=CERT_FILE, keyfile=KEY_FILE)
            return context
        
        else:
            raise FileNotFoundError("SSL CERT or KEY FILE is not found. Or disable HTTPS to continue.")

    async def _register_connection_manager(self, writer: asyncio.StreamWriter) -> Tuple[int, ConnectionManager]:
        connection_manager = None
        try:
            connection_manager = self.container.get(ConnectionManager)
        except Exception as e:
            print(f"ConnectionManager not found: {e}")
        # get the memory address of the writer as connection_id
        connection_id = id(writer)
        if connection_manager:
            try:
                await connection_manager.register(connection_id)
            except RuntimeError:
                print("Maximum connections reached, closing connection.")
                writer.close()

        return (connection_id, connection_manager)
    
    async def _handle_redirect(self, request: Request):
        host = request.headers.host
        if DEV and host and f":{PORT}" in host:
            host = host.split(":", maxsplit=1)[0] + f":{HTTPS_PORT}"
        https_path = f"https://{host}{request.path}"
        response = Response(status_code=308, disable_default_cookie=True, redirect_to=https_path)
        (encoded_response, _) = response.set_encoded_response()

        return (encoded_response, response)
    

    async def _process_request(self, reader, writer) -> tuple[Request | None, Response | None]:
        request = None
        try:
            (request, handler, is_static_prefix, local_middlewares, cache_middlewares, redirect) = \
                await self.parse_request(reader, writer)
            if redirect:
                encoded_response, response = await self._handle_redirect(request)
            else:
                encoded_response, response = \
                    await self.handle_request(request, handler, writer, is_static_prefix, local_middlewares, cache_middlewares)
        except HTTPError as http_e:
            print(f"HTTP Error: {http_e}")
            encoded_response, response = self.handle_error_response(http_e)
        except Exception as server_e:
            print(f'Internal Error: {server_e}')
            encoded_response, response = self.handle_error_response(InternalServerError())
            
        await self.server_respond(encoded_response, writer)
        return (request, response)
        

    def _should_keep_alive(self, request: Request, response: Response) -> bool:

        if request is None or response is None:
            return False
        

        connection_request = (request.headers.connection or "").lower() if request.headers.connection else ""
        
        if not getattr(request, "body_fully_read", True): return False

        if "close" in connection_request:
            return False
        connection_response = (response.headers.connection or "").lower() if response.headers.connection else ""

        if "close" in connection_response:
            return False
        

        transfer_encoding = (getattr(response.headers, "transfer_encoding", "") or "").lower()

        content_length = getattr(response.headers, "content_length", "") or ""
        has_length = bool(content_length) or ("chunked" in transfer_encoding)
        if not has_length:
            return False
        return True
        
    async def _deregister_connection(self, connection_id, connection_manager, request, writer):
            if connection_manager:
                print(f"Deregistering connection {connection_id}")
                await connection_manager.deregister(connection_id)                

    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        connection_id, connection_manager = await self._register_connection_manager(writer)
        request = None
        try:
            while True:
                (request, response) = await self._process_request(reader, writer)

                if not self._should_keep_alive(request, response):
                    break
        finally:

            await self._deregister_connection(connection_id, connection_manager, request, writer)
   
        await self._close_connection(writer)
        print("Socket has been closed.")

    async def server_respond(self, response: bytes, writer: asyncio.StreamWriter, is_early_hints:bool=False):
        await self._send_response(response, writer)
        # await self._close_connection(writer, is_early_hints)

    async def _send_response(self, response, writer):
        writer.write(response)
        await writer.drain()

    async def _close_connection(self, writer):
        writer.close()
        await writer.wait_closed()
            

    async def init_server(self):
        https_server = None
        if ENABLE_HTTPS == True:
            ssl_context = self._build_ssl_context()
            https_server = await asyncio.start_server(
                client_connected_cb=self._handle_client, 
                host=self.host, 
                port=HTTPS_PORT, 
                ssl=ssl_context
            ) 

        http_server = await asyncio.start_server(
            client_connected_cb=self._handle_client, 
            host=self.host, 
            port=PORT
        )

        return (https_server, http_server)

    async def parse_request(self):
        raise NotImplementedError

    async def handle_request(self):
        raise NotImplementedError

    def handle_error_response(self, http_error):
        response = Response(
            body=http_error.message,
            content_type=ContentType.PLAIN.value,
            status_code=int(http_error.status_code)
        )
        (encoded_response, _) = response.set_encoded_response()
        return encoded_response, response
    

class Server(HTTPServer):
    def __init__(self, host, port, container, backlog=5, concurrency_model=''):
        super().__init__(host, port, container, backlog)
        # self.container = container
        self.concurrency_model = concurrency_model
        self._hook_before_each_handler = []
        self._hook_after_each_handler = []
        self._executor = None
        self._load_concurrency_model()

    def _load_concurrency_model(self):
        if self.concurrency_model =='process':
            print('process')
            self._executor = ProcessPoolExecutor()
        elif self.concurrency_model =='thread':
            print('thread')
            self._executor = ThreadPoolExecutor()
        elif self.concurrency_model == '':
            self._executor = None
        else:
            raise ValueError(f"Unknown concurrency_model: {self.concurrency_model}")

    def set_global_middlewares(self, func):
        self.container.get(MiddlewareChain).add_middleware(func)
        return func

    def set_hook_before_each_handler(self, func):
        self.container.get(MiddlewareChain).add_hook_before_each_handler(func)
        return func
    
    def set_hook_after_each_handler(self, func):
        self.container.get(MiddlewareChain).add_hook_after_each_handler(func)
        return func

    async def _invoke_handler(self, handler, request, local_middlewares, cache_middlewares) -> Response:
        cache = self.container.get('cache')
        wrapped = self.container.get(MiddlewareChain).wrap_handler(handler, local_middlewares, request, cache_middlewares, cache)
        try:
            if asyncio.iscoroutinefunction(wrapped):
                response = await wrapped(request)
                return response
            else:
                if self._executor:
                    loop = asyncio.get_running_loop()
                    response = await loop.run_in_executor(self._executor, wrapped, request)
                    return response
                else:
                    response = wrapped(request)
                    return response
        except Exception as e:
            print(f"Error: {e}")
            raise BadRequest(f"{request.body}")


    async def parse_request(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> HTTPRequestParser:
        return await HTTPRequestParser(container=self.container).parse_request(reader, writer)
    
    def _extract_method_path(self, request) -> tuple[str, str, bool]:
        method, path, is_early_hints_supported = request.method, request.path,request.is_early_hints_supported
        return (method, path, is_early_hints_supported)
    
    async def _handle_early_hints_response(self, writer, custom_hints=[]):
        early_hints_response = EarlyHintsResponse(custom_hints)
        encoded_response, _ = early_hints_response.set_encoded_response()
        await super().server_respond(encoded_response, writer, is_early_hints=True)
    
    async def handle_request(self, request, handler, writer, is_static_prefix, local_middlewares=[], cache_middlewares=[]) -> tuple[bytes, Response]:
        # run the global hook before handler

        (method, path, is_early_hints_supported) = self._extract_method_path(request)

        if method == MethodType.GET.value and is_static_prefix:
            response = await self._handle_static_request(path, writer, is_early_hints_supported)
        elif method == MethodType.POST.value or method == MethodType.GET.value:
            response = await self._invoke_handler(handler, request, local_middlewares, cache_middlewares)
        else:
            raise MethodNotAllowed(f"{method}")
        
        await self.container.get(MiddlewareChain).wrap_response(request, response)
        
        (encoded_response, _) = response.set_encoded_response()
 
        return (encoded_response, response)
    

    async def _handle_static_request(self, path, writer, is_early_hints_supported):
            (file_bytes, content_type, hints) = self.container.get(ServeFile).serve_static_file(path)
            if len(hints) > 0 and is_early_hints_supported:
                await self._handle_early_hints_response(writer, hints)
            response = Response(body=file_bytes, status_code="200", content_type=content_type)
            return response
    


    
    def GET(self, template: str, local_middlewares=[], cache_middlewares=[]):
        def decorator(func):
            self.container.get(RouteToHandler).add_route(template, func, MethodType.GET.value, local_middlewares, cache_middlewares)
            return func
        return decorator

    def POST(self, template: str, local_middlewares=[]):
        def decorator(func):
            self.container.get(RouteToHandler).add_route(template, func, MethodType.POST.value, local_middlewares)
            return func
        return decorator

    def start_server(self):
        async def main():
            (https_server, http_server) = await self.init_server()
            http_msg = f"HTTP listening on {self.host}:{PORT}"
            https_msg = f"; HTTPS on {self.host}:{HTTPS_PORT}" if https_server else ""
            print(f"Server is up and running. {http_msg}{https_msg}")

            loop = asyncio.get_running_loop()
            stop = asyncio.Event() 

            def _shutdown():
                print("\nShutting down...")
                try:
                    if http_server:
                        http_server.close()     
                    if https_server:
                        https_server.close()
                finally:
                
                    try:
                        stop.set()
                    except Exception:
                        pass

            try:
                loop.add_signal_handler(signal.SIGINT, _shutdown)
                loop.add_signal_handler(signal.SIGTERM, _shutdown)
            except NotImplementedError:
                pass

            await stop.wait()

            exec_ = getattr(self, "_executor", None)
            if exec_ is not None:
                try:
                    exec_.shutdown(wait=False, cancel_futures=True)
                except TypeError:
                    exec_.shutdown(wait=False)


            if http_server:
                await http_server.wait_closed()
            if https_server:
                await https_server.wait_closed()

            print("The server has been closed.")

        asyncio.run(main())