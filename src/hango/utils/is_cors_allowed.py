from hango.core import CORS

def is_cors_allowed(host: str) -> str | None:
    cors_header = None
    if '*' in CORS:
        cors_header = "*"
    elif 'http://' + host in CORS: 
        cors_header = 'http://' + host
    elif 'https://' + host in CORS:
        cors_header = 'https://' + host
    return cors_header