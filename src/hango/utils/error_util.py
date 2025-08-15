import re, uuid, traceback
from typing import Mapping, TYPE_CHECKING, Optional
from hango.custom_http import HTTPError, InternalServerError
from hango.core import http_status_codes_message
import json
import datetime


if TYPE_CHECKING:
    from hango.custom_http import Request


SECRET_KEYS_REGEX = re.compile(r"(authorization|cookie|token|secret|password|api[-_]?key|session|bearer)", re.I)
SENSITIVE_HEADERS = {"authorization", "cookie", "x-api-key", "x-auth-token"}
MAX_LOG_FIELD_LEN = 4096  

def redact(value: any):
    if value is None:
        return None
    if isinstance(value, Mapping):
        out = {}
        for k, v in value.items():
            if isinstance(k, str) and (k.lower() in SENSITIVE_HEADERS or SECRET_KEYS_REGEX.search(k)):
                out[k] = "[REDACTED]"
            else:
                out[k] = redact(v)
        return out
    if isinstance(value, (list, tuple)):
        return type(value)(redact(x) for x in value)
    if isinstance(value, (bytes, bytearray)):
        return "[BINARY]"
    if isinstance(value, str) and len(value) > MAX_LOG_FIELD_LEN:
        return value[:MAX_LOG_FIELD_LEN] + "…"
    return value

def new_request_id() -> str:
    return str(uuid.uuid4())

def snapshot_request(request: Optional["Request"] = None) -> dict:
    try:
        headers = getattr(request, "headers", {}) or {}
        if not isinstance(headers, Mapping) and hasattr(headers, "__dict__"):
            headers = {k: v for k, v in headers.__dict__.items() if not k.startswith("_")}
    except Exception:
        headers = {}

    body = getattr(request, "body", None)
    if isinstance(body, (bytes, bytearray)):
        body = "[BINARY]"
    return {
        "method": getattr(request, "method", None),
        "path":   getattr(request, "path", None),
        "query":  redact(getattr(request, "query", None)),
        "headers": redact(headers),
        "body":   redact(body),
        "client_ip": getattr(request, "host", None),  
    }

def log_exception(err_id: str, exc: Exception, req_snapshot: dict):
    print(f"[ERROR] id={err_id} type={type(exc).__name__}")
    print(f"[ERROR] request={req_snapshot}")
    print("[ERROR] stacktrace:")
    print(traceback.format_exc())



def build_error_response(request_id: str, status_code: str):
    message = http_status_codes_message[str(status_code)]
    error_body = {
    "error": {
        "id": request_id,
        "status": status_code,
        "message": message,  
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
        }
    }
    return json.dumps(error_body), status_code


def handle_exception(exception: HTTPError | InternalServerError, request: Optional["Request"] = None) -> str:
    error_id = new_request_id()
    request_snapshot = snapshot_request(request) if request else {}
    log_exception(error_id, exception, request_snapshot)
    return error_id


    