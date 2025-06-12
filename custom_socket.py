import socket

class CustomSocket:
    def __init__(self, port: int, backlog: int = 5, host: str = socket.gethostname()):
        self.host = host
        self.port = port
        self.backlog = backlog
        self.val = None

    def __create_socket(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.val = s
        print(f"A socket has been created, will now try to bind it to {self.host} with port: {self.port}")

    def __bind_port(self):
        self.val.bind((self.host, self.port))

    def __listenPort(self):
        self.val.listen(self.backlog)

    def accept_connection(self):
        (clientSocket, clientAddress) = self.val.accept()
        return (clientSocket, clientAddress)
    
    def create_and_bind_socket(self):
        self.__create_socket()
        self.__bind_port()
        self.__listenPort()
