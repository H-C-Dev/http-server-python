from hango.constants import EarlyHintsClient
import asyncio
from urllib.parse import parse_qs, unquote_plus
from hango.http import HTTPVersionNotSupported
from hango.routing import RouteToHandler
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class RequestHeader:
    content_type: Optional[str] = None
    user_agent: Optional[str] = None
    accept: Optional[str] = None
    host: Optional[str] = None
    accept_encoding: Optional[str] = None
    connection: Optional[str] = None
    content_length: Optional[str] = None

    def set_content_type(self, content_type: str):
        self.content_type = content_type

    def set_user_agent(self, user_agent: str):
        self.user_agent = user_agent
    
    def set_accept(self, accept: str):
        self.accept = accept

    def set_host(self, host: str):
        self.host = host
    
    def set_accept_encoding(self, accept_encoding: str):
        self.accept_encoding = accept_encoding
    
    def set_connection(self, connection: str):
        self.connection = connection
    
    def set_content_length(self, content_length: str):
        self.content_length = content_length

    def get_header(self) -> dict:
        return {
            "content_type": self.content_type,
            "user_agent": self.user_agent,
            "accept": self.accept,
            "host": self.host,
            "accept_encoding": self.accept_encoding,
            "connection": self.connection,
            "content_length": self.content_length
        }
    
@dataclass
class Request:
    method: str
    path: str
    version: str
    query: dict
    body: str
    header: RequestHeader
    is_early_hints_supported: bool
    params: dict = field(default_factory=dict)


class CustomRequest:
    def __init__(self, router: RouteToHandler, bufsize: int = 4096, encoding: str = 'utf-8'):
        self.bufsize = bufsize
        self.encoding = encoding
        self.router = router


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
        header = RequestHeader()
        setter_map = {
            "content-type": header.set_content_type,
            "user-agent": header.set_user_agent,
            "accept": header.set_accept,
            "host": header.set_host,
            "accept-encoding": header.set_accept_encoding,
            "connection": header.set_connection,
            "content-length": header.set_content_length 
        }
        for line in lines[1:]:
            if not line:
                continue
            name, value = line.split(":", 1)
            name = name.strip().lower()
            value = value.strip()
            if setter_map.get(name):
                setter_map[name](value)

        return (header)
    
    
    async def __extract_body(self, body, header, reader: asyncio.StreamReader):
        content_length = int(header.content_length) if header.content_length != None else 0
        # carry on receiving the rest of the TCP packets if the length is bigger than what we received
        while len(body) < content_length:
            body += await reader.read(self.bufsize)
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
        
    def __client_supports_early_hints(self, user_agent: str) -> bool:
        if EarlyHintsClient.FIREFOX.value.upper() in user_agent.upper():
            return True
        return False

    async def parse_request(self, reader: asyncio.StreamReader) -> any:
        body, lines = await self.__extract_request_lines_and_body(reader)
        method, path, version = self.__extract_request_line(lines)
        header = self.__parse_headers(lines)

        is_early_hints_supported = self.__client_supports_early_hints(header.user_agent)
        body = await self.__extract_body(body, header, reader)
        path, query = self.__extract_path_and_query(path)
        (handler, parameters) = self.router.match_handler(method, path)

        request = Request(method, unquote_plus(path), version, query, body.decode(self.encoding, errors='ignore'), header, is_early_hints_supported, parameters)
        return (request, handler)