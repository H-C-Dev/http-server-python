import asyncio
from hango.http import HTTPError, MethodNotAllowed, InternalServerError, BadRequest, CustomRequest, CustomResponse, CustomEarlyHintsResponse
from hango.constants import ContentType, MethodType
from hango.routing import RouteToHandler
from hango.utils import ServeFile
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
PORT=8080

class HTTPServer:
    def __init__(self, host, port, backlog=5):
        self.host = host
        self.port = port
        self.backlog = backlog


    async def __handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        try:
            request = await self.parse_request(reader)
            response = await self.handle_request(request, writer)
            await self.__write_response(response, writer)
        except HTTPError as http_e:
            response = self.handle_error_response(http_e)
            await self.__write_response(response, writer)
        except Exception as server_e:
            print(f'Internal Error: {server_e}')
            response = self.handle_error_response(InternalServerError())
            await self.__write_response(response, writer)

    async def write_early_hints_response(self, response: bytes, writer: asyncio.StreamWriter):
        writer.write(response)
        await writer.drain()

    async def __write_response(self, response: bytes, writer: asyncio.StreamWriter):
        writer.write(response)
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    async def init_server(self):
        server = await asyncio.start_server(client_connected_cb=self.__handle_client, host=self.host, port=self.port) 
        return server

    async def parse_request(self, reader: asyncio.StreamReader):
        raise NotImplementedError

    async def handle_request(self, request, writer):
        raise NotImplementedError

    def handle_error_response(self, http_error):
        response = CustomResponse(
            body=http_error.message,
            content_type=ContentType.PLAIN.value,
            status_code=str(http_error.status_code)
        )
        return response.construct_response()

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

    async def __invoke_handler(self, handler, request) -> CustomResponse:
        try:
            if asyncio.iscoroutinefunction(handler):
                response = await handler(request) 
                return response
            else:
                if self.executor:
                    loop = asyncio.get_running_loop()
                    return await loop.run_in_executor(self.executor, (lambda: handler(request)))
                else:
                    response = handler(request)
                    return response
        except Exception as e:
            print(f"Error: {e}")
            raise BadRequest(f"{request['body']}")


    async def parse_request(self, reader: asyncio.StreamReader):
        return await CustomRequest().parse_request(reader)
    
    def __extract_raw_path_and_method(self, request) -> tuple[str, str]:
        method, path, is_early_hints_supported = request['method'], request['path'], request['is_early_hints_supported']
        return (method, path, is_early_hints_supported)
    
    async def __handle_early_hints_response(self, writer, custom_hints=[]):
        early_hints_response = CustomEarlyHintsResponse(custom_hints)
        response = early_hints_response.construct_early_hints_response()
        await super().write_early_hints_response(response, writer)
    
    
    async def handle_request(self, request, writer) -> bytes:
        # run the global hook before handler
        for global_hook in self._hook_before_each_handler:
            result = global_hook(request)
            if asyncio.iscoroutine(result):
                await result

        (method, path, is_early_hints_supported) = self.__extract_raw_path_and_method(request)
        (handler, parameters) = self.router.match_handler(method, path)
        request['params'] = parameters
        if method == MethodType.GET.value and self.serve_file.is_static_prefix(path):
            response = await self.__handle_GET_static_request(path, writer, is_early_hints_supported)
        elif method == MethodType.POST.value or method == MethodType.GET.value:
            response = await self.__invoke_handler(handler, request)
        else:
            raise MethodNotAllowed(f"{method}")
        (formatted_response, dict_response) = response.construct_response()

        for global_hook in self._hook_after_each_handler:
            result = global_hook(request, dict_response)
            if asyncio.iscoroutine(result):
                await result
            
        return formatted_response
    

    async def __handle_GET_static_request(self, path, writer, is_early_hints_supported):
            (file_bytes, content_type, hints) = self.serve_file.serve_static_file(path)
            if len(hints) > 0 and is_early_hints_supported:
                await self.__handle_early_hints_response(writer, hints)
            response = CustomResponse(body=file_bytes, status_code="200", content_type=content_type)
            return response

    
    def GET(self, template: str):
        def decorator(func):
            self.router.add_route(template, func, MethodType.GET.value)
            return func
        return decorator

    def POST(self, template: str):
        def decorator(func):
            self.router.add_route(template, func, MethodType.POST.value)
            return func
        return decorator
    



server = Server("0.0.0.0", PORT, concurrency_model='')