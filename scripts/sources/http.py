"""Small stdlib HTTP helper shared by the adapters: timeouts, TLS opt-out, error bodies, retries."""

import json
import os
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request


def parse_headers(s):
    """'Name: value; Other: value' -> dict (from CONFIG.md `source_headers`)."""
    out = {}
    for part in (s or "").split(";"):
        if ":" in part:
            k, v = part.split(":", 1)
            out[k.strip()] = v.strip()
    return out


def request(url, data=None, headers=None, insecure=False, timeout=None, retries=2):
    timeout = timeout or float(os.environ.get("MM_TIMEOUT", "120"))
    ctx = None
    if url.startswith("https"):
        ctx = ssl.create_default_context()
        if insecure:
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
    body = data.encode() if isinstance(data, str) else data
    last = None
    for attempt in range(retries + 1):
        req = urllib.request.Request(url, data=body, method="POST" if body is not None else "GET")
        for k, v in (headers or {}).items():
            req.add_header(k, v)
        try:
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
                return r.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            msg = e.read().decode("utf-8", "replace").strip()[:800]
            last = RuntimeError(f"HTTP {e.code} from {url.split('?')[0]}: {msg}")
            if e.code < 500 and e.code != 429:
                raise last from None
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            last = RuntimeError(f"cannot reach {url.split('?')[0]}: {e}")
        time.sleep(3 * (attempt + 1))
    raise last


def get_json(url, **kw):
    return json.loads(request(url, **kw))
