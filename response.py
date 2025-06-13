from constants import http_status_codes_message

class CustomResponse:
    def __init__(self, body: str, content_type, status_code, encoding: str = 'utf-8'):
        self.status_code = status_code
        self.encoding = encoding
        self.content_type = content_type
        self.body = body
        self.status_line = None
        self.header_block = None

    def __encode_body(self):
        return self.body.encode(self.encoding)
        
    def __encode_and_combine_response(self):
        return self.status_line.encode(self.encoding) + self.header_block.encode(self.encoding) + self.__encode_body()
    
    def construct_response(self) -> bytes:
        if self.status_code in http_status_codes_message:
            body_len = len(self.__encode_body())
            self.status_line = f"HTTP/1.1 {self.status_code} {http_status_codes_message[self.status_code]}\r\n"
            self.header_block = (
                f"Content-Type: {self.content_type}; charset={self.encoding}\r\n"
                f"Content-Length: {body_len}\r\n"
                "\r\n"
            )
            return self.__encode_and_combine_response()
        else:
            raise Exception("Status code not found")
        


