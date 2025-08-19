import json
from .server import server
from hango.custom_http import Response, Request, HttpClient, NotFound, BadRequest, InternalServerError
import os
from .sns import send_email
from hango.utils import env_loader
env_loader()
from .db import get_schedules, add_schedule
import asyncio
import time
from hango.obs import log
from hango.middleware import make_validate_middleware, Validator
from hango.middleware import  CacheHelper, make_rate_limit_middleware, RateLimiter
from hango.core import type_safe

STARLING_PAT = os.environ["STARLING_PAT"]
STARLING_PAT = f"Bearer {STARLING_PAT}"
GET_ACC_ID_API = "https://api.starlingbank.com/api/v2/accounts"
GET_ACC_BALANCE =  lambda account_id: f"https://api.starlingbank.com/api/v2/accounts/{account_id}/balance"

async def get_account_id(request_id: str | None = None) -> str:
    _, _, body = await client.request("GET", GET_ACC_ID_API, authorization=STARLING_PAT,request_id=request_id)
    body = json.loads(body)
    if not body['accounts'][0]['accountUid']:
        raise NotFound("Account Not Found")
    
    account_id = body['accounts'][0]['accountUid']

    return account_id

@type_safe
async def get_balance_starling(account_id: str, request_id: str | None = None) -> str:
    _, _, body = await client.request("GET", GET_ACC_BALANCE(account_id=account_id), authorization=STARLING_PAT,request_id=request_id)

    body = json.loads(body)
    if body['effectiveBalance']['minorUnits'] == None:
        raise NotFound("Balance Not Found")

    balance = body['effectiveBalance']['minorUnits']
    return f'£{balance}'

async def send_balance_email():
    try:
        print("sending email")
        now = time.monotonic()
        account_id = await get_account_id(f'Server-Schdule-request {now}')
        balance = await get_balance_starling(account_id, now)
        response = send_email(balance)
        log("Email Sent", status=response)
    except Exception as e:
        log("Email Failed", error=str(e))
        raise



@server.GET("/test")
def test(request: Request) -> Response:
    return Response(body="Test", status_code="200")

client = HttpClient(user_agent="test")

def cache_middleware(handler, cache):
    async def wrapped(request):
        cache_helper = CacheHelper(cache)
        response = await cache_helper.handle_cache(request, handler, 10)
        return response
    return wrapped

balance_rl = make_rate_limit_middleware(RateLimiter(max_requests_number=1, period=10))
@server.GET("/balance", cache_middlewares=[cache_middleware], local_middlewares=[balance_rl])
async def get_balance(request: Request) -> Response:
    account_id = await get_account_id(request_id=request.request_id)
    balance = await get_balance_starling(account_id=account_id, request_id=request.request_id)
    return Response(status_code="200", body=balance)

@server.GET("/schedule")
async def get_schedule(request: Request) -> Response:
    schedules = get_schedules()[0]
    return Response(status_code="200", body=str(schedules[2]))

modify_tv = make_validate_middleware([Validator(schema={"schedule": int}, source="body")])

@server.POST("/modify", local_middlewares=[modify_tv])
async def modify_schedule(request: Request) -> Response:
    val = request.body["schedule"]
    add_schedule("daily_balance", val)
    schedules = get_schedules()[0]
    return Response(status_code="200", body=str(schedules[2]))

@server.set_global_middlewares
def foo_middleware(handler):
    async def wrapped(request):
        print("[Middleware] mw says hello to handler for:", request)
        response: Response = handler(request)
        if asyncio.iscoroutine(response):
             response = await response
        response.set_headers()
        print(response.headers.return_response_headers())
        print("[Middleware] mw says bye to handler response:", response)
        return response
    return wrapped