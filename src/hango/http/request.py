from hango.core import EarlyHintsClient
import asyncio
from urllib.parse import parse_qs, unquote_plus
from hango.http import HTTPVersionNotSupported
from hango.routing import RouteToHandler
from dataclasses import dataclass, field
from typing import Optional, Any
from hango.core import CORS
from hango.http import Forbidden
from hango.utils import ServeFile
@dataclass
class RequestHeaders:
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
    headers: RequestHeaders
    is_early_hints_supported: bool
    params: Optional[dict] = field(default_factory=dict)
    is_localhost: bool = False


class HTTPRequestParser:
    def __init__(self, router: RouteToHandler, bufsize: int = 4096, encoding: str = 'utf-8'):
        self.bufsize = bufsize
        self.encoding = encoding
        self.router = router
        self.serve_file = ServeFile()


    async def _receive_byte_data(self, reader: asyncio.StreamReader) -> bytes:
        try:
            data = await reader.readuntil(b"\r\n\r\n")
        except asyncio.IncompleteReadError as e:
            # return what was read if the stream closed before \r\n\r\n
            return e.partial
        print('[RECEIVED DATA]', data)
        return data
        
    def _separate_lines_and_body(self, data: bytes) -> tuple[bytes, bytes]:
        headers, space, body = data.partition(b"\r\n\r\n")
        return (headers, body)
    
    def _decode_header(self, headers: bytes) -> str:
        header_text = headers.decode(self.encoding, errors="ignore")
        return header_text
    
    def _split_header_text(self, header_text: str) -> list[str]:
        lines = header_text.split("\r\n")
        return lines

    async def _extract_request_lines_and_body(self, reader: asyncio.StreamReader) -> tuple[bytes, list[str]]:
        data = await self._receive_byte_data(reader)
        headers, body = self._separate_lines_and_body(data)
        header_text = self._decode_header(headers)
        lines = self._split_header_text(header_text)
        
        return (body, lines)
    
    def _check_http_version(self, version):
        if version != "HTTP/1.1":
            raise HTTPVersionNotSupported()

    def _extract_request_line(self, lines):
        method, path, version = lines[0].split(" ")
        self._check_http_version(version)
        return (method, path, version)
    



    
    def _parse_headers(self, lines):
        headers = RequestHeaders()
        setter_map = {
            "content-type": headers.set_content_type,
            "user-agent": headers.set_user_agent,
            "accept": headers.set_accept,
            "host": headers.set_host,
            "accept-encoding": headers.set_accept_encoding,
            "connection": headers.set_connection,
            "content-length": headers.set_content_length 
        }
        for line in lines[1:]:
            if not line:
                continue
            name, value = line.split(":", 1)
            name = name.strip().lower()
            value = value.lstrip()
            if setter_map.get(name):
                setter_map[name](value)

        return (headers)
    
    

    def _is_client_localhost(self, writer: asyncio.StreamWriter) -> bool:
        peer_ip, _ = writer.get_extra_info('peername')
        if peer_ip in ('127.0.0.1', '::1'):
                return True
        return False


    async def _extract_body(self, body, headers, reader: asyncio.StreamReader):
        content_length = int(headers.content_length) if headers.content_length != None else 0
        # carry on receiving the rest of the TCP packets if the length is bigger than what we received
        while len(body) < content_length:
            body += await reader.read(self.bufsize)
        return body
    
    def _extract_path_and_query(self, raw_path):
        # if there is a "?", parse the query
        if "?" in raw_path:
            path, qs = raw_path.split("?", 1)
            query = parse_qs(qs, keep_blank_values=True)
            return (path, query)
        else:
            path = raw_path
            query = {}
            return (path, query)
        
    def _client_supports_early_hints(self, user_agent: str) -> bool:
        if EarlyHintsClient.FIREFOX.value.upper() in user_agent.upper():
            return True
        return False

    async def parse_request(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> Any:
        body, lines = await self._extract_request_lines_and_body(reader)
        method, path, version = self._extract_request_line(lines)
        headers = self._parse_headers(lines)
        is_early_hints_supported = self._client_supports_early_hints(headers.user_agent)
        body = await self._extract_body(body, headers, reader)
        path, query = self._extract_path_and_query(path)
        is_localhost = self._is_client_localhost(writer)
        request = Request(method, unquote_plus(path), version, query, body.decode(self.encoding, errors='ignore'), headers, is_early_hints_supported, params=None, is_localhost=is_localhost)
        if self.serve_file.is_static_prefix(path):
            return (request, None, self.serve_file.is_static_prefix(path), None)
        (handler, parameters, local_middlewares) = self.router.match_handler(method, path)
        request.params = parameters
        return (request, handler, False, local_middlewares)