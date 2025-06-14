from response import CustomResponse

def return_hello_world() -> CustomResponse:
    message = "hello world"
    return CustomResponse(body=message, status_code=200)

def return_client_data(client_data: str) -> str:
    return CustomResponse(body=client_data, status_code=200)

def post_endpoint(post_data: str) -> str:
    print("data received from client: ", post_data)
    print("post endpoint has been invoked")
    return CustomResponse(body="hello world from post endpoint", status_code=200)