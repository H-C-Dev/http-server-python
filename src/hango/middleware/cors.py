from hango.core import CORS
from hango.http import Forbidden
import asyncio

def cors_middleware(handler):
    async def wrapped(request):
        user_agent = request.headers.user_agent.lower()
        host = request.headers.host
        is_localhost = request.is_localhost
        cors_header = None
        if 'mozilla' in user_agent or 'chrome' in user_agent or 'safari' in user_agent: 
            if is_localhost:
                pass
            elif '*' in CORS:
                cors_header = "*"
            elif 'http://' + host in CORS: 
                cors_header = 'http://' + host
            elif 'https://' + host in CORS:
                cors_header = 'https://' + host
            else:
                raise Forbidden(message=f"Host {host} is not allowed to access this resource. CORS policy is validated.")
        response = handler(request)
        if asyncio.iscoroutine(response):
             response = await response
        response.cors_header = cors_header
        return response
    return wrapped