#!/usr/bin/env python3
"""Build the dashboard: dashboard/template.html + work/data/snapshot.json -> work/dist/dashboard.html.

An instance may override the template with work/dashboard/template.html (its own design); the
placeholder `/*__SNAPSHOT__*/null` is the only contract between the template and the data.
An optional logo (`logo`, `logo_dark` in work/CONFIG.md: image files in work/) is embedded as a
data URI where the template has `/*__LOGO__*/null`, so the page stays self-contained.

  scripts/build.py [--snapshot PATH] [--out PATH]
"""

import argparse
import base64
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib.mm import DEF, SNAPSHOT, WORK, cfg_all  # noqa: E402

PLACEHOLDER = "/*__SNAPSHOT__*/null"
LOGO_PLACEHOLDER = "/*__LOGO__*/null"
LOGO_MAX = 512 * 1024
LOGO_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp",
              ".svg": "image/svg+xml"}


def logo_uri(name):
    """work/<name> as a data URI. Raises SystemExit with the fix when it cannot be used."""
    path = os.path.realpath(os.path.join(WORK, name))
    if not path.startswith(os.path.realpath(WORK) + os.sep):
        raise SystemExit(f"logo {name}: must be a file inside work/")
    ext = os.path.splitext(path)[1].lower()
    if ext not in LOGO_TYPES:
        raise SystemExit(f"logo {name}: use one of {', '.join(sorted(LOGO_TYPES))}")
    if not os.path.isfile(path):
        raise SystemExit(f"logo {name}: no such file in work/")
    data = open(path, "rb").read()
    if len(data) > LOGO_MAX:
        raise SystemExit(f"logo {name}: {len(data) // 1024} KB, keep it under {LOGO_MAX // 1024} KB (resize it)")
    head = data[:512].lstrip()
    ok = {".png": data.startswith(b"\x89PNG"), ".jpg": data.startswith(b"\xff\xd8"),
          ".jpeg": data.startswith(b"\xff\xd8"), ".webp": data[8:12] == b"WEBP",
          ".svg": head.startswith(b"<svg") or head.startswith(b"<?xml")}[ext]
    if not ok:
        raise SystemExit(f"logo {name}: the content is not a {ext[1:]} image")
    return f"data:{LOGO_TYPES[ext]};base64,{base64.b64encode(data).decode()}"


def logos():
    conf = cfg_all()
    if not conf.get("logo"):
        return None
    light = logo_uri(conf["logo"])
    return {"light": light, "dark": logo_uri(conf["logo_dark"]) if conf.get("logo_dark") else light,
            "alt": conf.get("title") or ""}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot", default=SNAPSHOT)
    ap.add_argument("--out", default=os.path.join(WORK, "dist", "dashboard.html"))
    a = ap.parse_args()
    own = os.path.join(WORK, "dashboard", "template.html")
    tpl_path = own if os.path.exists(own) else os.path.join(DEF, "dashboard", "template.html")
    tpl = open(tpl_path, encoding="utf-8").read()
    if tpl.count(PLACEHOLDER) != 1:
        raise SystemExit(f"{tpl_path}: needs exactly one {PLACEHOLDER}")
    snap = json.load(open(a.snapshot))
    # </script> inside a label must not end the script element
    data = json.dumps(snap, separators=(",", ":")).replace("</", "<\\/")
    logo = logos()
    if logo and LOGO_PLACEHOLDER not in tpl:
        print(f"warning: {tpl_path} has no {LOGO_PLACEHOLDER}; the logo is not shown")
    tpl = tpl.replace(LOGO_PLACEHOLDER, json.dumps(logo).replace("</", "<\\/"))
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    tmp = a.out + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(tpl.replace(PLACEHOLDER, data, 1))
    os.replace(tmp, a.out)
    print(f"built {a.out} ({os.path.getsize(a.out) // 1024} KB) from {os.path.relpath(tpl_path, DEF if tpl_path.startswith(DEF) else WORK)}")


if __name__ == "__main__":
    main()
