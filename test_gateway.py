"""
Unit tests for the production-grade LLM gateway layer.

Fully offline — no API keys or network required. Exercises the resiliency
machinery directly: circuit breakers, BYOK key management + rotation, rate
limiting, and the router's retry/failover logic.

Run:  uv run python test_gateway.py   (expect 9/9 passed)
"""

import sys
import time

from src.gateway.circuit import CircuitBreaker
from src.gateway.keys import KeyManager, hash_virtual_key
from src.gateway.ratelimit import RateLimiter
from src.gateway.router import Gateway, Route, QuotaExceeded, AllRoutesFailed
from src.gateway.providers import ProviderResult, ProviderHTTPError, ProviderTimeoutError


class FakeProvider:
    """Configurable provider for simulating success / failures / timeouts."""

    def __init__(self, name, fail=0, retriable=True, status=503, timeout=False):
        self.name = name
        self.api_keys = ["k1", "k2"]
        self._fail = fail
        self._retriable = retriable
        self._status = status
        self._timeout = timeout
        self.calls = 0

    def complete(self, messages, model="", temperature=0.3, max_tokens=None, api_key=None):
        self.calls += 1
        if self._timeout:
            raise ProviderTimeoutError("simulated timeout")
        if self._fail:
            self._fail -= 1
            raise ProviderHTTPError(self._status, "boom", self._retriable)
        return ProviderResult(text="OK", prompt_tokens=10, completion_tokens=5,
                              model=model, latency_s=0.01)


def make_gateway(providers, **gw):
    g = Gateway(max_attempts=gw.pop("max_attempts", 2), retry_base_s=0.01,
                retry_cap_s=0.05, **gw)
    for i, p in enumerate(providers):
        g.register(Route(provider=p, model="m", tier="t", priority=i + 1,
                         name=f"{p.name}/m"))
    return g


# ---- 1. Circuit breaker lifecycle ---------------------------------------
def test_circuit():
    cb = CircuitBreaker("x", failure_threshold=3, cooldown_s=0.1, half_open_max=1)
    assert cb.state == "CLOSED"
    for _ in range(3):
        cb.on_failure(True)
    assert cb.state == "OPEN"
    assert cb.allow_request() is False          # fast-fail while open
    time.sleep(0.15)
    assert cb.allow_request() is True           # cooldown -> half-open probe
    cb.on_success()
    assert cb.state == "CLOSED"                 # success closes
    print("1/9 circuit lifecycle OK")

# ---- 2. BYOK key management + rotation ----------------------------------
def test_virtual_key_hashing():
    km = KeyManager()
    vk = km.mint_virtual_key("acme", budget_usd=5.0)
    assert vk.startswith("xa_")
    assert hash_virtual_key(vk) != vk            # never store plaintext
    t = km.resolve_virtual_key(vk)
    assert t is not None and t.tenant_id == "acme"
    assert km.resolve_virtual_key("x_bad_key") is None
    print("3/9 virtual key: hashed, resolved, rejected OK")


def test_budget_enforcement():
    g = make_gateway([FakeProvider("p")])
    vk = g.km.mint_virtual_key("acme", budget_usd=1.0)
    g.km.tenant("acme").spent_usd = 2.0          # already over budget
    try:
        g.complete([{"role": "user", "content": "x"}], model="t", virtual_key=vk)
        raise AssertionError("budget not enforced")
    except QuotaExceeded:
        print("4/9 BYOK budget enforcement OK")


def test_provider_key_rotation():
    km = KeyManager(rotating_grace_s=200.0)
    km.register_provider_key("groq", "old-key", ttl_s=60)
    # Simulate a key that expired 60s ago, still inside a 200s grace window.
    km._provider_keys["groq"][0].created_at = time.time() - 60 - 60
    rotated = []
    km.set_rotate_callback("groq", lambda prov, old: rotated.append(prov) or "new-key")
    usable = km.usable_provider_keys("groq")
    assert usable and usable[0].key == "new-key", usable
    assert rotated and rotated[0] == "groq"
    print("5/9 provider key rotation (TTL + grace + callback) OK")


# ---- 3. Rate limiting ---------------------------------------------------
def test_ratelimit():
    rl = RateLimiter(default_rpm=3, default_tpm=10_000)
    assert all(rl.acquire("t", "m") for _ in range(3))
    assert not rl.acquire("t", "m")              # 4th request within the minute denied
    assert rl.acquire("other", "m")              # different tenant unaffected
    rl.enter_parallel(); rl.exit_parallel()
    print("6/9 rate limiting (RPM + tenant isolation) OK")


def test_circuit_ignores_non_retriable():
    cb = CircuitBreaker("x", failure_threshold=3, cooldown_s=100, half_open_max=1)
    for _ in range(10):
        cb.on_failure(False)                    # client errors must NOT trip
    assert cb.state == "CLOSED"
    print("2/9 circuit ignores non-retriable OK")


# ---- 4. Router: retry / failover ----------------------------------------
def test_retry_then_success():
    f1, f2 = FakeProvider("a", fail=1), FakeProvider("b")
    g = make_gateway([f1, f2])
    res = g.complete([{"role": "user", "content": "hi"}], model="t")
    assert res.text == "OK" and f1.calls == 2 and f2.calls == 0
    print("7/9 retry-then-success (no unnecessary failover) OK")


def test_failover_and_timeout():
    g = make_gateway([FakeProvider("a", fail=999), FakeProvider("b")])
    res = g.complete([{"role": "user", "content": "x"}], model="t")
    assert res.text == "OK"
    g2 = make_gateway([FakeProvider("t", timeout=True), FakeProvider("o")])
    res2 = g2.complete([{"role": "user", "content": "x"}], model="t")
    assert res2.text == "OK"
    print("8/9 failover (persistent error + timeout) OK")


def test_all_routes_fail():
    g = make_gateway([FakeProvider("z", fail=999)], max_attempts=1)
    try:
        g.complete([{"role": "user", "content": "x"}], model="t")
        raise AssertionError("should have failed")
    except AllRoutesFailed:
        print("9/9 all-routes-failed raises OK")


TESTS = [
    test_circuit,
    test_circuit_ignores_non_retriable,
    test_virtual_key_hashing,
    test_budget_enforcement,
    test_provider_key_rotation,
    test_ratelimit,
    test_retry_then_success,
    test_failover_and_timeout,
    test_all_routes_fail,
]


if __name__ == "__main__":
    passed = 0
    for t in TESTS:
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"FAIL: {t.__name__} -> {e}")
    print(f"\n{passed}/{len(TESTS)} tests passed")
    sys.exit(0 if passed == len(TESTS) else 1)
    print("2/9 circuit ignores non-retriable OK")