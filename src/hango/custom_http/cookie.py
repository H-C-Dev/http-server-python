from http import cookies
from .response import Response

def parse_cookie(raw_cookie_part: str) -> dict[str, str]:
    if not raw_cookie_part:
        return {}
    cookie_part = merge_cookie_part(raw_cookie_part)
    cookie = cookies.SimpleCookie()
    cookie.load(cookie_part or "")
    parsed_cookie = {k: v.value for k, v in cookie.items()}
    if "session_id" not in parsed_cookie:
        parsed_cookie["session_id"] = ""
    return parsed_cookie

def merge_cookie_part(raw_cookie_part: str) -> dict:
    return "; ".join(raw_cookie_part)

def set_cookie(response: Response, name: str, value: any, *, 
               http_only: bool =True,
               secure: bool =True,
               samesite: str="Lax",
               path: str="/",
               max_age: int | None=None):
    
    if samesite and samesite.lower() == "none":
        secure = True

    cookie = cookies.SimpleCookie()
    cookie[name] = value
    morsel = cookie[name]
    morsel["path"] = path
    if max_age is not None:
        morsel["max-age"] = str(max_age)
    if http_only:
        morsel["httponly"] = http_only
    if secure:
        morsel["secure"] = secure
    if samesite:
        morsel["samesite"] = samesite

    if response.set_cookie == None:
        response.set_cookie = cookie.output(header="").strip()
    else:
        response.set_cookie += cookie.output(header="").strip()

    return response
