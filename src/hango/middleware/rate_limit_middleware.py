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

    def _allow(self, request: Request) -> bool:
        current_time = time.monotonic()
        client_ip = self.get_client_ip(request)
        queue = self.store[client_ip]
        while queue and (current_time - queue[0] > self.period):
            queue.popleft()
        if len(queue) >= self.max_requests_number:
            return False
        queue.append(current_time)
        return True

    async def rate_limit_handler(self, request: Request, handler: callable):
        if self._allow(request):
            response = await is_coroutine(handler, request)
            return response
        else:
            return Response(status_code="429", body=f"Too many Requests.")

def make_rate_limit_middleware(rate_limiter: RateLimiter):
    def rate_limit_middleware(handler: callable):
        async def wrapped(request: Request) -> Response:
            response: Response = await rate_limiter.rate_limit_handler(request, handler)
            return response
        return wrapped
    return rate_limit_middleware







