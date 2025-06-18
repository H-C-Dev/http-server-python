from server import Server
from response import CustomResponse
from handler import return_hello_world, return_client_data, post_endpoint
def main():
    server = Server("0.0.0.0", 8080)
    def catch_favicon():
        return CustomResponse(body="a favicon is detected", status_code=200)
    server.GET("/favicon.ico", catch_favicon)
    server.GET("/test", return_hello_world)
    server.GET("/data/{client_data}", return_client_data)
    server.POST("/post", post_endpoint)
    server.start_server()

    
    
main()