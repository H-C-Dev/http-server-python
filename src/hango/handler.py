from hango.http   import CustomResponse
from hango.utils  import type_safe
from hango.server import server
import asyncio

@server.GET("/favicon.ico")
@type_safe
def catch_favicon() -> CustomResponse:
    return CustomResponse(body="a favicon is detected", status_code="200")

@server.GET("/test")
@type_safe
def return_hello_world() -> CustomResponse:
    return CustomResponse(body="hello world", status_code="200")

@server.GET("/data/{client_data}")
@type_safe
def return_client_data(client_data: dict) -> CustomResponse:
    res = test_safe("hello")
    print(res)
    return CustomResponse(body=client_data, status_code="200")

@server.POST("/post")
@type_safe
def post_endpoint(post_data: str) -> CustomResponse:
    print("data received from client:", post_data)
    return CustomResponse(body="hello world from post endpoint", status_code="200")

@type_safe
def test_safe(foo: str) -> str:
    return foo

@server.GET("/async-test")
@type_safe
async def async_test_handler() -> CustomResponse:
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
