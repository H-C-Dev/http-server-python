import socket
PORT=8080

class CustomSocket:
    def __init__(self, port: int, backlog: int = 5, host: str = socket.gethostname()):
        self.host = host
        self.port = port
        self.backlog = backlog
        self.socket = None

    def __createSocket(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket = s
        print(f"A socket has been created, will now try to bind it to {self.host} with port: {self.port}")

    def __bindPort(self):
        self.socket.bind((self.host, self.port))

    def __listenPort(self):
        self.socket.listen(self.backlog)

    def acceptConnection(self):
        (client_socket, client_address) = self.socket.accept()
        return (client_socket, client_address)
    
    def createAndBindSocket(self):
        self.__createSocket()
        self.__bindPort()
        self.__listenPort()

class CustomRequest:
    def __init__(self, socket: socket.socket, bufsize: int = 4096, encoding: str = 'utf-8'):
        self.socket = socket
        self.bufsize = bufsize
        self.encoding = encoding
        self.val = None
    
    def parseRequest(self) -> any: 
        return self.socket.recv(self.bufsize).decode(self.encoding)

class CustomResponse:
    def __init__(self, message: str, encoding: str = 'utf-8'):
        self.val = (
            "HTTP/1.1 200 OK\r\n"
            f"Content-Type: text/plain; charset={encoding}\r\n"
            f"Content-Length: {len(message)}\r\n"
            "\r\n"
            f"{message}"
        )
    
    def encode(self, encoding: str = 'utf-8'):
        return self.val.encode(encoding)



class Server:
    def __init__(self, port: int = PORT, host: str = socket.gethostname(), backlog: int = 5):
        self.port = port
        self.host = host
        self.backlog = backlog
    
    def initServer(self):
        s = CustomSocket(self.port, self.backlog, self.host)
        s.createAndBindSocket()
        print(f"Listening on port: {self.port}")
        while True:
            (client_socket, client_address) = s.acceptConnection()
            print(f"Got a connection from {client_address}")
            request = CustomRequest(client_socket)
            print(request.parseRequest())
            response = CustomResponse("Welcome to my Chango server")
            client_socket.sendall(response.val.encode('utf-8'))
            client_socket.close()
    


server = Server()
server.initServer()

