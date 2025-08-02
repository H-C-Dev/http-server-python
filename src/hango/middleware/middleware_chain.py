import asyncio
from .cors import cors_middleware


DEFAULT_MIDDLEWARES = [cors_middleware]

class MiddlewareChain:
    def __init__(self):
        self.global_middlewares = []
        self._hook_before_each_handler = []
        self._hook_after_each_handler = []
    

    def add_hook_before_each_handler(self, func):
        self._hook_before_each_handler.append(func)
        return func
    
    def add_hook_after_each_handler(self, func):
        self._hook_after_each_handler.append(func)
        return func

    def add_middleware(self, middleware):
        self.global_middlewares.append(middleware)

    
    def add_default_middlewares(self):
        for middleware in DEFAULT_MIDDLEWARES:
            self.global_middlewares.append(middleware)

    def wrap_handler(self, handler, local_middlewares, request, cache_middlewares, cache):

        for hook in self._hook_before_each_handler:
            hook(request)

        self.add_default_middlewares()

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
