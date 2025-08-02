from hango.server import app

server = app(cache='redis')
from hango.examples.handler import *

if __name__ == "__main__":
    server.start_server()
