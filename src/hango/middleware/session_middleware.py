from hango.custom_http import Request, Response, set_cookie
from hango.session import SessionStore, LazySession
from hango.utils import is_coroutine  



def make_session_middleware(session_store: SessionStore):
    def session_middleware(handler: callable):
        async def wrapped(request: Request) -> Response:
            cookies = request.headers.cookie or {}
            session_id = cookies.get("session_id")

            data = session_store.get_session(session_id) if session_id else None

            request.session = LazySession(session_store, session_id, data)

            response: Response = await is_coroutine(handler=handler, request=request)

            if request.session.is_modified and response.disable_default_cookie:
                assert request.session.session_id is not None
                session_store.set_session(request.session.session_id, request.session.data)
                set_cookie(
                    response,
                    "session_id",
                    request.session.session_id,
                    http_only=True,
                    secure=True,
                    samesite="Lax",
                    path="/",
                    max_age=86400,
                )
            return response
        return wrapped
    return session_middleware
