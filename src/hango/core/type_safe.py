import inspect
import typing
from functools import wraps
import asyncio
from hango.core import DEV
def type_safe(func):
    if DEV == False:
        return func
    # strips the metadata from func typw annotations, and put them in a dict/map
    types_map = typing.get_type_hints(func)
    # returns Signature object that contains the provides the structure for matching actual call args to those annotated args
    actul_types   = inspect.signature(func)
    if asyncio.iscoroutinefunction(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            boundArgument = actul_types.bind_partial(*args, **kwargs)
            for name, val in boundArgument.arguments.items():
                expected = types_map.get(name)
                if expected and not isinstance(val, expected):
                    raise TypeError(
                        f"{func.__name__}() -> args '{name}' expected {expected.__name__}, received {type(val).__name__}"
                    )
            result = await func(*boundArgument.args, **boundArgument.kwargs)
            return_types = types_map.get("return")
            if return_types and not isinstance(result, return_types):
                raise TypeError(
                    f"{func.__name__}() -> return expected {return_types.__name__}, but returned {type(result).__name__}"
                )
            return result
        return async_wrapper
    else:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # returns BoundArguments (map of args to func's parameter) or returns TypeError if the args are not matching what signature.
            boundArgument = actul_types.bind_partial(*args, **kwargs)
            # in each argument (the dict/map that map the val to args name), we get the args from the type_map above. 
            for name, val in boundArgument.arguments.items():
                # get the args name from the types_map
                expected = types_map.get(name)
                # if we found the value mapped by the types_map, and if the actual val from ba is not matching what we erxpected in isinstance, then raise the typeError.
                if expected and not isinstance(val, expected):
                    raise TypeError(
                        f"{func.__name__}() -> args '{name}' expected {expected.__name__}, received {type(val).__name__}"
                    )
            # call the actual func with the checked args
            result = func(*boundArgument.args, **boundArgument.kwargs)
            # get the return type annotations from the types_map
            return_types = types_map.get("return")
            if return_types and not isinstance(result, return_types):
                raise TypeError(
                    f"{func.__name__}() -> return expected {return_types.__name__}, but returned {type(result).__name__}"
                )
            return result
        return wrapper