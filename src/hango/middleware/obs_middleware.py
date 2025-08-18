from hango.custom_http import Request, Response
from hango.utils import is_coroutine
from hango.obs import start_request, end_request, inc_request, observe_latency
def make_obervabilty_middleware(SLOW_THRESHOLD: int = 500):
    def obervability_middleware(handler):
        async def wrapped(request: Request):
            start_request(request)

            response: Response = await is_coroutine(handler, request)

            end_request(request=request, response=response, SLOW_THRESHOLD=SLOW_THRESHOLD)
            inc_request(request.method, request.path, response.status_code)
            observe_latency(request.method, request.path, response.duration)

            return response
        return wrapped
    return obervability_middleware



            
                



            


    