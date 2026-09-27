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
for _short, _full in (("CEREBRAS", "CEREBRAS_API_KEY"), ("GEMINI", "GEMINI_API_KEY"), ("GROQ", "GROQ_API_KEY")):
    if not os.environ.get(_full) and os.environ.get(_short):
        os.environ[_full] = os.environ[_short].strip().strip('"').strip("'")


@dataclass
class ModelCfg:
    name: str                 # short name used in results/ paths
    provider: str             # cerebras | groq | gemini | mock
    model: str                # provider model id
    rpm: int
    tpm: int
    rph: int = 0                  # requests per hour (0 = none)
    tpm_input_only: bool = False  # Gemini API quotas count input tokens only
    max_tokens: int = 2048    # completion cap per call (includes hidden reasoning tokens)
    temperature: float = 0.6
    extra: dict = field(default_factory=dict)


MODELS = {
    # Cerebras free tier (inference-docs.cerebras.ai/support/rate-limits, 2026-09-25):
    # gpt-oss-120b 5 RPM, 30K uncached TPM, 90K total TPM, 1M TPH, 1M TPD; response headers additionally show
    # 150 requests/hour and 2,400 requests/day (x-ratelimit-limit-requests-hour/-day).
    "gpt-oss-120b": ModelCfg("gpt-oss-120b", "cerebras", "gpt-oss-120b", rpm=5, tpm=28_000, rph=148,
                             extra={"reasoning_effort": "low"}),
    "gpt-oss-120b-groq": ModelCfg("gpt-oss-120b-groq", "groq", "openai/gpt-oss-120b", rpm=28, tpm=7_500,
                                  extra={"reasoning_effort": "low"}),
    # Account limits observed in AI Studio (free tier, 2026-09-25): Gemma 4 31B 30 RPM / 16K input TPM / 14.4K RPD;
    # Gemini 3.5 Flash-Lite 15 RPM / 250K TPM / 500 RPD.
    "gemma-4-31b": ModelCfg("gemma-4-31b", "gemini", "gemma-4-31b-it", rpm=25, tpm=15_000, tpm_input_only=True,
                            # Default Gemma 4 thinking exhausted the 1024-token cap on every pilot call (no answer);
                            # "minimal" is the only accepted thinking control ("low"/thinkingBudget -> HTTP 400).
                            extra={"thinkingConfig": {"thinkingLevel": "minimal"}}),
    "flash-lite": ModelCfg("flash-lite", "gemini", "gemini-3.5-flash-lite", rpm=13, tpm=230_000, tpm_input_only=True,
                           extra={"thinkingConfig": {"thinkingLevel": "low"}}),
    # Exploratory supplement (added after freeze): frontier GPT models via the Codex CLI (ChatGPT account).
    # Agent harness adds its own system prompt; no temperature/seed control; read-only sandbox in an empty dir.
    "gpt-6-luna": ModelCfg("gpt-6-luna", "codex", "gpt-6-luna", rpm=30, tpm=10**9, extra={"effort": "low"}),
    "gpt-6-sol": ModelCfg("gpt-6-sol", "codex", "gpt-6-sol", rpm=30, tpm=10**9, extra={"effort": "low"}),
    "gpt-5.6-terra": ModelCfg("gpt-5.6-terra", "codex", "gpt-5.6-terra", rpm=30, tpm=10**9, extra={"effort": "low"}),
    # "Think longer, not together" arm: single call (Direct) at high reasoning, same 30 questions (added 2026-09-26).
    "gpt-oss-120b-high": ModelCfg("gpt-oss-120b-high", "cerebras", "gpt-oss-120b", rpm=5, tpm=28_000, rph=148,
                                  max_tokens=8192, extra={"reasoning_effort": "high"}),
    "flash-lite-high": ModelCfg("flash-lite-high", "gemini", "gemini-3.5-flash-lite", rpm=13, tpm=230_000,
                                tpm_input_only=True, max_tokens=8192, extra={"thinkingConfig": {"thinkingLevel": "high"}}),
    # Tools arm (added 2026-09-26 17:00): same Luna/low, but code execution + live web search enabled.
    "gpt-6-luna-tools": ModelCfg("gpt-6-luna-tools", "codex", "gpt-6-luna", rpm=30, tpm=10**9,
                                 extra={"effort": "low", "tools": True}),
    "gpt-6-luna-tools-high": ModelCfg("gpt-6-luna-tools-high", "codex", "gpt-6-luna", rpm=30, tpm=10**9,
                                      extra={"effort": "high", "tools": True}),
    # GPT-OSS via Ollama cloud (added 2026-09-26 14:15): high-reasoning arm + a low Direct provider check.
    "gpt-oss-120b-ollama-high": ModelCfg("gpt-oss-120b-ollama-high", "ollama", "gpt-oss:120b-cloud", rpm=30,
                                         tpm=10**9, max_tokens=16384, extra={"think": "high"}),
    "gpt-oss-120b-ollama-low": ModelCfg("gpt-oss-120b-ollama-low", "ollama", "gpt-oss:120b-cloud", rpm=30,
                                        tpm=10**9, extra={"think": "low"}),
    # High-reasoning baseline for the frontier supplement (requested 2026-09-26); luna-low above is kept as ablation.
    "gpt-6-luna-high": ModelCfg("gpt-6-luna-high", "codex", "gpt-6-luna", rpm=30, tpm=10**9, extra={"effort": "high"}),
    "gpt-6-sol-high": ModelCfg("gpt-6-sol-high", "codex", "gpt-6-sol", rpm=30, tpm=10**9, extra={"effort": "high"}),
    "gpt-5.6-terra-high": ModelCfg("gpt-5.6-terra-high", "codex", "gpt-5.6-terra", rpm=30, tpm=10**9, extra={"effort": "high"}),
    "mock": ModelCfg("mock", "mock", "mock", rpm=100_000, tpm=10**9),
}

ENDPOINTS = {
    "cerebras": ("https://api.cerebras.ai/v1/chat/completions", "CEREBRAS_API_KEY"),
    "groq": ("https://api.groq.com/openai/v1/chat/completions", "GROQ_API_KEY"),
}


class Throttle:
    """Sliding 60 s window over requests and (estimated, then actual) tokens."""

    def __init__(self, rpm: int, tpm: int, rph: int = 0):
        self.rpm, self.tpm, self.rph = rpm, tpm, rph
        self.events: deque[list] = deque()  # [timestamp, tokens]
        self.hour: deque[float] = deque()
        self.lock = asyncio.Lock()

    async def acquire(self, est_tokens: int) -> list:
        while True:
            async with self.lock:
                now = time.monotonic()
                while self.events and now - self.events[0][0] > 60:
                    self.events.popleft()
                while self.hour and now - self.hour[0] > 3600:
                    self.hour.popleft()
                used = sum(e[1] for e in self.events)
                hour_ok = not self.rph or len(self.hour) < self.rph
                if len(self.events) < self.rpm and used + est_tokens <= self.tpm and hour_ok:
                    ev = [now, est_tokens]
                    self.events.append(ev)
                    self.hour.append(now)
                    return ev
                if not hour_ok:
                    wait = 3600 - (now - self.hour[0]) + 0.05
                else:
                    wait = 60 - (now - self.events[0][0]) + 0.05 if self.events else 1
            await asyncio.sleep(min(max(wait, 0.2), 5))


class LLM:
    def __init__(self, cfg: ModelCfg, concurrency: int = 8):
        self.cfg = cfg
        self.throttle = Throttle(cfg.rpm, cfg.tpm, cfg.rph)
        self.sem = asyncio.Semaphore(concurrency)
        self.http = httpx.AsyncClient(timeout=180)

    async def complete(self, prompt: str, seed: int) -> dict:
        est = len(prompt) // 3 + (0 if self.cfg.tpm_input_only else self.cfg.max_tokens)
        async with self.sem:
            for attempt in range(40):
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
                    # rate limits (429) are retried patiently; server errors at most 8 times
                    if (code == 429 and attempt < 39) or (code in (500, 502, 503, 504) and attempt < 7):
                        ra = e.response.headers.get("retry-after")
                        # cap: a long retry-after (hourly window) must not park the worker once capacity frees up
                        delay = min(float(ra), 300) if ra and re.fullmatch(r"[\d.]+", ra) else min(90, 5 * 2 ** min(attempt, 4))
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
        if c.provider == "codex":
            return await _codex(c, prompt)
        if c.provider == "ollama":
            body = {"model": c.model, "messages": [{"role": "user", "content": prompt}], "stream": False,
                    "think": c.extra.get("think", "low"),
                    "options": {"temperature": c.temperature, "seed": seed, "num_predict": c.max_tokens}}
            r = await self.http.post("http://localhost:11434/api/chat", json=body)
            if r.status_code == 429 or "usage limit" in r.text.lower():
                raise QuotaExhausted(r.text[:300])
            r.raise_for_status()
            d = r.json()
            msg = d.get("message") or {}
            n_in, n_out = d.get("prompt_eval_count", 0), d.get("eval_count", 0)
            return {"text": msg.get("content") or "", "reasoning": msg.get("thinking") or "",
                    "finish_reason": d.get("done_reason"),
                    "usage": {"input_tokens": n_in, "output_tokens": n_out, "reasoning_tokens": None,
                              "total_tokens": n_in + n_out}, "raw_usage": {}}
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


CODEX_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results", "_codex_empty")


# No retrieval, no code execution, no sub-agents: the Codex harness must behave like a plain completion.
CODEX_DISABLE = ["shell_tool", "unified_exec", "unified_exec_tty", "code_mode_host", "multi_agent", "apps",
                 "browser_use", "browser_use_external", "computer_use", "in_app_browser", "image_generation",
                 "plugins", "remote_plugin", "skill_search", "tool_suggest", "view_image", "sleep_tool"]


# Tools arm: keep code execution (shell/exec) and live web search; still no sub-agents, plugins, apps or MCP.
CODEX_DISABLE_TOOLS_ARM = ["multi_agent", "apps", "browser_use", "browser_use_external", "computer_use",
                           "in_app_browser", "image_generation", "plugins", "remote_plugin", "skill_search",
                           "tool_suggest", "view_image", "sleep_tool"]


TOOLS_NOTE = ("You have a shell with Python (for exact sequence computations) and web search (for literature and "
              "database lookups); use them whenever they would make your answer more reliable.")


async def _codex(c: ModelCfg, prompt: str) -> dict:
    """Retry (up to 3x) any call in which the agent used a tool; if all attempts used tools, return the last one
    with `tool_items` set so the analysis can flag it. The tools arm allows tools and never retries."""
    if c.extra.get("tools"):
        return await _codex_once(c, prompt)
    for _ in range(3):
        out = await _codex_once(c, prompt)
        if not out["tool_items"]:
            return out
    return out


async def _codex_once(c: ModelCfg, prompt: str) -> dict:
    import json as _json
    os.makedirs(CODEX_DIR, exist_ok=True)
    tools = bool(c.extra.get("tools"))
    if tools:  # the tools condition's harness note (the only prompt difference from the no-tools condition)
        prompt = TOOLS_NOTE + "\n\n" + prompt
    disable = [a for f in (CODEX_DISABLE_TOOLS_ARM if tools else CODEX_DISABLE) for a in ("--disable", f)]
    proc = await asyncio.create_subprocess_exec(
        "codex", "exec", "--json", "--skip-git-repo-check", "--ephemeral", "-s", "read-only", "-C", CODEX_DIR,
        "-m", c.model, "-c", f'model_reasoning_effort="{c.extra.get("effort", "low")}"',
        "-c", f'web_search="{"live" if tools else "disabled"}"', "-c", "mcp_servers={}", *disable, "-",
        stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    try:
        out, err = await asyncio.wait_for(proc.communicate(prompt.encode()), timeout=600)
    except asyncio.TimeoutError:
        proc.kill()
        raise httpx.TimeoutException("codex exec timed out")
    texts, usage, other, errors, details = [], {}, [], [], []
    for line in out.decode(errors="replace").splitlines():
        try:
            ev = _json.loads(line)
        except ValueError:
            continue
        if ev.get("type") == "item.completed":
            item = ev.get("item", {})
            if item.get("type") == "agent_message":
                texts.append(item.get("text", ""))
            elif item.get("type") == "error" and "code-mode host is disabled" in item.get("message", ""):
                pass  # expected: code execution is disabled and fails closed
            elif item.get("type") != "reasoning":
                other.append(item.get("type"))
                details.append({k: item.get(k) for k in ("type", "query", "action", "command", "aggregated_output",
                                                         "exit_code") if item.get(k) is not None})
        elif ev.get("type") == "turn.completed":
            usage = ev.get("usage", {})
        elif ev.get("type") in ("error", "turn.failed"):
            errors.append(str(ev)[:400])
    blob = " ".join(errors) + err.decode(errors="replace")[-600:]
    if not texts:
        low = blob.lower()
        if "usage limit" in low or "rate limit" in low or "quota" in low:
            raise QuotaExhausted(blob[:400])
        raise RuntimeError(f"codex exec produced no message: {blob[:400]}")
    n_in, n_out = usage.get("input_tokens", 0), usage.get("output_tokens", 0) + usage.get("reasoning_output_tokens", 0)
    for d in details:
        if "aggregated_output" in d:
            d["aggregated_output"] = str(d["aggregated_output"])[:2000]
    return {"text": texts[-1], "reasoning": "", "finish_reason": "stop", "tool_items": other, "tool_details": details,
            "usage": {"input_tokens": n_in, "output_tokens": n_out, "reasoning_tokens": usage.get("reasoning_output_tokens"),
                      "total_tokens": n_in + n_out}, "raw_usage": usage}


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
