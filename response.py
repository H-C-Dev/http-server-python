from constants import http_status_codes_message

class CustomResponse:
    def __init__(self, message: str, contentType, statusCode, encoding: str = 'utf-8'):
        self.statusCode = statusCode
        self.encoding = encoding
        self.contentType = contentType
        self.message = message
        self.statusLine = None
        self.val = None

    def construct_response(self) -> bytes:
        if self.statusCode in http_status_codes_message:
            self.statusLine = f"HTTP/1.1 {self.statusCode} {http_status_codes_message[self.statusCode]}\r\n"
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

