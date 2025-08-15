from hango.core import EarlyHintsClient, ServiceContainer, allowed_content_type, ENABLE_HTTPS, DEV
import asyncio
from urllib.parse import parse_qs, unquote_plus
from hango.custom_http import HTTPVersionNotSupported, BadRequest
from hango.routing import RouteToHandler
from dataclasses import dataclass, field
from typing import Optional, Any
from hango.custom_http import Forbidden
from hango.utils import ServeFile
from .cookie import parse_cookie
from hango.session import LazySession
import json
BODY_SIZE = 10 * 1024 * 1024


@dataclass
class RequestHeaders:
    content_type: str | None = None
    user_agent: str | None = None
    accept: str | None = None
    host: str | None = None
    accept_encoding: str | None = None
    connection: str | None = None
    content_length: str | None = None
    cookie: dict[str, str] = field(default_factory=dict)
    cookie_part: list[str] = field(default_factory=list)
    transfer_encoding: str | None = None

    def set_content_type(self, content_type: str):
        raw = (content_type or "").strip()
        if not raw:
            self.content_type = None
            return
        main_content_type = raw.split(";", 1)[0].strip().lower()
        allowed = {content_type.lower() for content_type in allowed_content_type}
        is_allowed = False
        for pattern in allowed:
            if self._matches_content_type(pattern, main_content_type):
                is_allowed = True
                break
        if not is_allowed:
            raise BadRequest(f"Content-Type not allowed: {content_type}")
        self.content_type = main_content_type

    def set_user_agent(self, user_agent: str):
        self.user_agent = user_agent
    
    def set_accept(self, accept: str):
        self.accept = accept

    def set_host(self, host: str):
        if not host: 
            raise BadRequest()
        self.host = host
    
    def set_accept_encoding(self, accept_encoding: str):
        self.accept_encoding = accept_encoding
    
    def set_connection(self, connection: str):
        self.connection = connection
    
    def set_content_length(self, content_length: str):
        try:
            content_length = int(content_length) if content_length else 0
        except ValueError:
            raise BadRequest("Invalid Content-Length")
        
        if content_length < 0 or content_length > BODY_SIZE:
            raise BadRequest(f"Content-Length exceeds limit ({BODY_SIZE} bytes)")
        self.content_length = content_length


    def set_cookie_part(self, cookie: str):
        self.cookie_part.append(cookie)

    def set_cookie(self, cookie: dict[str, str]):
        self.cookie = cookie


    def set_transfer_encoding(self, transfer_encoding: str):
        if 'chunked' in transfer_encoding:
            raise BadRequest(f"Chunked not supported yet.")
        self.transfer_encoding = transfer_encoding


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
    

    def _matches_content_type(self, allowed_pattern: str, main_content_type: str) -> bool:
        if allowed_pattern == main_content_type:
            return True
        # wildcard
        if allowed_pattern == "*/*":
            return True
        # pattern range -> "type/*"
        if allowed_pattern.endswith("/*"):
            pattern_type = allowed_pattern.split("/", 1)[0]
            content_type = main_content_type.split("/", 1)[0]
            return pattern_type == content_type
            # suffix wildcard -> "*+json" -any vendor json
        if allowed_pattern == "*+json":
            return main_content_type.endswith("+json")
        # type-scoped +json wildcard -> "type/*+json"
        if allowed_pattern.endswith("/*+json"):
            pattern_type = allowed_pattern.split("/", 1)[0]
            content_type, conetent_sub = main_content_type.split("/", 1)
            return pattern_type == content_type and conetent_sub.endswith("+json")
        return False
    
@dataclass
class Request:
    method: str
    path: str
    version: str
    query: dict
    query_validated: dict
    body: dict | str | None
    body_validated: dict
    headers: RequestHeaders
    is_early_hints_supported: bool
    params: Optional[dict] = field(default_factory=dict)
    is_localhost: bool = False
    session: LazySession | None = None
    body_fully_read: bool = False


class HTTPRequestParser:
    def __init__(self, container, bufsize: int = 4096, encoding: str = 'utf-8'):
        if container is None:
            raise RuntimeError("HTTPRequestParser requires a ServiceContainer")
        self.container = container 
        self.bufsize = bufsize
        self.encoding = encoding
        # self.serve_file = ServeFile()



    async def _receive_byte_data(self, reader: asyncio.StreamReader) -> bytes:
        IDLE_TIMEOUT = 5.0        
        HEADER_TIMEOUT = 5.0     
        MAX_HEADER_BYTES = 64 * 1024

        loop = asyncio.get_running_loop()
        try:
            first = await asyncio.wait_for(reader.read(1), timeout=IDLE_TIMEOUT)
        except asyncio.TimeoutError:
            raise asyncio.IncompleteReadError(partial=b"", expected=1)

        if first == b"": 
            raise asyncio.IncompleteReadError(partial=b"", expected=1)

        buf = bytearray(first)
        if b"\r\n\r\n" in buf:
            return bytes(buf)

        deadline = loop.time() + HEADER_TIMEOUT
        while b"\r\n\r\n" not in buf:
            remaining = deadline - loop.time()
            if remaining <= 0:
                raise BadRequest("Header read timeout")

            try:
                chunk = await asyncio.wait_for(reader.read(self.bufsize), timeout=remaining)
            except asyncio.TimeoutError:
                raise BadRequest("Header read timeout")

            if chunk == b"": 
                if buf:
                    raise BadRequest("Malformed request headers")
                raise asyncio.IncompleteReadError(partial=b"", expected=1)

            buf += chunk
            if len(buf) > MAX_HEADER_BYTES:
                raise BadRequest("Header too large")

        return bytes(buf)
            
        
    def _separate_lines_and_body(self, data: bytes) -> tuple[bytes, bytes]:
        headers, _, body = data.partition(b"\r\n\r\n")
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
    

    def _set_cookie_header(self, set_cookie, cookie_part):
        cookie_value = parse_cookie(cookie_part)
        set_cookie(cookie_value)
    
    
    def _parse_headers(self, lines):
        headers = RequestHeaders()
        setter_map = {
            "content-type": headers.set_content_type,
            "user-agent": headers.set_user_agent,
            "accept": headers.set_accept,
            "host": headers.set_host,
            "accept-encoding": headers.set_accept_encoding,
            "connection": headers.set_connection,
            "content-length": headers.set_content_length,
            "cookie": headers.set_cookie_part,
            "transfer-encoding": headers.set_transfer_encoding,
        }
        for line in lines[1:]:
            if not line:
                continue
            name, value = line.split(":", 1)
            name = name.strip().lower()
            value = value.lstrip()
            if setter_map.get(name):
                setter_map[name](value)

        self._set_cookie_header(headers.set_cookie, headers.cookie_part)
        return (headers)
    
    

    def _is_client_localhost(self, writer: asyncio.StreamWriter) -> bool:
        peer_ip, _ = writer.get_extra_info('peername')
        if peer_ip in ('127.0.0.1', '::1'):
                return True
        return False


    async def _extract_body(self, body, body_fully_read, headers, reader: asyncio.StreamReader):
        content_length = int(headers.content_length) if headers.content_length != None else 0
        remaining_bufsize = content_length - len(body)
        # carry on receiving the rest of the TCP packets if the length is bigger than what we received
        while len(body) < content_length:
            remaining_bufsize = content_length - len(body)
            body += await reader.read(min(self.bufsize, remaining_bufsize))

        body_fully_read = (len(body) == content_length)
        return body, body_fully_read
    
    def _extract_path_and_query(self, raw_path):
        # if there is a "?", parse the query
        if "?" in raw_path:
            path, qs = raw_path.split("?", 1)
            query = parse_qs(qs, keep_blank_values=True)
            sorted_query = {k: v for k, v in sorted(list(query.items()))}
            return (path, sorted_query)
        else:
            path = raw_path
            query = {}
            return (path, query)
        
    def _client_supports_early_hints(self, user_agent: str) -> bool:
        if EarlyHintsClient.FIREFOX.value.upper() in user_agent.upper():
            return True
        return False
    
    def _is_https(self, writer: asyncio.StreamWriter):
        if writer.get_extra_info('ssl_object') is not None or DEV == False:
            return True
        return False
    

    async def parse_request(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> Any:
        is_localhost = self._is_client_localhost(writer)
        is_https = self._is_https(writer)
        body_fully_read = False

        body, lines = await self._extract_request_lines_and_body(reader)
        method, path, version = self._extract_request_line(lines)
        headers = self._parse_headers(lines)

        if not is_https and not is_localhost:
            request = Request(method, path, version, {}, {}, None, {}, headers, False, params=None, is_localhost=is_localhost, body_fully_read=False)
            return (request, None, False, None, None, True)
        
        is_early_hints_supported = self._client_supports_early_hints(headers.user_agent)
        body, body_fully_read = await self._extract_body(body, body_fully_read, headers, reader)
        path, query = self._extract_path_and_query(path)

        body = body.decode(self.encoding, errors='ignore')
        if headers.content_type and 'json' in headers.content_type.lower():
            body = json.loads(body)
        request = Request(method, unquote_plus(path), version, query, {}, body, {}, headers, is_early_hints_supported, params=None, is_localhost=is_localhost, body_fully_read=body_fully_read)
        serve_file = self.container.get(ServeFile)
        if serve_file.is_static_prefix(path):
            return (request, None, True, None, None, False)
        (handler, parameters, local_middlewares, cache_middlewares) = self.container.get(RouteToHandler).match_handler(method, path)
        request.params = parameters
        return (request, handler, False, local_middlewares, cache_middlewares, False)