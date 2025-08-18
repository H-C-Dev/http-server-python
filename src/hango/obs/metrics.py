from collections import defaultdict

counters = defaultdict(int)
BUCKETS_MS = [50,100,200,500,1000,2000,5000,10000]

def inc_request(method: str, route: str, status: int):
    counters[("requests_total", method, route, str(status))] += 1

def observe_latency(method: str, route: str, ms: int):
    placed = False
    for b in BUCKETS_MS:
        if ms <= b:
            counters[("request_duration_ms_bucket", method, route, f"le_{b}")] += 1
            placed = True
            break
    if not placed:
        counters[("request_duration_ms_bucket", method, route, "gt_10000")] += 1

def snapshot():
    return {"/".join(k): v for k, v in counters.items()}
