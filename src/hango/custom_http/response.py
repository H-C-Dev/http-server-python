from hango.core import http_status_codes_message, ContentType
import json
from dataclasses import dataclass
from hango.utils import response_time
from typing import Optional, Tuple, Union
@dataclass
class ResponseHeaders:
    def __init__(self, status_code: int, status_message: str, date: str, server: str, content_type: str, content_length: int, connection: str | None = "keep-alive", cors_header: str | None = None, set_cookie: str | None = None, location: str | None = None, hsts: bool = False, hsts_max_age: int = 31536000):
        self.start_line: str = f"HTTP/1.1 {status_code} {status_message}\r\n"
        self.date: str = f"Date: {date}\r\n"
        self.server: str = f"Server: {server}\r\n"
        self.content_type: str = f"Content-Type: {content_type}\r\n" if content_type else ""
        self.content_length: str = (f"Content-Length: {content_length}\r\n" if content_length else "Content-Length: 0\r\n")
        self.connection: str = f"Connection: {connection}\r\n" if connection else f"Connection: keep-alive\r\n"
        self.cors_header: str = f"Access-Control-Allow-Origin: {cors_header}\r\n" if cors_header else ""
        self.set_cookie: str = f"Set-Cookie: {set_cookie}\r\n" if set_cookie else ""
        self.transfer_encoding: str = ""
        self.location: str = f"Location: {location}\r\n" if location else ""
        self.hsts_max_age: int = hsts_max_age
        self.hsts: str = f"Strict-Transport-Security: max-age={hsts_max_age}; includeSubDomains\r\n" if hsts else ""
        self.content_type_options: str = "X-Content-Type-Options: nosniff"
        self.referrer: str = "Referrer-Policy: no-referrer"
        self.frame_options: str = "X-Frame-Options: DENY"
    
    def return_response_headers(self) -> str:     
        return (
            self.start_line +
            self.date +
            self.server +
            self.content_type +
            self.content_length  +
            self.connection + 
            self.cors_header +
            self.set_cookie +
            self.location +
            self.hsts +
            self.content_type_options +
            self.referrer +
            self.frame_options +
            "\r\n"
        )


@dataclass
class Response:
    def __init__(self, status_code: int | str, content_type: str | None = None, body: str | None = None, disable_default_cookie: bool = False, redirect_to: str | None = None, is_https: bool = False):
        self.encoding = 'utf-8'
        self.status_code: Union[int, str] = status_code
        self.headers: ResponseHeaders | None = None
        self.body: Optional[str] = json.dumps(body) if isinstance(body, (dict, list)) else body 
        self.content_type = (content_type if content_type
                             else ContentType.JSON.value if isinstance(body, (dict, list))
                             else ContentType.PLAIN.value if body == None
                             else None)
        self.cors_header = None
        self.set_cookie = None
        self.disable_default_cookie = disable_default_cookie
        self.transfer_encoding = ""
        self.redirect_to = redirect_to
        self._is_https: bool = is_https

        
    def get_headers(self, content_length):
        headers = ResponseHeaders(
            status_code=self.status_code,
            status_message=http_status_codes_message[str(self.status_code)],
            date=response_time(),
            server="HANGO",
            content_type=self.content_type,
            content_length=content_length,
            cors_header= self.cors_header if self.cors_header else None,
            set_cookie= self.set_cookie if self.set_cookie else None,
            location=self.redirect_to,
            connection="close" if self.redirect_to else None,
            hsts=self._is_https

        )
        return headers


    def set_headers(self):
        if not http_status_codes_message[str(self.status_code)]:
            raise ValueError(f"Invalid status code: {self.status_code}")
        
        if isinstance(self.body, bytes):
            content_length = len(self.body)
        elif self.body is None:
            content_length = 0
        else:
            content_length = len(str(self.body).encode(self.encoding))

        headers = self.get_headers(content_length)

        self.headers = headers
        

    def set_encoded_response(self, is_https) -> Tuple[bytes, str]:
        if is_https:
            self._is_https = True
        self.set_headers()
        if self.headers is None:
            raise ValueError("Response headers have not been set.")
        header_bytes = self.headers.return_response_headers().encode(self.encoding)
 
        if isinstance(self.body, bytes):
            encoded_response = header_bytes + self.body
            formatted_response = self.headers.return_response_headers() + "[binary body]"
        else:
            body_text = "" if self.body is None else str(self.body)
            formatted_response = self.headers.return_response_headers() + body_text
            encoded_response = formatted_response.encode(self.encoding)
        return (encoded_response, formatted_response)

class EarlyHintsResponse(Response):
    def __init__(self, hints: list):
        super().__init__(status_code=103)
        self.hints = hints

    def _set_early_hints_header(self):
        early_hints_header = ""
        for hint in self.hints:
            early_hints_header += f"Link: <{hint['url']}>; rel={hint['rel']}; as={hint['as']}; type={hint['type']}\r\n"
        early_hints_header += "\r\n"
        return early_hints_header

    def set_encoded_response(self, is_https) -> Tuple[bytes, str]:
        if is_https:
            self._is_https = True
        super().set_headers()
        early_hints_header = self._set_early_hints_header()
        if self.headers is None:
            raise ValueError("Response headers have not been set.")
        formatted_response = self.headers.return_response_headers()[:-4] + early_hints_header
        print('[FORMATTED EARLY HINTS RESPONSE]', formatted_response)
        encoded_response = formatted_response.encode(self.encoding)
        return (encoded_response, formatted_response)