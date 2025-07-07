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

    # def __create_socket(self) -> CustomSocket:
    #     server_socket = CustomSocket(self.port, self.backlog, self.host)
    #     server_socket.create_and_bind_socket()
    #     print(f"Listening on {self.host}:{self.port}")
    #     return server_socket
    
    # def __enter_accept_state(self, server_socket: CustomSocket):
    #     while True:
    #         (client_socket,  client_address) = server_socket.accept_connection()
    #         print(f"Got request from IP: {client_address}")
    #         try:
    #             request = self.parse_request(client_socket)
    #             response = self.handle_request(request)
    #         except HTTPError as http_error:
    #             response = self.handle_error(http_error)
    #         except Exception as e:    
    #             print("Unexpected:", e)
    #             error = InternalServerError()
    #             response = self.handle_error(error)
    #         client_socket.sendall(response.construct_response())
    #         client_socket.close()

    async def __handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        print("Received a request from a client.")
        print(reader)
        print(writer)


    async def init_server(self):
        server = await asyncio.start_server(client_connected_cb=self.__handle_client, host=self.host, port=self.port) 
        async with server:
            await server.serve_forever()


    def parse_request(self, client_socket):
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

    def parse_request(self, client_socket):
        return CustomRequest().parse_request(client_socket)
    
    def __extract_raw_path_and_method(self, request) -> tuple[str, str]:
        method, path = request['method'], request['path']
        return (method, path)
    
    def handle_request(self, request) -> CustomResponse:
        (method, path) = self.__extract_raw_path_and_method(request)
        if method == MethodType.GET.value:
            response = self.__handle_GET_request(path)
            return response
        elif method == MethodType.POST.value:
            response = self.__handle_POST_request(path, request)
            return response
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