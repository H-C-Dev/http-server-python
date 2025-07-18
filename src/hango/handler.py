from hango.http   import CustomResponse
from hango.utils  import type_safe
from hango.server import server
import asyncio

@server.GET("/favicon.ico")
def catch_favicon(request) -> CustomResponse:
    return CustomResponse(body="a favicon is detected", status_code="200")

@server.GET("/test")
@type_safe
def return_hello_world(request) -> CustomResponse:
    return CustomResponse(body="hello world", status_code="200")

@server.GET("/data/{client_data}")
@type_safe
def return_client_data(request) -> CustomResponse:
    res = test_safe("hello")
    print("data received from client:", request['params'])
    print(res)
    return CustomResponse(body=request['params'], status_code="200")

@server.POST("/post")
@type_safe
def post_endpoint(request) -> CustomResponse:
    print("[Data received from client]:", request['body'])
    return CustomResponse(body="hello world from post endpoint", status_code="200")

@type_safe
def test_safe(foo: str) -> str:
    return foo

@server.GET("/async-test")
@type_safe
async def async_test_handler(request) -> CustomResponse:
    await asyncio.sleep(1)  
    return CustomResponse(body="this is from async function", status_code="200")


@server.set_hook_after_each_handler
def log_response(request, response):
    print('[HOOK RESPONSE]:',response)

@server.set_hook_before_each_handler
def log_request(request):
    print('[HOOK REQUEST]', request)


@server.set_global_middlewares
def foo_middleware(handler):
    async def wrapped(request):
        print("[Middleware] mw says hello to handler for:", request)
        response = handler(request)
        if asyncio.iscoroutine(response):
             response = await response
        print("[Middleware] mw says bye to handler response:", response)
        return response
    return wrapped
