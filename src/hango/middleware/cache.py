from hango.http import Response
import asyncio

def _set_cache_query(query: dict, path: str, method: str) -> str:
    # if len(query.keys()) > 0 and method == 'GET':
    if method == 'GET':
        cache_query = method + ":" + path
        if len(query.keys()) > 0:
            cache_query += "?"
            for k in query:
                for v in query[k]:
                    cache_query += f"{k}={v}&"
            cache_query = cache_query[:-1]
        return cache_query
    return None

TTL = 3600
import json
def cache_middleware(handler, cache):
    print(cache)
    if cache is None:
        return handler
    async def wrapped(request):
        cache_query = _set_cache_query(request.query, request.path, request.method)
        if cache_query == None: 
            response = handler(request)
            if asyncio.iscoroutine(response):
                response = await response
                return response
        else:
            raw = await cache.get(cache_query)
            if raw:
                print("Cache hitted")
                payload = json.loads(raw)
                response = Response(                
                    status_code=payload["status_code"],
                    content_type=payload.get("content_type"),
                    body=payload.get("body")
                    )
                response.cors_header = payload.get("cors_header")
                return response
            else:
                response = handler(request)
                if asyncio.iscoroutine(response):
                    response = await response
                print("Cache creating")

                to_cache = {
                    "status_code": response.status_code,
                    "content_type": response.content_type,
                    "body": response.body,
                    "cors_header": response.cors_header,
                }
                
                await cache.set(cache_query, json.dumps(to_cache), ex=TTL)
                print("cache created")
                return response
    return wrapped




