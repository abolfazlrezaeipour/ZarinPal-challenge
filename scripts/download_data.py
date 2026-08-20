import os
import urllib.request
from pathlib import Path

DEFAULT_URL = "https://startech.s3.ir-thr-at1.arvanstorage.ir/other%2Fchallenge_data.csv.gz?versionId="
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "challenge_data.csv.gz"
URL = os.getenv("ZP_DATA_URL", DEFAULT_URL)

OUT.parent.mkdir(parents=True, exist_ok=True)
print(f"Downloading to {OUT} ...")
try:
    urllib.request.urlretrieve(URL, OUT)
except Exception as exc:
    print("Download failed:", exc)
    print("Set ZP_DATA_URL to a working challenge-data URL or copy the file to data/challenge_data.csv.gz")
    raise
print(f"Downloaded {OUT.stat().st_size:,} bytes")
