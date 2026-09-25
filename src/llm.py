"""Minimal async clients for the free-tier backends, with RPM/TPM throttling, retries and usage logging.

Every call is a single user message (no system prompt) so that the request is identical across
providers (Gemma on the Gemini API does not accept system instructions).
"""
from __future__ import annotations

import asyncio
import os
import random
import re
import time
from collections import deque
from dataclasses import dataclass, field

import httpx
from dotenv import load_dotenv

load_dotenv()


@dataclass
class ModelCfg:
    name: str                 # short name used in results/ paths
    provider: str             # cerebras | groq | gemini | mock
    model: str                # provider model id
    rpm: int
    tpm: int
    tpm_input_only: bool = False  # Gemini API quotas count input tokens only
    max_tokens: int = 1024    # completion cap per call (includes hidden reasoning tokens)
    temperature: float = 0.6
    extra: dict = field(default_factory=dict)


MODELS = {
    # Cerebras free tier (inference-docs.cerebras.ai/support/rate-limits, 2026-09-25):
    # gpt-oss-120b 5 RPM, 30K uncached TPM, 90K total TPM, 1M TPH, 1M TPD (token-bucket replenishment).
    "gpt-oss-120b": ModelCfg("gpt-oss-120b", "cerebras", "gpt-oss-120b", rpm=5, tpm=28_000,
                             extra={"reasoning_effort": "low"}),
    "gpt-oss-120b-groq": ModelCfg("gpt-oss-120b-groq", "groq", "openai/gpt-oss-120b", rpm=28, tpm=7_500,
                                  extra={"reasoning_effort": "low"}),
    # Account limits observed in AI Studio (free tier, 2026-09-25): Gemma 4 31B 30 RPM / 16K input TPM / 14.4K RPD;
    # Gemini 3.5 Flash-Lite 15 RPM / 250K TPM / 500 RPD.
    "gemma-4-31b": ModelCfg("gemma-4-31b", "gemini", "gemma-4-31b-it", rpm=25, tpm=15_000, tpm_input_only=True),
    "flash-lite": ModelCfg("flash-lite", "gemini", "gemini-3.5-flash-lite", rpm=13, tpm=230_000, tpm_input_only=True,
                           extra={"thinkingConfig": {"thinkingLevel": "low"}}),
    "mock": ModelCfg("mock", "mock", "mock", rpm=100_000, tpm=10**9),
}

ENDPOINTS = {
    "cerebras": ("https://api.cerebras.ai/v1/chat/completions", "CEREBRAS_API_KEY"),
    "groq": ("https://api.groq.com/openai/v1/chat/completions", "GROQ_API_KEY"),
}


class Throttle:
    """Sliding 60 s window over requests and (estimated, then actual) tokens."""

    def __init__(self, rpm: int, tpm: int):
        self.rpm, self.tpm = rpm, tpm
        self.events: deque[list] = deque()  # [timestamp, tokens]
        self.lock = asyncio.Lock()

    async def acquire(self, est_tokens: int) -> list:
        while True:
            async with self.lock:
                now = time.monotonic()
                while self.events and now - self.events[0][0] > 60:
                    self.events.popleft()
                used = sum(e[1] for e in self.events)
                if len(self.events) < self.rpm and used + est_tokens <= self.tpm:
                    ev = [now, est_tokens]
                    self.events.append(ev)
                    return ev
                wait = 60 - (now - self.events[0][0]) + 0.05 if self.events else 1
            await asyncio.sleep(min(max(wait, 0.2), 5))


class LLM:
    def __init__(self, cfg: ModelCfg, concurrency: int = 8):
        self.cfg = cfg
        self.throttle = Throttle(cfg.rpm, cfg.tpm)
        self.sem = asyncio.Semaphore(concurrency)
        self.http = httpx.AsyncClient(timeout=180)

    async def complete(self, prompt: str, seed: int) -> dict:
        est = len(prompt) // 3 + (0 if self.cfg.tpm_input_only else self.cfg.max_tokens)
        async with self.sem:
            for attempt in range(8):
                ev = await self.throttle.acquire(est)
                t0 = time.monotonic()
                try:
                    out = await self._call(prompt, seed)
                    out["latency_s"] = round(time.monotonic() - t0, 3)
                    out["attempts"] = attempt + 1
                    u = out["usage"]
                    ev[1] = u["input_tokens"] if self.cfg.tpm_input_only else u["total_tokens"]
                    return out
                except httpx.HTTPStatusError as e:
                    code = e.response.status_code
                    body = e.response.text[:500]
                    if code in (429, 500, 502, 503, 504) and attempt < 7:
                        ra = e.response.headers.get("retry-after")
                        delay = float(ra) if ra and re.fullmatch(r"[\d.]+", ra) else min(90, 5 * 2 ** attempt)
                        if code == 429 and "per day" in body.lower():
                            raise QuotaExhausted(body) from e
                        await asyncio.sleep(delay + random.random())
                        continue
                    raise RuntimeError(f"HTTP {code}: {body}") from e
                except (httpx.TransportError, httpx.TimeoutException):
                    if attempt < 7:
                        await asyncio.sleep(min(60, 3 * 2 ** attempt))
                        continue
                    raise
        raise RuntimeError("unreachable")

    async def _call(self, prompt: str, seed: int) -> dict:
        c = self.cfg
        if c.provider == "mock":
            return _mock(prompt, seed)
        if c.provider in ENDPOINTS:
            url, env = ENDPOINTS[c.provider]
            body = {"model": c.model, "messages": [{"role": "user", "content": prompt}],
                    "temperature": c.temperature, "max_completion_tokens": c.max_tokens, "seed": seed, **c.extra}
            r = await self.http.post(url, json=body, headers={"Authorization": f"Bearer {os.environ[env]}"})
            r.raise_for_status()
            d = r.json()
            ch = d["choices"][0]
            u = d.get("usage") or {}
            det = u.get("completion_tokens_details") or {}
            return {
                "text": ch["message"].get("content") or "",
                "reasoning": ch["message"].get("reasoning") or "",
                "finish_reason": ch.get("finish_reason"),
                "usage": {"input_tokens": u.get("prompt_tokens", 0), "output_tokens": u.get("completion_tokens", 0),
                          "reasoning_tokens": det.get("reasoning_tokens"), "total_tokens": u.get("total_tokens", 0)},
                "raw_usage": u,
            }
        if c.provider == "gemini":
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{c.model}:generateContent"
            gen = {"temperature": c.temperature, "maxOutputTokens": c.max_tokens, "seed": seed,
                   **{k: v for k, v in c.extra.items()}}
            body = {"contents": [{"role": "user", "parts": [{"text": prompt}]}], "generationConfig": gen}
            r = await self.http.post(url, json=body, headers={"x-goog-api-key": os.environ["GEMINI_API_KEY"]})
            r.raise_for_status()
            d = r.json()
            cand = (d.get("candidates") or [{}])[0]
            parts = (cand.get("content") or {}).get("parts") or []
            text = "".join(p.get("text", "") for p in parts if not p.get("thought"))
            thought = "".join(p.get("text", "") for p in parts if p.get("thought"))
            u = d.get("usageMetadata") or {}
            out_t = u.get("candidatesTokenCount", 0) + u.get("thoughtsTokenCount", 0)
            return {
                "text": text, "reasoning": thought, "finish_reason": cand.get("finishReason"),
                "usage": {"input_tokens": u.get("promptTokenCount", 0), "output_tokens": out_t,
                          "reasoning_tokens": u.get("thoughtsTokenCount"),
                          "total_tokens": u.get("totalTokenCount", u.get("promptTokenCount", 0) + out_t)},
                "raw_usage": u,
            }
        raise ValueError(c.provider)

    async def aclose(self):
        await self.http.aclose()


class QuotaExhausted(RuntimeError):
    pass


def _mock(prompt: str, seed: int) -> dict:
    rng = random.Random(hash((prompt[-200:], seed)))
    if "Options:" in prompt:
        n = len(re.findall(r"^[A-J]\) ", prompt, re.M))
        ans = "ABCDEFGHIJ"[rng.randrange(max(n, 1))]
    else:
        ans = str(round(rng.uniform(0, 100), 2))
    text = (f"CRITIQUE: The solution may be wrong." if prompt.rstrip().endswith('starting with "CRITIQUE:".')
            else f"<answer>{ans}</answer>\nCONFIDENCE: {rng.random():.2f}\nJUSTIFICATION: mock.")
    n_in = len(prompt) // 4
    return {"text": text, "reasoning": "", "finish_reason": "stop",
            "usage": {"input_tokens": n_in, "output_tokens": 40, "reasoning_tokens": 20, "total_tokens": n_in + 40},
            "raw_usage": {}}
