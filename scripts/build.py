#!/usr/bin/env python3
"""Build the dashboard: dashboard/template.html + work/data/snapshot.json -> work/dist/dashboard.html.

An instance may override the template with work/dashboard/template.html (its own design); the
placeholder `/*__SNAPSHOT__*/null` is the only contract between the template and the data.

  scripts/build.py [--snapshot PATH] [--out PATH]
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib.mm import DEF, SNAPSHOT, WORK  # noqa: E402

PLACEHOLDER = "/*__SNAPSHOT__*/null"


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
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    tmp = a.out + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(tpl.replace(PLACEHOLDER, data))
    os.replace(tmp, a.out)
    print(f"built {a.out} ({os.path.getsize(a.out) // 1024} KB) from {os.path.relpath(tpl_path, DEF if tpl_path.startswith(DEF) else WORK)}")


if __name__ == "__main__":
    main()
