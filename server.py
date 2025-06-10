import socket
from urllib.parse import parse_qs, unquote_plus
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
        (clientSocket, clientAddress) = self.socket.accept()
        return (clientSocket, clientAddress)
    
    def createAndBindSocket(self):
        self.__createSocket()
        self.__bindPort()
        self.__listenPort()

class CustomRequest:
    def __init__(self, socket: socket.socket, bufsize: int = 4096, encoding: str = 'utf-8'):
        self.socket = socket
        self.bufsize = bufsize
        self.encoding = encoding

    def __receiveHeaderLine(self):
        # empty byte
        data = b""
        while b"\r\n\r\n" not in data:
            chunk = self.socket.recv(self.bufsize)
            # if we no longer receive any chunk, also end the loop
            if not chunk:
                break
            data += chunk
        
        header, space, body = data.partition(b"\r\n\r\n")
        headerText = header.decode(self.encoding, errors="ignore")
        lines = headerText.split("\r\n")
        return (lines, body)
    
    def __extracrtRequestLine(self, lines):
        return lines[0].split(" ")
    
    def __parseHeaders(self, lines):
        headers = dict()
        for line in lines[1:]:
            if not line:
                continue
            name, value = line.split(":", 1)
            headers[name.strip().lower()] = value.lstrip()

        return headers
    
    def __extractBody(self, body, headers):
        contentLength = int(headers.get("content-length", "0"))
        # carry on receiving the rest of the TCP packets if the length is bigger than what we received
        while len(body) < contentLength:
            body += self.socket.recv(self.bufsize)
        return body
    
    def __extractPathAndQuery(self, rawPath):
        # if there is a "?", parse the query
        if "?" in rawPath:
            path, qs = rawPath.split("?", 1)
            query = parse_qs(qs, keep_blank_values=True)
            return (path, query)
        else:
            path = rawPath
            query = {}
            return (path, query)

    
    def parseRequest(self) -> any:
        lines, body = self.__receiveHeaderLine()
        # http method, path and http version in the requestLine
        method, path, version = self.__extracrtRequestLine(lines)
        headers = self.__parseHeaders(lines)
        body = self.__extractBody(body, headers)
        path, query = self.__extractPathAndQuery(path)

        return {
            "method": method,
            "path": unquote_plus(path),
            "version": version,
            "query": query,
            "body": body,
            "headers": headers
        }


httpStatusCode = {
    200: "OK",
    404: "Not Found"
}

contentType = {
    "application/json":"application/json",
    "text/plain":"text/plain"
    
    }


class CustomResponse:
    def __init__(self, message: str, contentType, statusCode, encoding: str = 'utf-8'):
        self.statusCode = statusCode
        self.encoding = encoding
        self.contentType = contentType
        self.message = message
        self.statusLine = None
        self.header = None
        self.body = None
        self.val = None

    def constructResponse(self) -> bytes:
        if self.statusCode in httpStatusCode:
            self.statusLine = f"HTTP/1.1 {self.statusCode} {httpStatusCode[self.statusCode]}\r\n"
            response = (
                f"{self.statusLine}"
                f"Content-Type: {self.contentType}; charset={self.encoding}\r\n"
                f"Content-Length: {len(self.message)}\r\n"
                "\r\n"
                f"{self.message}"
            )
            self.val = response
            formattedRes = self.__encode()
            return formattedRes
        else:
            raise Exception("Status code not found")


    def __encode(self):
        return self.val.encode(self.encoding)



class Server:
    def __init__(self, port: int = PORT, host: str = socket.gethostname(), backlog: int = 5):
        self.port = port
        self.host = host
        self.backlog = backlog
        self.socket = None
    
    def initServer(self):
        s = CustomSocket(self.port, self.backlog, self.host)
        s.createAndBindSocket()
        print(f"Listening on port: {self.port}")
        self.socket = s
        while True:
            (clientSocket, clientAddress) = s.acceptConnection()
            print(f"Got a connection from {clientAddress}")
            request = CustomRequest(clientSocket)
            print(request.parseRequest())
            response = CustomResponse("Welcome to my Hango server", "text/plain", 200)
            print(response.constructResponse())
            clientSocket.sendall(response.constructResponse())
            clientSocket.close()
        
        

        

server = Server(8080, "0.0.0.0")
server.initServer()

