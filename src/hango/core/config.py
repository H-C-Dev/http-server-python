import os

SERVER_ROOT = os.path.dirname(os.path.abspath(__file__))
STATIC_ROOT = os.path.join(SERVER_ROOT, "static")
PORT=8080
HOST="0.0.0.0"
REDIS_HOST="localhost"
REDIS_PORT=6379
ENABLE_HTTPS=False
DEV=True
CERT_FILE = "server.crt"
KEY_FILE = "server.key"
SLOW_THRESHOLD = 0.001