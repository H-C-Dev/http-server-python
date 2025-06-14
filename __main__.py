from server import Server
from handler import return_hello_world, return_client_data, post_endpoint
def main():
    server = Server("0.0.0.0", 8080)
    server.GET("/test", return_hello_world)
    server.GET("/data/{client_data}", return_client_data)
    server.POST("/post", post_endpoint)
    server.start_server()

    
    
main()