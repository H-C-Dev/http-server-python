from email.utils import formatdate

def response_time() -> str:
    return formatdate(timeval=None, localtime=False, usegmt=True)