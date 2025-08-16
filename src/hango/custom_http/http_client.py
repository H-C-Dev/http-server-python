import json, random
import urllib.request, urllib.error
import asyncio
from hango.utils import build_ssl_context, redact
from functools import partial


class OutboundHTTPError(Exception):
    def __init__(self, status: int, body: str, headers: dict[str, str]):
        super().__init__(f"Outbound HTTP {status}")
        self.status = status
        self.body = body
        self.headers = headers

class HttpClient:
    def __init__(self, user_agent: str, default_timeout_s: float = 5.0, max_retries: int = 2, backoff_base: float = 0.2, backoff_cap: float = 2.0):
        self.user_agent = user_agent
        self.default_timeout_s = default_timeout_s
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self.backoff_cap = backoff_cap
        self._ssl_context = build_ssl_context(is_server=False)

    
    async def request(self, method: str, 
                      url: str, 
                      headers: dict[str, str] | None = None,
                      json_body: any = None, 
                      data: bytes | None = None, 
                      timeout_s: float | None = None, 
                      request_id: str | None = None,
                      authorization: str | None = None,
                      accept: str = "application/json"
                      ) -> tuple[int, dict[str, str], bytes]:
        method = method.upper()
        timeout_s = timeout_s or self.default_timeout_s

        headers = {
            "User-Agent": self.user_agent,
            "Accept": accept
        }
        if authorization:
            headers["Authorization"] = authorization
        if headers:
            headers.update(headers)
        

        body_bytes = None
        if json_body is not None:
            body_bytes = json.dumps(json_body).encode("utf-8")
            headers.setdefault("Content-Type", "application/json")
        elif data is not None:
            body_bytes = data
        
        idempotent = method in ("GET", "HEAD")

        attempt = 0

        while True:
            attempt += 1
            try:
                status, response_headers, response_body = await asyncio.get_running_loop().run_in_executor(None,
                                                                                                           partial(self._do_request_blocking,
                                                                                                                   method=method,
                                                                                                                   url=url,
                                                                                                                   headers=headers,
                                                                                                                   body=body_bytes,
                                                                                                                   timeout_s=timeout_s,
    ),
                                                                                                           )
                if 200 <= status < 300:
                    self._log_ok(method, url, status, headers, len(response_body), request_id)

                if idempotent and status in (429, 502, 503, 504) and attempt <= self.max_retries + 1:
                    self._log_retry(method, url, status, attempt, request_id)
                    await asyncio.sleep(self._backoff(attempt))
                    continue

                self._log_fail(method, url, status, headers, len(response_body), request_id)
                raise OutboundHTTPError(status, response_body.decode("utf-8", "replace"), response_headers)
            except urllib.error.URLError as e:
                if idempotent and attempt <= self.max_retries + 1:
                    self._log_retry(method, url, f"neterr:{getattr(e, 'reason', e)}", attempt, request_id)
                    await asyncio.sleep(self._backoff(attempt))
                    continue
                self._log_netfail(method, url, e, request_id)
                raise


    def _do_request_blocking(self, method: str, url: str, headers: dict[str, str], timeout_s: float, body: bytes | None = None) -> tuple[int, dict[str, str], bytes]:
        request = urllib.request.Request(url=url, method=method, headers=headers or {}, data=body)
        try:
            with urllib.request.urlopen(request, timeout=timeout_s, context=self._ssl_context) as response:
                status = response.getcode()
                response_headers = {k.lower(): v for k, v in response.getheaders()}
                response_body = response.read()
                return status, response_headers, response_body
        except urllib.error.HTTPError as e:
            status = e.code
            resp_headers = {k.lower(): v for k, v in (e.headers.items() if e.headers else [])}
            body = e.read() if hasattr(e, "read") else b""
            return status, resp_headers, body
    

    def _backoff(self, attempt: int) -> float:
        base = self.backoff_base * (2 ** (attempt - 1))
        return min(self.backoff_cap, base + random.uniform(0, base))
    
    def _log_ok(self, method, url, status, req_headers, body_len, req_id):
        print(f"[OUTBOUND OK] id={req_id} {method} {url} -> {status} ({body_len}B) "
              f"hdrs={redact(req_headers)}")

    def _log_retry(self, method, url, reason, attempt, req_id):
        print(f"[OUTBOUND RETRY] id={req_id} {method} {url} reason={reason} attempt={attempt}")

    def _log_fail(self, method, url, status, req_headers, body_len, req_id):
        print(f"[OUTBOUND FAIL] id={req_id} {method} {url} -> {status} ({body_len}B) "
              f"hdrs={redact(req_headers)}")

    def _log_netfail(self, method, url, exc, req_id):
        print(f"[OUTBOUND NETERR] id={req_id} {method} {url} error={exc}")