from hango.http import Response
import asyncio

def _set_cache_query(query: dict, path: str, method: str) -> str:
    # if len(query.keys()) > 0 and method == 'GET':
    if method == 'GET':
        cache_query = method + ":" + f"{path}?" 
        if len(query.keys()) > 0:
            for k in query:
                for v in query[k]:
                    cache_query += f"{k}={v}&"
            cache_query = cache_query[:-1]
        return cache_query
    return None

TTL = 3600

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
            cached = await cache.get(cache_query)
            if cached:
                print("Cache hitted")
                return Response(body=cached, status_code="200")
            else:
                response = handler(request)
                if asyncio.iscoroutine(response):
                    response = await response
                print("Cache creating")
                await cache.set(cache_query, response.body, ex=TTL)
                print("cache created")
                return response
    return wrapped




