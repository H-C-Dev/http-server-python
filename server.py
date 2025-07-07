import asyncio
# from custom_socket import CustomSocket
from http_error import HTTPError, MethodNotAllowed, InternalServerError, BadRequest
from constants import ContentType, MethodType
from request import CustomRequest
from response import CustomResponse
from route import RouteToHandler
from util import ServeFile
PORT=8080

class HTTPServer:
    def __init__(self, host, port, backlog=5):
        self.host = host
        self.port = port
        self.backlog = backlog


    async def __handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        request = await self.parse_request(reader)
        response = self.handle_request(request)
        await self.__write_response(response, writer)

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

    def handle_request(self, request):
        raise NotImplementedError

    def handle_error(self, http_error):
        return CustomResponse(
            body=http_error.message,
            content_type=ContentType.PLAIN.value,
            status_code=str(http_error.status_code)
        )

class Server(HTTPServer):

    def __init__(self, host, port, backlog=5):
        super().__init__(host, port, backlog)
        self.router = RouteToHandler()
        self.serve_file = ServeFile()

    def __invoke_handler(self, handler, parameter) -> CustomResponse:
        try:
            response = handler(parameter) if parameter else handler()
            return response
        except Exception as e:
            print(f"Error: {e}")
            raise BadRequest(f"{parameter}")

    async def parse_request(self, reader: asyncio.StreamReader):
        return await CustomRequest().parse_request(reader)
    
    def __extract_raw_path_and_method(self, request) -> tuple[str, str]:
        method, path = request['method'], request['path']
        return (method, path)
    
    def handle_request(self, request) -> bytes:
        (method, path) = self.__extract_raw_path_and_method(request)
        if method == MethodType.GET.value:
            response = self.__handle_GET_request(path)   
            return response.construct_response()
        elif method == MethodType.POST.value:
            response = self.__handle_POST_request(path, request)
            return response.construct_response()
        else:
            raise MethodNotAllowed(f"{method}")
    
        
    def __handle_GET_request(self, path):
        if self.serve_file.is_static_prefix(path):
            (file_bytes, content_type) = self.serve_file.serve_static_file(path)
            return CustomResponse(body=file_bytes, status_code="200", content_type=content_type)

        (handler, parameters) = self.router.match_handler(MethodType.GET.value, path)
        response = self.__invoke_handler(handler, parameters)
        return response
    
    def __extract_POST_request_body(self, request):
        body = request['body'].decode(request.get('encoding', 'utf-8'))
        return body
    
    def __handle_POST_request(self, path, request):
        handler, parameters = self.router.match_handler(MethodType.POST.value, path)
        request_body = self.__extract_POST_request_body(request)
        response = self.__invoke_handler(handler, request_body)
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
    


    
server = Server("0.0.0.0", PORT)