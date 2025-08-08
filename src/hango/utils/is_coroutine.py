import asyncio

async def is_coroutine(handler, request):
    response = handler(request)
    if asyncio.iscoroutine(response):
        response = await response
    return response 
