"""
BYOK (Bring Your Own Key) key management for the LLM gateway.

Two distinct kinds of keys, like LiteLLM/Portkey:

1. **Virtual Keys** (`xa_...`) — issued to end users/tenants. They never see a
   raw provider key. We store only a SHA-256 *hash* of the virtual key (so a DB
   leak does not expose usable keys). Each virtual key maps to a tenant and
   carries a budget (USD) and daily token limit. These are what the app/agent
   authenticates with and what cost is attributed to for billing.

2. **Provider Keys** — the real upstream secrets (Groq, OpenAI, ...). They live
   in a pool per provider and are *rotated* on a TTL. Rotation follows a
   **grace period** pattern (like LiteLLM's ``_KEY_ROTATION_GRACE_PERIOD``): the
   old key stays "rotating" for a grace window so in-flight requests finish,
   while a new key is fetched from a ``rotate_callback`` (e.g. a Vault / AWS SM /
   KMS adapter in production). Provider secrets can optionally be encrypted at
   rest with ``GATEWAY_MASTER_KEY`` (AES-GCM) via the helper functions.

Everything here is stdlib-only and does not touch the network unless you supply
a ``rotate_callback``.
"""

from __future__ import annotations

import base64
import hashlib
import os
import secrets
import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


def hash_virtual_key(virtual_key: str) -> str:
    """SHA-256 hash used to store a virtual key without keeping plaintext."""
    return hashlib.sha256(virtual_key.encode("utf-8")).hexdigest()


def generate_virtual_key(prefix: str = "xa_") -> str:
    return prefix + secrets.token_urlsafe(24)


def generate_provider_key(prefix: str = "pk_") -> str:
    return prefix + secrets.token_urlsafe(24)


# ---- Optional AES-GCM encryption of provider secrets at rest ----------
def _master_key() -> Optional[bytes]:
    raw = os.getenv("GATEWAY_MASTER_KEY")
    if not raw:
        return None
    # derive 32-byte key from an arbitrary-length env secret
    return hashlib.sha256(raw.encode("utf-8")).digest()


class KeyManager:
    """In-process BYOK store. Swap internals for a real DB/secrets backend in prod."""

    def __init__(self, rotating_grace_s: float = 3600.0) -> None:
        self._lock = threading.RLock()
        self._rotating_grace_s = rotating_grace_s
        self._virtual: Dict[str, str] = {}          # hash -> tenant_id
        self._tenants: Dict[str, Tenant] = {}
        self._provider_keys: Dict[str, List[ProviderKey]] = {}
        self._rotate_callbacks: Dict[str, Callable[[str, str], str]] = {}

    # ---- virtual keys ---------------------------------------------------
    def create_tenant(self, tenant_id: str, budget_usd: float = 100.0, tokens_per_day: int = 1_000_000) -> Tenant:
        with self._lock:
            t = Tenant(tenant_id=tenant_id, budget_usd=budget_usd, tokens_per_day=tokens_per_day)
            self._tenants[tenant_id] = t
            return t

    def mint_virtual_key(self, tenant_id: str, budget_usd: Optional[float] = None) -> str:
        """Create a virtual key for a tenant and return the raw key (shown once)."""
        with self._lock:
            if tenant_id not in self._tenants:
                self.create_tenant(tenant_id)
            if budget_usd is not None:
                self._tenants[tenant_id].budget_usd = budget_usd
            vk = generate_virtual_key()
            self._virtual[hash_virtual_key(vk)] = tenant_id
            return vk

    def resolve_virtual_key(self, virtual_key: str) -> Optional[Tenant]:
        """Validate a presented virtual key; return the tenant or None."""
        with self._lock:
            tenant_id = self._virtual.get(hash_virtual_key(virtual_key))
            if tenant_id is None:
                return None
            t = self._tenants.get(tenant_id)
            if t is None or not t.enabled:
                return None
            return t

    def authorize(self, virtual_key: str, estimated_cost_usd: float = 0.0) -> Optional[Tenant]:
        """BYOK auth + budget pre-check. Returns tenant if allowed, else None."""
        t = self.resolve_virtual_key(virtual_key)
        if t is None:
            return None
        if t.spent_usd + estimated_cost_usd > t.budget_usd:
            return None
        return t

    def charge(self, tenant: Tenant, cost_usd: float, tokens: int) -> None:
        with self._lock:
            tenant.spent_usd += cost_usd
            tenant.tokens_today += tokens

    def tenant(self, tenant_id: str) -> Optional[Tenant]:
        with self._lock:
            return self._tenants.get(tenant_id)

    # ---- provider keys & rotation --------------------------------------
    def register_provider_key(
        self,
        provider: str,
        key: str = "",
        ttl_s: Optional[float] = None,
    ) -> None:
        with self._lock:
            self._provider_keys.setdefault(provider, []).append(
                ProviderKey(provider=provider, key=key, ttl_s=ttl_s)
            )

    def set_rotate_callback(self, provider: str, cb: Callable[[str, str], str]) -> None:
        """``cb(provider, old_key_hint) -> new_key`` — hook to Vault/SM/KMS in prod."""
        with self._lock:
            self._rotate_callbacks[provider] = cb

    def _rotate(self, k: ProviderKey) -> None:
        cb = self._rotate_callbacks.get(k.provider)
        new_key = cb(k.provider, k.key) if cb else ""
        if new_key:
            with self._lock:
                k.key = new_key
            k.created_at = time.time()
            k.failures = 0
            k.status = "active"
            k.grace_until = None
        else:
            k.status = "disabled"   # needs operator attention / external rotation
            k.grace_until = None

    def usable_provider_keys(self, provider: str, now: Optional[float] = None) -> List[ProviderKey]:
        """Return currently usable keys, rotating any that have passed TTL+grace."""
        now = now or time.time()
        with self._lock:
            for k in list(self._provider_keys.get(provider, [])):
                if k.status in ("disabled",):  # expired & no replacement
                    continue
                if k.ttl_s:
                    deadline = k.created_at + k.ttl_s
                    if now > deadline:
                        if now > deadline + self._rotating_grace_s:
                            k.status = "disabled"
                            continue
                        k.status = "rotating"
                    else:
                        k.status = "active"
            out = [k for k in self._provider_keys.get(provider, []) if k.status != "disabled"]
        # lazily rotate keys that are past TTL and have a callback available
        for k in out:
            if k.status == "rotating" and k.provider in self._rotate_callbacks:
                old_created = k.created_at
                self._rotate(k)
                if k.created_at == old_created:
                    k.status = "rotating"
        out = [k for k in out if k.status in ("active", "rotating")]
        return out


def encrypt_secret(plaintext: str) -> Optional[str]:
    """Return ``enc:v1:<b64(iv|ciphertext|tag)>`` or None if no master key set."""
    key = _master_key()
    if key is None or not plaintext:
        return None
    iv = os.urandom(12)
    cipher = __import__("cryptography.hazmat.primitives.ciphers.aead", fromlist=["AESGCM"]).AESGCM(key)
    ct = cipher.encrypt(iv, plaintext.encode("utf-8"), None)
    blob = b"enc:v1:" + base64.b64encode(iv + ct)
    return blob.decode("utf-8")


def decrypt_secret(value: str) -> str:
    if value.startswith("enc:v1:"):
        key = _master_key()
        if key is None:
            raise RuntimeError("GATEWAY_MASTER_KEY not set; cannot decrypt provider secret")
        b64 = value[len("enc:v1:"):]
        raw = base64.b64decode(b64)
        iv, ct = raw[:12], raw[12:]
        cipher = __import__("cryptography.hazmat.primitives.ciphers.aead", fromlist=["AESGCM"]).AESGCM(key)
        return cipher.decrypt(iv, ct, None).decode("utf-8")
    return value


@dataclass
class Tenant:
    tenant_id: str
    budget_usd: float = 100.0
    tokens_per_day: int = 1_000_000
    spent_usd: float = 0.0
    tokens_today: int = 0
    enabled: bool = True


@dataclass
class ProviderKey:
    provider: str
    key: str = ""
    status: str = "active"          # active | rotating | disabled
    ttl_s: Optional[float] = None
    created_at: float = field(default_factory=time.time)
    grace_until: Optional[float] = None
    failures: int = 0
    last_good: Optional[float] = None