from enum import Enum

http_status_codes_message = {
    200: "OK", 
    400: "Bad Request", 
    404: "Not Found",
    405: "Method Not Allowed", 
    500: "Internal Server Error"
}

class MethodType(Enum):
    GET = "GET"
    POST = "POST"

class ContentType(Enum):
    JSON = "application/json"
    PLAIN = "text/plain"
