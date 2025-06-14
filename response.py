from constants import http_status_codes_message, ContentType
import json

class CustomResponse:
    def __init__(self, body: str, status_code: str, content_type: str = ContentType.PLAIN.value, encoding: str = 'utf-8'):
        self.status_code = status_code
        self.encoding = encoding
        self.content_type = content_type
        self.body = body
        self.status_line = None
        self.header_block = None

    def __encode_body(self):
        print("encoding...", self.body)
        if isinstance(self.body, (dict, list)):
            text = json.dumps(self.body)
        else:
            text = str(self.body)
        return text.encode(self.encoding)

    
    def __set_status_line(self):
        self.status_line = f"HTTP/1.1 {self.status_code} {http_status_codes_message[self.status_code]}\r\n"
    
    def __set_header_block(self):
        body_len = len(self.__encode_body())
        self.header_block = (
                f"Content-Type: {self.content_type}; charset={self.encoding}\r\n"
                f"Content-Length: {body_len}\r\n"
                "\r\n"
            )
    
    def __encode_and_combine_response(self):
        return self.status_line.encode(self.encoding) + self.header_block.encode(self.encoding) + self.__encode_body()

    def construct_response(self) -> bytes:
        print(self.status_code, "status")
        if self.status_code in http_status_codes_message:
            self.__set_status_line()
            self.__set_header_block()

            return self.__encode_and_combine_response()
        else:
            raise Exception("Status code not found")
        

class CustomJSONResponse(CustomResponse):
    def __init__(self, body: str, status_code: str, encoding: str = 'utf-8'):
        super().__init__(body, status_code,  content_type=ContentType.JSON.value, encoding=encoding)