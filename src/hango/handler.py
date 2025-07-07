from hango.response   import CustomResponse
from hango.type_safe  import type_safe
from hango import server

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