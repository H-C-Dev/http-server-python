
from hango.custom_http import Forbidden
import asyncio
from hango.utils import is_cors_allowed

def cors_middleware(handler):
    async def wrapped(request):
        user_agent = request.headers.user_agent.lower()
        origin = request.headers.origin
        is_localhost = request.is_localhost
        cors_header = None
        
        if is_localhost and 'mozilla' not in user_agent or 'chrome' not in user_agent or 'safari' not in user_agent:
                pass
        elif 'mozilla' in user_agent or 'chrome' in user_agent or 'safari' in user_agent: 
            if is_cors_allowed(origin) != None:
                cors_header = is_cors_allowed(origin)
            else:
                raise Forbidden(message=f"Host {origin} is not allowed to access this resource. CORS policy is validated.")
        response = handler(request)
        if asyncio.iscoroutine(response):
             response = await response
        response.cors_header = cors_header
        return response
    return wrapped