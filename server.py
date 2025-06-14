from custom_socket import CustomSocket
from http_error import HTTPError, MethodNotAllowed, InternalServerError, BadRequest
from constants import ContentType, MethodType
from request import CustomRequest
from response import CustomResponse
from route import RouteToHandler
PORT=8080

class HTTPServer:
    def __init__(self, host, port, backlog=5):
        self.host = host
        self.port = port
        self.backlog = backlog

    def __create_socket(self) -> CustomSocket:
        server_socket = CustomSocket(self.port, self.backlog, self.host)
        server_socket.create_and_bind_socket()
        print(f"Listening on {self.host}:{self.port}")
        return server_socket
    
    def __enter_accept_state(self, server_socket: CustomSocket):
        while True:
            (client_socket,  client_address) = server_socket.accept_connection()
            print(f"Got request from IP: {client_address}")
            try:
                request = self.parse_request(client_socket)
                response = self.handle_request(request)
            except HTTPError as http_error:
                response = self.handle_error(http_error)
            except Exception as e:    
                print("Unexpected:", e)
                response = self.handle_error(InternalServerError)
            client_socket.sendall(response.construct_response())
            client_socket.close()

    def start_server(self):
        server_socket = self.__create_socket()
        self.__enter_accept_state(server_socket)

    def parse_request(self, client_socket):
        raise NotImplementedError

    def handle_request(self, request):
        raise NotImplementedError

    def handle_error(self, http_error):
        return CustomResponse(
            http_error.message,
            ContentType.PLAIN.value,
            http_error.status_code
        )

class Server(HTTPServer):

    def __init__(self, host, port, backlog=5):
        super().__init__(host, port, backlog)
        self.router = RouteToHandler()

    def __invoke_handler(self, handler, parameter):
        try:
            if parameter and len(parameter) != 0:
                response = handler(parameter)
                return response
            else:
                response = handler()
                return response
        except Exception as e:
            print(f"Error: {e}")
            raise BadRequest(f"{parameter} - Bad Request")

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
            raise MethodNotAllowed(f"{method} - Method Not Allowed")
        
    def __handle_GET_request(self, path):
        handler, parameters = self.router.match_handler(MethodType.GET.value, path)
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
    
    def POST(self, template, handler):
        self.router.add_route(template, handler, MethodType.POST.value)

    def GET(self, template, handler):
        self.router.add_route(template, handler, MethodType.GET.value)

    


        


