import socket
import asyncio
from urllib.parse import parse_qs, unquote_plus
from http_error import HTTPVersionNotSupported
class CustomRequest:
    def __init__(self, bufsize: int = 4096, encoding: str = 'utf-8'):
        self.bufsize = bufsize
        self.encoding = encoding


    async def __receive_byte_data(self, reader: asyncio.StreamReader) -> bytes:
        try:
            data = await reader.readuntil(b"\r\n\r\n")
        except asyncio.IncompleteReadError as e:
            # return what was read if the stream closed before \r\n\r\n
            return e.partial
        return data
        
    def __separate_lines_and_body(self, data: bytes) -> tuple[bytes, bytes]:
        header, space, body = data.partition(b"\r\n\r\n")
        return (header, body)
    
    def __decode_header(self, header: bytes) -> str:
        header_text = header.decode(self.encoding, errors="ignore")
        return header_text
    
    def __split_header_text(self, header_text: str) -> list[str]:
        lines = header_text.split("\r\n")
        return lines

    async def __extract_request_lines_and_body(self, reader: asyncio.StreamReader) -> tuple[bytes, list[str]]:
        data = await self.__receive_byte_data(reader)
        header, body = self.__separate_lines_and_body(data)
        header_text = self.__decode_header(header)
        lines = self.__split_header_text(header_text)
        return (body, lines)
    
    def __check_http_version(self, version):
        if version != "HTTP/1.1":
            raise HTTPVersionNotSupported()

    def __extract_request_line(self, lines):
        method, path, version = lines[0].split(" ")
        self.__check_http_version(version)
        return (method, path, version)
    
    def __parse_headers(self, lines):
        headers = dict()
        for line in lines[1:]:
            if not line:
                continue
            name, value = line.split(":", 1)
            headers[name.strip().lower()] = value.lstrip()

        return headers
    
    def __extract_body(self, body, headers, client_socket: socket.socket):
        content_length = int(headers.get("content-length", "0"))
        # carry on receiving the rest of the TCP packets if the length is bigger than what we received
        while len(body) < content_length:
            body += client_socket.recv(self.bufsize)
        return body
    
    def __extract_path_and_query(self, raw_path):
        # if there is a "?", parse the query
        if "?" in raw_path:
            path, qs = raw_path.split("?", 1)
            query = parse_qs(qs, keep_blank_values=True)
            return (path, query)
        else:
            path = raw_path
            query = {}
            return (path, query)

    async def parse_request(self, reader: asyncio.StreamReader) -> any:
        body, lines = await self.__extract_request_lines_and_body(reader)
        # http method, path and http version in the requestLine
        method, path, version = self.__extract_request_line(lines)
        headers = self.__parse_headers(lines)
        body = self.__extract_body(body, headers, client_socket)
        path, query = self.__extract_path_and_query(path)

        req = {
            "method": method,
            "path": unquote_plus(path),
            "version": version,
            "query": query,
            "body": body,
            "headers": headers
        }

        return req
