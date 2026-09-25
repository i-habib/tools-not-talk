"""Check keys + exact model ids with one tiny call per model; list Gemini models matching gemma/flash-lite."""
import asyncio
import os
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).parent))
from llm import LLM, MODELS  # noqa: E402

PROMPT = "What is 17*3? Respond in exactly this format:\n<answer>NUMBER</answer>\nCONFIDENCE: <0-1>\nJUSTIFICATION: <one sentence>"


async def main(names):
    if os.environ.get("GEMINI_API_KEY"):
        r = httpx.get("https://generativelanguage.googleapis.com/v1beta/models?pageSize=1000",
                      headers={"x-goog-api-key": os.environ["GEMINI_API_KEY"]})
        ids = [m["name"].split("/")[-1] for m in r.json().get("models", [])]
        print("gemini models:", [i for i in ids if "gemma-4" in i or "flash-lite" in i])
    for n in names:
        llm = LLM(MODELS[n])
        try:
            out = await llm.complete(PROMPT, seed=1)
            print(f"OK   {n}: {out['text'][:120]!r} usage={out['usage']} finish={out['finish_reason']} {out['latency_s']}s")
        except Exception as e:
            print(f"FAIL {n}: {e!r}"[:600])
        await llm.aclose()


asyncio.run(main(sys.argv[1:] or ["gpt-oss-120b", "gemma-4-31b", "flash-lite"]))
