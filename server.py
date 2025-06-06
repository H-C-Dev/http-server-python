import socket
PORT=8080
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((socket.gethostname(), PORT))
s.listen(5)

print(f"Listening on port: {PORT}")

while True:
    (client_socket, client_address) = s.accept()
    print(f"Got a connection from {client_address}")
    request = client_socket.recv(4096).decode('utf-8')
    print(request)
    response = (
        "HTTP/1.1 200 OK\r\n"
        "Content-Type: text/plain; charset=utf-8\r\n"
        "Content-Length: 37\r\n"
        "\r\n"
        "This is a test for HTTP/1.1 Response!"
    )
    client_socket.sendall(response.encode('utf-8'))
    client_socket.close()
