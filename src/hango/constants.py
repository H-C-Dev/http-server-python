from enum import Enum

http_status_codes_message = {
    "200": "OK", 
    "400": "Bad Request", 
    "404": "Not Found",
    "405": "Method Not Allowed", 
    "500": "Internal Server Error",
    "505": "HTTP Version Not Supported"
}

class MethodType(Enum):
    GET = "GET"
    POST = "POST"

class ContentType(Enum):
    JSON = "application/json"
    PLAIN = "text/plain"


class EarlyHintsClient(Enum):
    FIREFOX = 'firefox'
    POSTMAN = 'postman'

EXTENSION_TO_MIME = {
    ".html": "text/html",
    ".json": "application/json",
    ".png":  "image/png",
    ".jpg":  "image/jpeg",
    ".css": "text/css",
    ".js": "application/javascript"
}


