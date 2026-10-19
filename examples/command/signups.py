"""Example command source: prints one JSON line per bucket and series for MM_START..MM_END.

Copy to work/sources/signups.py and point it at your API. The request goes through the agent's
gateway: name the Custom Header connection with its path prefix (docs/sources.md).
"""
import json
import os
import urllib.request

start, end, step = (int(os.environ[k]) for k in ("MM_START", "MM_END", "MM_STEP"))
url = os.environ.get("SIGNUPS_URL", "https://api.example.com/__platform_conn/CONN_ID/v1/signups")
with urllib.request.urlopen(f"{url}?from={start}&to={end}&bucket={step}", timeout=60) as r:
    for row in json.load(r)["buckets"]:          # [{"start": 1760000000, "plan": "pro", "count": 12}, ...]
        print(json.dumps({"t": row["start"], "value": row["count"], "plan": row["plan"]}))
