class HTTPError(Exception):
    def __init__(self, status_code: int, message: str = None):
        self.status_code = status_code
        self.message = message or f"{status_code} Error"
        super().__init__(self.message)

class BadRequest(HTTPError):
    def __init__(self, message: str = "Bad Request"):
        super().__init__(400, message)

class Unauthorized(HTTPError):
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(401, message)

class PaymentRequired(HTTPError):
    def __init__(self, message: str = "Payment Required"):
        super().__init__(402, message)

class Forbidden(HTTPError):
    def __init__(self, message: str = "Forbidden"):
        super().__init__(403, message)    

class NotFound(HTTPError):
    def __init__(self, message: str = "Not Found"):
        super().__init__(404, message)

class MethodNotAllowed(HTTPError):
    def __init__(self, message: str = "Method Not Allowed"):
        super().__init__(405, message)

class InternalServerError(HTTPError):
    def __init__(self, message: str = "Internal Server Error"):
        super().__init__(500, message)

class HTTPVersionNotSupported(HTTPError):
    def __init__(self, message: str = "HTTP Version Not Supported"):
        super().__init__(505, message)
        