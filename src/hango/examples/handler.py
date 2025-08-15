from hango.custom_http   import Response, Request, set_cookie, HttpClient
from hango.core  import type_safe
import asyncio
from hango.example_entry_point import server
from hango.middleware import  CacheHelper
from hango.utils import is_coroutine
from hango.middleware import make_rate_limit_middleware, RateLimiter, make_validate_middleware, Validator


@server.set_global_middlewares
def foo_middleware(handler):
    async def wrapped(request):
        print("[Middleware] mw says hello to handler for:", request)
        response: Response = handler(request)
        if asyncio.iscoroutine(response):
             response = await response
        response.set_headers()
        print(response.headers.return_response_headers())
        print("[Middleware] mw says bye to handler response:", response)
        return response
    return wrapped

def local_middleware(handler):
    async def wrapped(request):
        print("[LOCAL Middleware] mw says hello to handler for:", request)
        response = await is_coroutine(handler, request)
        return response
    return wrapped

def cache_middleware(handler, cache):
    async def wrapped(request):
        cache_helper = CacheHelper(cache)
        response = await cache_helper.handle_cache(request, handler, 3600)
        return response
    return wrapped
        
@server.GET("/use-unique-cookie")
def use_unique_cookie(request: Request) -> Response:
    request.session.set('unique_id', "unique cookie")
    response = Response(body="tested a cookie", status_code="200", disable_default_cookie=True)
    set_cookie(response, "session_id", request.session.session_id)
    return response

@server.GET("/read-unique-cookie")
def read_unique_cookie(request: Request) -> Response:
    unique_id = request.session.get("unique_id")
    if unique_id is None:
        return Response(status_code="200", body="no unique_id in session")

    return Response(status_code="200", body=f"unique_id={unique_id}")


@server.GET("/test-cookie")
def test_cookie(request: Request) -> Response:
    request.session.set('user_id', "test-cookie")
    return Response(body="tested a cookie", status_code="200")    


@server.GET("/read-cookie")
def read_cookie(request: Request) -> Response:
    user_id = request.session.get("user_id")
    if user_id is None:
        return Response(status_code="200", body="no user_id in session")

    return Response(status_code="200", body=f"user_id={user_id}")
    

@server.GET("/favicon.ico")
def catch_favicon(request) -> Response:
    return Response(body="a favicon is detected", status_code="200")



@server.GET("/test", local_middlewares=[local_middleware, make_rate_limit_middleware(RateLimiter(max_requests_number=1, period=10))], cache_middlewares=[cache_middleware])
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


@server.POST("/post", local_middlewares=[make_validate_middleware([Validator(
        schema={"hello": str}, 
        source="body")])])
@type_safe
def post_endpoint(request) -> Response:
    print("[Data received from client]:", request.body)
    print(type(request.body))
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



client = HttpClient(user_agent="HangoTest/1.0")

async def get_http_bin():
    try:
        status, headers, body = await client.request("GET", "https://httpbin.org/get", request_id="test_123")
        print("Status:", status)
        print("Headers:", headers)
        print("Body:", body.decode("utf-8"))
    except Exception as e:
        print("HTTPCLIENT")
        print("Error from HttpClient: ", e)


@server.GET("/test-http-client")
@type_safe
async def async_test_handler(request) -> Response:
    await get_http_bin()
    return Response(body="this is from async function", status_code="200")
