import socket
from urllib.parse import parse_qs, unquote_plus

class CustomRequest:
    def __init__(self, bufsize: int = 4096, encoding: str = 'utf-8'):
        self.bufsize = bufsize
        self.encoding = encoding

    def __receive_header_line(self, client_socket: socket.socket):
        # empty byte
        data = b""
        while b"\r\n\r\n" not in data:
            chunk = client_socket.recv(self.bufsize)
            # if we no longer receive any chunk, also end the loop
            if not chunk:
                break
            data += chunk
        
        header, space, body = data.partition(b"\r\n\r\n")
        headerText = header.decode(self.encoding, errors="ignore")
        lines = headerText.split("\r\n")
        return (lines, body)
    
    def __extracrt_request_line(self, lines):
        return lines[0].split(" ")
    
    def __parse_headers(self, lines):
        headers = dict()
        for line in lines[1:]:
            if not line:
                continue
            name, value = line.split(":", 1)
            headers[name.strip().lower()] = value.lstrip()

        return headers
    
    def __extract_body(self, body, headers, client_socket: socket.socket):
        contentLength = int(headers.get("content-length", "0"))
        # carry on receiving the rest of the TCP packets if the length is bigger than what we received
        while len(body) < contentLength:
            body += client_socket.recv(self.bufsize)
        return body
    
    def __extract_path_and_query(self, rawPath):
        # if there is a "?", parse the query
        if "?" in rawPath:
            path, qs = rawPath.split("?", 1)
            query = parse_qs(qs, keep_blank_values=True)
            return (path, query)
        else:
            path = rawPath
            query = {}
            return (path, query)

    
    def parse_request(self, client_socket: socket.socket) -> any:
        lines, body = self.__receive_header_line(client_socket)
        # http method, path and http version in the requestLine
        method, path, version = self.__extracrt_request_line(lines)
        headers = self.__parse_headers(lines)
        body = self.__extract_body(body, headers, client_socket)
        path, query = self.__extract_path_and_query(path)

        return {
            "method": method,
            "path": unquote_plus(path),
            "version": version,
            "query": query,
            "body": body,
            "headers": headers
        }
