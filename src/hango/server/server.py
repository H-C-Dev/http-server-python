import asyncio
from hango.http import HTTPError, MethodNotAllowed, InternalServerError, BadRequest, HTTPRequestParser, Response,EarlyHintsResponse, Forbidden
from hango.core import ContentType, MethodType, CORS
from hango.routing import RouteToHandler
from hango.utils import ServeFile
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from typing import Tuple, Any
PORT=8080

class HTTPServer:
    def __init__(self, host, port, backlog=5):
        self.host = host
        self.port = port
        self.backlog = backlog


    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        try:
            (request, handler, is_static_prefix, local_middlewares) = await self.parse_request(reader, writer)
            response = await self.handle_request(request, handler, writer, is_static_prefix, local_middlewares)
            await self.write_response(response, writer)
        except HTTPError as http_e:
            response = self.handle_error_response(http_e)
            await self.write_response(response, writer)
        except Exception as server_e:
            print(f'Internal Error: {server_e}')
            response = self.handle_error_response(InternalServerError())
            await self.write_response(response, writer)


    async def write_response(self, response: bytes, writer: asyncio.StreamWriter, is_early_hints:bool=False):
        writer.write(response)
        await writer.drain()
        if not is_early_hints:
            writer.close()
            await writer.wait_closed()

    async def init_server(self):
        server = await asyncio.start_server(client_connected_cb=self._handle_client, host=self.host, port=self.port) 
        return server

    async def parse_request(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        raise NotImplementedError

    async def handle_request(self, request, handler, writer, is_static_prefix, local_middlewares):
        raise NotImplementedError

    def handle_error_response(self, http_error):
        response = Response(
            body=http_error.message,
            content_type=ContentType.PLAIN.value,
            status_code=str(http_error.status_code)
        )
        (encoded_response, _) = response.set_encoded_response()
        return encoded_response

class Server(HTTPServer):

    def __init__(self, host, port, backlog=5, concurrency_model=''):
        super().__init__(host, port, backlog)
        self.router = RouteToHandler()
        self.serve_file = ServeFile()
        self._hook_before_each_handler = []
        self._hook_after_each_handler = []
        self._global_middlewares = []

        if concurrency_model =='process':
            print('process')
            self.executor = ProcessPoolExecutor()
        elif concurrency_model =='thread':
            print('thread')
            self.executor = ThreadPoolExecutor()
        elif concurrency_model == '':
            self.executor = None
        else:
            raise ValueError(f"Unknown concurrency_model: {concurrency_model}")

    def set_global_middlewares(self, func):
        self._global_middlewares.append(func)
        return func

    def set_hook_before_each_handler(self, func):
        self._hook_before_each_handler.append(func)
        return func
    
    def set_hook_after_each_handler(self, func):
        self._hook_after_each_handler.append(func)
        return func

    async def _invoke_handler(self, handler, request, local_middlewares) -> Response:
        wrapped = handler
        for local_middleware in local_middlewares:
            wrapped = local_middleware(wrapped)

        for middleware in self._global_middlewares:
            wrapped = middleware(wrapped)
        
        
        try:
            if asyncio.iscoroutinefunction(wrapped):
                response = await wrapped(request)
                return response
            else:
                if self.executor:
                    loop = asyncio.get_running_loop()
                    return await loop.run_in_executor(self.executor, (lambda: wrapped(request)))
                else:
                    response = wrapped(request)
                    return response
        except Exception as e:
            print(f"Error: {e}")
            raise BadRequest(f"{request.body}")


    async def parse_request(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> HTTPRequestParser:
        return await HTTPRequestParser(router=self.router).parse_request(reader, writer)
    
    def _extract_method_path(self, request) -> tuple[str, str, bool]:
        method, path, is_early_hints_supported = request.method, request.path,request.is_early_hints_supported
        return (method, path, is_early_hints_supported)
    
    async def _handle_early_hints_response(self, writer, custom_hints=[]):
        early_hints_response = EarlyHintsResponse(custom_hints)
        encoded_response, _ = early_hints_response.set_encoded_response()
        await super().write_response(encoded_response, writer, is_early_hints=True)
    
    async def handle_request(self, request, handler, writer, is_static_prefix, local_middlewares=[]) -> bytes:
        # run the global hook before handler
        for global_hook in self._hook_before_each_handler:
            result = global_hook(request)
            if asyncio.iscoroutine(result):
                await result
        


        (method, path, is_early_hints_supported) = self._extract_method_path(request)

        if method == MethodType.GET.value and is_static_prefix:
            response = await self._handle_static_request(path, writer, is_early_hints_supported)
        elif method == MethodType.POST.value or method == MethodType.GET.value:
            response = await self._invoke_handler(handler, request, local_middlewares)
        else:
            raise MethodNotAllowed(f"{method}")
        
        (encoded_response, formatted_response) = response.set_encoded_response()

        for global_hook in self._hook_after_each_handler:
            result = global_hook(request, formatted_response)
            if asyncio.iscoroutine(result):
                await result
            
        return encoded_response
    

    async def _handle_static_request(self, path, writer, is_early_hints_supported):
            (file_bytes, content_type, hints) = self.serve_file.serve_static_file(path)
            if len(hints) > 0 and is_early_hints_supported:
                await self._handle_early_hints_response(writer, hints)
            response = Response(body=file_bytes, status_code="200", content_type=content_type)
            return response

    
    def GET(self, template: str, local_middlewares=[]):
        def decorator(func):
            self.router.add_route(template, func, MethodType.GET.value, local_middlewares)
            return func
        return decorator

    def POST(self, template: str, local_middlewares=[]):
        def decorator(func):
            self.router.add_route(template, func, MethodType.POST.value, local_middlewares)
            return func
        return decorator
    



server = Server("0.0.0.0", PORT, concurrency_model='')

@server.set_global_middlewares
def cors_middleware(handler):
    async def wrapped(request):
        user_agent = request.headers.user_agent.lower()
        host = request.headers.host
        is_localhost = request.is_localhost
        cors_header = None
        if 'mozilla' in user_agent or 'chrome' in user_agent or 'safari' in user_agent: 
            if is_localhost:
                pass
            elif '*' in CORS:
                cors_header = "*"
            elif 'http://' + host in CORS: 
                cors_header = 'http://' + host
            elif 'https://' + host in CORS:
                cors_header = 'https://' + host
            else:
                raise Forbidden(message=f"Host {host} is not allowed to access this resource. CORS policy is validated.")
        response = handler(request)
        if asyncio.iscoroutine(response):
             response = await response
        response.cors_header = cors_header
        return response
    return wrapped
    
        