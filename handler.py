
def return_hello_world() -> str:
    message = "hello world"
    return message

def return_client_data(client_data: str) -> str:
    return client_data

def post_endpoint(post_data: str) -> str:
    print("data received from client: ", post_data)
    print("post endpoint has been invoked")
    return "hello world from post endpoint"