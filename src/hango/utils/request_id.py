import uuid 

def request_id(existing: str | None = None): return existing or str(uuid.uuid4())