from custom_socket import CustomSocket
from http_error import HTTPError, MethodNotAllowed, InternalServerError
from constants import ContentType
from request import CustomRequest
from response import CustomResponse

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
            ContentType.PLAIN,
            http_error.status_code
        )

class Server(HTTPServer):
    def parse_request(self, client_socket):
        return CustomRequest().parse_request(client_socket)
    
    def handle_request(self, request):
        method, path = request['method'], request['path']
        if method == 'GET':
            body = f"GET {path}"
            return CustomResponse(body, ContentType.PLAIN, 200)
        
        elif method == 'POST':
            body = request['body'].decode(request.get('encoding', 'utf-8'))
            return CustomResponse(f"POST: {body}", ContentType.PLAIN, 200)
        
        else:
            raise MethodNotAllowed(f"{method} - Method Not Allowed")


def main():
    server = Server("0.0.0.0", 8080)
    server.start_server()

main()