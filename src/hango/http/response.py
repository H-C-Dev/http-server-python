from hango.constants import http_status_codes_message, ContentType
import json
from dataclasses import dataclass

# class CustomResponse:
#     def __init__(self, body: bytes | str | dict | list, status_code: str | int, content_type: str = ContentType.PLAIN.value, encoding: str = 'utf-8'):
#         self.status_code = str(status_code)
#         self.encoding = encoding
#         self.content_type = content_type
#         self.body = body
#         self.status_line = None
#         self.header_block = None

#     def __encode_body(self):
#         if isinstance(self.body, (dict, list)):
#             text = json.dumps(self.body)
#             return text.encode(self.encoding)
#         if isinstance(self.body, bytes):
#             return self.body
#         return str(self.body).encode(self.encoding)

#     def __set_status_line(self):
#         self.status_line = f"HTTP/1.1 {self.status_code} {http_status_codes_message[self.status_code]}\r\n"
    
#     def __set_header_block(self):
#         body_len = len(self.__encode_body())
#         self.header_block = (
#                 f"Content-Type: {self.content_type}; charset={self.encoding}\r\n"
#                 f"Content-Length: {body_len}\r\n"
#                 "\r\n"
#             )
    
#     def __encode_and_combine_response(self):
#         return self.status_line.encode(self.encoding) + self.header_block.encode(self.encoding) + self.__encode_body()

#     def construct_response(self, request, host) -> bytes:

#         request_headers = ResponseHeaders(self.status_code, http_status_codes_message[self.status_code], "Mon, 01 Jan 2024 00:00:00 GMT", "HANGO", self.content_type, len(self.__encode_body()))
#         if str(self.status_code) in http_status_codes_message:
#             self.__set_status_line()
#             self.__set_header_block()
#             dict_response = self.__return_response_detail()
#             formatted_response = self.__encode_and_combine_response()
#             return (formatted_response, dict_response)
#         else:
#             raise Exception("Status code not found")
        
#     def __return_response_detail(self):
#         return {"status_code": self.status_code, "header": self.status_line + self.header_block, "body": self.__encode_and_combine_response(), "content_type": self.content_type}


# class CustomEarlyHintsResponse(CustomResponse):
#     def __init__(self, hints):
#         super().__init__(body="", status_code=103,  content_type=ContentType.JSON.value)
#         self.hints = hints

#     def __set_early_hints_status_line(self):
#         self.status_line = f"HTTP/1.1 {self.status_code} {http_status_codes_message[self.status_code]}\r\n"
    


#     def __set_early_hints_header_block(self):
#         header_block = ""
#         for hint in self.hints:
#              header_block += (
#                     f"Link: <{hint['url']}>; rel={hint['rel']}; as={hint['as']}; type={hint['type']}\r\n"
#                 )
#         header_block += "\r\n"
#         self.header_block = header_block

 
#     def __encode_and_combine_early_hints_response(self):
#         return self.status_line.encode(self.encoding) + self.header_block.encode(self.encoding)

#     def construct_early_hints_response(self) -> bytes:
#         self.__set_early_hints_status_line()
#         self.__set_early_hints_header_block()
#         formatted_response = self.__encode_and_combine_early_hints_response()
#         print('[FORMATTED RESPONSE]', formatted_response)
#         return formatted_response

# class CustomJSONResponse(CustomResponse):
#     def __init__(self, body: str, status_code: str, encoding: str = 'utf-8'):
#         super().__init__(body, status_code,  content_type=ContentType.JSON.value, encoding=encoding)

@dataclass
class ResponseHeaders:
    def __init__(self, status_code: int, status_message: str, date: str, server: str, content_type: str, content_length: int, connection: str = "keep-alive", cors_header: str = None):
        self.start_line = f"HTTP/1.1 {status_code} {status_message}\r\n"
        self.date = f"Date: {date}\r\n"
        self.server = f"Server: {server}\r\n"
        self.content_type = content_type if f"Content-Type: {content_type}\r\n" else None
        self.content_length = content_length if f"Content-Length: {str(content_length)}\r\n" else None
        self.connection = f"Connection: {connection}\r\n"
        self.cors_header = cors_header if f"Access-Control-Allow-Origin: {cors_header}\r\n" else None
    
    def return_response_headers(self):     
        return (
            self.start_line +
            self.date +
            self.server +
            (self.content_type if self.content_type else "") +
            (self.content_length if self.content_length else "") +
            self.connection + 
            (self.cors_header if self.cors_header else "") +
            "\r\n"
        )


@dataclass
class Response:
    def __init__(self, status_code: int, content_type: str = None, body: str = None):
        self.encoding = 'utf-8'
        self.status_code: int = status_code
        self.headers: ResponseHeaders = None
        self.body: str = json.dumps(body) if isinstance(body, (dict, list)) else body 
        self.content_type = (content_type if content_type
                             else ContentType.JSON.value if isinstance(body, (dict, list))
                             else ContentType.PLAIN.value if body == None
                             else None)
        
    def set_headers(self, cors_header):
        if not http_status_codes_message[str(self.status_code)]:
            raise ValueError(f"Invalid status code: {self.status_code}")
        
        if isinstance(self.body, bytes):
            content_length = str(len(self.body))
        elif not isinstance(self.body, bytes):
            content_length = str(len(str(self.body).encode(self.encoding)))
        else:
            content_length = None

        headers = ResponseHeaders(
            status_code=self.status_code,
            status_message=http_status_codes_message[str(self.status_code)],
            date="Mon, 01 Jan 2024 00:00:00 GMT",
            server="HANGO",
            content_type=self.content_type,
            content_length=content_length,
            cors_header= cors_header if cors_header else None
        )
        self.headers = headers
        

    def set_encoded_response(self, cors_header=None) -> bytes:
        self.set_headers(cors_header)
        if isinstance(self.body, bytes):
            encoded_response = self.headers.return_response_headers().encode(self.encoding) + self.body 
            formatted_response = self.headers.return_response_headers() + "Body is a bytes object"
        else:
            formatted_response = self.headers.return_response_headers() + str(self.body)
            encoded_response = formatted_response.encode(self.encoding)
        return (encoded_response, formatted_response)

class EarlyHintsResponse(Response):
    def __init__(self, hints: list):
        super().__init__(status_code=103)
        self.hints = hints

    def set_encoded_response(self) -> bytes:
        super().set_headers(None)
        early_hints_header = ""
        for hint in self.hints:
            early_hints_header += f"Link: <{hint['url']}>; rel={hint['rel']}; as={hint['as']}; type={hint['type']}\r\n"
        early_hints_header += "\r\n"
        print('[EARLY HINTS HEADER]')
        print(self.headers.connection)
        print(self.headers.content_type)
        print(self.headers.content_length)
        print(self.headers.date)
        formatted_response = self.headers.return_response_headers()[:-4] + early_hints_header
        print('[FORMATTED EARLY HINTS RESPONSE]', formatted_response)
        print(type(formatted_response))
        encoded_response = formatted_response.encode(self.encoding)
        return (encoded_response, formatted_response)