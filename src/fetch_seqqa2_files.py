"""Download LABBench2 SeqQA2 input + validator files from the public GCS bucket
(same bucket/layout as vendor/labbench2/evals/utils.py) into data/labbench2_files/."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BUCKET = "labbench2-data-public"
DEST = ROOT / "data" / "labbench2_files"


def fetch(prefix: str) -> None:
    prefix = prefix.strip("/") + "/"
    names, token = [], None
    while True:
        params = {"prefix": prefix, **({"pageToken": token} if token else {})}
        r = httpx.get(f"https://storage.googleapis.com/storage/v1/b/{BUCKET}/o", params=params, timeout=60)
        r.raise_for_status()
        d = r.json()
        names += [i["name"] for i in d.get("items", [])]
        token = d.get("nextPageToken")
        if not token:
            break
    for name in names:
        dest = DEST / name
        if name.endswith("/") or dest.exists():
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        r = httpx.get(f"https://storage.googleapis.com/{BUCKET}/{name}", timeout=120)
        r.raise_for_status()
        dest.write_bytes(r.content)


if __name__ == "__main__":
    df = pd.read_parquet(ROOT / "data/raw/labbench2/seqqa2.parquet")
    prefixes = sorted(set(df[df.ground_truth].files)) + ["validation"]
    with ThreadPoolExecutor(16) as ex:
        list(ex.map(fetch, prefixes))
    print("fetched", len(prefixes), "prefixes")
