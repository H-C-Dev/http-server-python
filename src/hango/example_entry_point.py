from hango.server import create_app

app = create_app()
from hango.examples.handler import *

if __name__ == "__main__":
    app.start_server()
