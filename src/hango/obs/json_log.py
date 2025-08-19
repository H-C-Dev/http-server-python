import json, sys, time
from hango.utils import redact, milliseconds, request_id
from hango.custom_http import Request, Response
SLOW_THRESHOLD = 0.0


def _json_dumps_safe(obj):
    if isinstance(obj, (set, frozenset)):
        return list(obj)
    if isinstance(obj, (bytes, bytearray)):
        return obj.decode("utf-8", errors="replace")
    return str(obj)

def log(event: str, **fields):
    if "headers" in fields: fields["headers"] = redact(fields["headers"])
    if "body" in fields: fields["body"] = redact(fields["body"])
    record = {"ts": milliseconds(), "event": event, **fields}
    sys.stdout.write(json.dumps(record, separators=(",", ":"), default=_json_dumps_safe) + "\n")
    sys.stdout.flush()

def start_request(request: Request):
    log("[INCOMING REQUEST]", request_id=request_id(), method=getattr(request, "method", ""), path=getattr(request, "path", ""), version=getattr(request, "version", ""))
    request.start_time = time.monotonic()
    request.request_id = request_id()

def slow_request(request: Request):
    log("[SLOW REQUEST]", request_id=request.request_id)

def end_request(response: Response, request: Request, SLOW_THRESHOLD: float):
    response.response_id = request.request_id
    log("[RETURNING RESPONSE]", response_id=response.response_id, status_code=getattr(response, "status_code", ""), body=getattr(response, "body", ""), cors_header=getattr(response, "cors_header", "")) 
    duration = time.monotonic() - request.start_time
    response.duration = duration
    if duration > SLOW_THRESHOLD:
        slow_request(request=request)

def end_error_request(response: Response, e: Exception): 
    log("[RETURNING ERROR RESPONSE]", request_id=request_id(), status_code=getattr(response, "status_code", ""), body=getattr(response, "body", ""), cors_header=getattr(response, "cors_header", ""), error=str(e))
