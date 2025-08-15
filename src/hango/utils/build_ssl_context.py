import ssl
from hango.core import CERT_FILE, KEY_FILE

def build_ssl_context(is_server: bool) -> ssl.SSLContext:
    if is_server:
        if not CERT_FILE or not KEY_FILE:
                 raise FileNotFoundError("SSL CERT or KEY FILE is not found. Or disable HTTPS to continue.")
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(certfile=CERT_FILE, keyfile=KEY_FILE)
    else:
        context = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    return context
