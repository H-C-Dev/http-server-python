from hango.http   import Response
from hango.utils  import type_safe
from hango.server import server
import asyncio


@server.set_global_middlewares
def foo_middleware(handler):
    async def wrapped(request):
        print("[Middleware] mw says hello to handler for:", request)
        response = handler(request)
        if asyncio.iscoroutine(response):
             response = await response
        # print("[Middleware] mw says bye to handler response:", response)
        return response
    return wrapped


def local_middleware(handler):
    async def wrapped(request):
        print("[LOCAL Middleware] mw says hello to handler for:", request)
        response = handler(request)
        if asyncio.iscoroutine(response):
             response = await response
        return response
    return wrapped


@server.GET("/favicon.ico")
def catch_favicon(request) -> Response:
    return Response(body="a favicon is detected", status_code="200")

@server.GET("/test", local_middlewares=[local_middleware])
@type_safe
def return_hello_world(request) -> Response:
    return Response(body="hello world", status_code="200")

@server.GET("/data/{client_data}")
@type_safe
def return_client_data(request) -> Response:
    res = test_safe("hello")
    print("data received from client:", request.params)
    print(res)
    return Response(body=request.params, status_code="200")

@server.POST("/post")
@type_safe
def post_endpoint(request) -> Response:
    print("[Data received from client]:", request.body)
    return Response(body="hello world from post endpoint", status_code="200")

@type_safe
def test_safe(foo: str) -> str:
    return foo

@server.GET("/async-test")
@type_safe
async def async_test_handler(request) -> Response:
    await asyncio.sleep(1)  
    return Response(body="this is from async function", status_code="200")


@server.set_hook_after_each_handler
def log_response(request, response):
    print('[HOOK RESPONSE]:',response)

@server.set_hook_before_each_handler
def log_request(request):
    print('[HOOK REQUEST]', request)



