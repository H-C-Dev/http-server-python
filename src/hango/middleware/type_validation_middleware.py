from hango.custom_http import Response, Request

class Validator:
    def __init__(self, schema: dict[str, type], source="query"):
        self.schema = schema
        self.source = source

    def validate(self, request: Request) -> tuple[bool, dict]:
        data = getattr(request, self.source, {}) or {}

        extra_fields = set(data.keys()) - set(self.schema.keys())
        if extra_fields:
            return False, {
                "fields": list(extra_fields),
                "message": f"Unexpected fields: {', '.join(extra_fields)}. See API docs.",
            }

        for k, v in self.schema.items():
            if k not in data:
                return False, { 
                    "field": k,                    
                    "message": f"Required field '{k}' is missing. See API docs.",
                }

            value = data[k]  

            if not isinstance(value, v):
                return False, {  
                    "field": k,                    
                    "message": f"Field '{k}' must be {v.__name__}. See API docs.",
                }

        # shallow copy to avoid the mutation risk
        return True, dict(data)

def make_validate_middleware(validators: list[Validator]):
    def validate_middleware(handler):
        async def wrapped(request):
            for validator in validators:
                validated, result = validator.validate(request)  
                if not validated:
                    return Response(
                        status_code=400,
                        body={
                            "error": "validation_failed",  
                            "details": result,             
                        }
                    )
                setattr(request, validator.source, result)  
            return await handler(request)
        return wrapped
    return validate_middleware