from typing import TYPE_CHECKING

if TYPE_CHECKING:  
    from hango.custom_http import Response
import json
from hango.utils import is_coroutine

class CacheHelper:
    
    def __init__(self, cache):
        self.cache = cache

    def _set_cache_key(self, query: dict, path: str, method: str) -> str:
        # if len(query.keys()) > 0 and method == 'GET':
        if method == 'GET':
            cache_key = method + ":" + path
            if len(query.keys()) > 0:
                cache_key += "?"
                for k in query:
                    for v in query[k]:
                        cache_key += f"{k}={v}&"
                cache_key = cache_key[:-1]
            return cache_key
        return None

    def _handle_cache_hitted(self, raw):
        print('cache hitted')
        payload = json.loads(raw)
        response = Response(                
        status_code=payload["status_code"],
        content_type=payload.get("content_type"),
        body=payload.get("body")
        )
        response.cors_header = payload.get("cors_header")
        return response

    async def _handle_cache_creating(self, handler, request, cache_key, TTL):
        response = await is_coroutine(handler, request)
        print("Cache creating")
        to_cache = {
            "status_code": response.status_code,
            "content_type": response.content_type,
            "body": response.body,
            "cors_header": response.cors_header,
        }
        await self.cache.set(cache_key, json.dumps(to_cache), ex=TTL)
        print("cache created")
        return response

    async def _handle_cache_response(self, handler, request, cache_key, TTL):
        raw = await self.cache.get(cache_key)
        if raw:
            response = self._handle_cache_hitted(raw)
        else:
            response = await self._handle_cache_creating(handler, request, cache_key, TTL)
        return response


    
    async def handle_cache(self, request, handler, TTL: int):
        cache_key = self._set_cache_key(request.query, request.path, request.method)

        if cache_key == None:
            print("Error ocurred during setting cache") 
            response = await is_coroutine(handler, request)
        else:
            response = await self._handle_cache_response(handler, request, cache_key, TTL)
        return response