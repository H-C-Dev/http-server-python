import time
from collections import deque, defaultdict
from hango.custom_http import Request, Response
from hango.utils import is_coroutine
class RateLimiter:
    def __init__(self,  max_requests_number=60, period=60, client_ip=None):
        self.max_requests_number = max_requests_number
        self.period = period
        self.get_client_ip = client_ip or (lambda request: getattr(request.headers, "host", "unknown"))
        self.store: dict[str, deque[float]]= defaultdict(deque)

    def allow(self, request: Request) -> bool:
        current_time = time.monotonic()
        client_ip = self.get_client_ip(request)
        queue = deque[client_ip]
        while current_time - queue[0]:
            deque.popleft()
        if len(queue) >= self.max_request_number:
            return True
        
        return False
    

def make_rate_limit_middleware(config: dict[str, int]):
    def rate_limit_middleware(handler: callable):
        async def wrapped(request: Request) -> Response:
            max_number = config.max_requests_number
            period = config.period
            rate_limiter = RateLimiter(max_requests_number=max_number, period=period)
            if rate_limiter.allow(request):
                response = await is_coroutine(handler, request)
                return response
            else:
                return Response(status_code="429", body=f"Too many Requests.")
        return wrapped
    return rate_limit_middleware







