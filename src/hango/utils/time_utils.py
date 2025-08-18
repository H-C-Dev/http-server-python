from email.utils import formatdate

import time
def response_time() -> str:
    return formatdate(timeval=None, localtime=False, usegmt=True)

def milliseconds(): return int(time.time() * 1000)