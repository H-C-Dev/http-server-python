import asyncio
from .cors import cors_middleware
from .obs_middleware import make_obervabilty_middleware
from .session_middleware import make_session_middleware
from hango.session import SessionStore

DEFAULT_MIDDLEWARES = [cors_middleware, make_obervabilty_middleware]

class MiddlewareChain:
    def __init__(self, session_store: SessionStore=None):
        self.global_middlewares = []
        self._hook_before_each_handler = []
        self._hook_after_each_handler = []
        self.session_store = session_store
        self._defaults_added = False
    

    def add_hook_before_each_handler(self, func):
        self._hook_before_each_handler.append(func)
        return func
    
    def add_hook_after_each_handler(self, func):
        self._hook_after_each_handler.append(func)
        return func

    def add_middleware(self, middleware):
        self.global_middlewares.append(middleware)

    
    def add_default_middlewares(self):
        if self._defaults_added:       
            return
        for middleware in DEFAULT_MIDDLEWARES:
            self.global_middlewares.append(middleware)
        self.global_middlewares.append(make_session_middleware(self.session_store))

        print(self.global_middlewares)
        self._defaults_added = True

    def wrap_handler(self, handler, local_middlewares, request, cache_middlewares, cache):

        for hook in self._hook_before_each_handler:
            hook(request)



        wrapped = handler

        for global_middleware in self.global_middlewares:
            wrapped = global_middleware(wrapped)
        
        for cache_middleware in cache_middlewares:
            wrapped = cache_middleware(wrapped, cache)

        for local_middleware in local_middlewares:
            wrapped = local_middleware(wrapped)
        return wrapped
    
    async def wrap_response(self, request, formatted_response):
        for hook in self._hook_after_each_handler:
            result = hook(request, formatted_response)
            if asyncio.iscoroutine(result):
                await result
            return result
