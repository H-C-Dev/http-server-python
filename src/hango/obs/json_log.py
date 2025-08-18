import json, sys
from hango.utils import redact, milliseconds

def log(event: str, **fields):
    if "headers" in fields: fields["headers"] = redact(fields["headers"])
    if "body" in fields: fields["body"] = redact(fields["body"])
    record = {"ts": milliseconds(), "event": event, **fields}
    sys.stdout.write(json.dumps(record, separators=(",", ":")) + "\n")
    sys.stdout.flush()
