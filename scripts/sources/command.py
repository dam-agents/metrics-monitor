"""Any other source: a command you write (psql, bq, a REST API with curl, a CSV export ...).

The metric's `query` is a shell command, run from the definition directory with
  MM_START  MM_END  MM_STEP   (unix seconds, seconds), and MM_WORK (the work directory),
in its environment. It prints JSON lines, one per bucket and series:
  {"t": 1760000000, "value": 12.5, "plan": "pro"}
`t` is the bucket start, `value` a number; every other key is a label. A window query runs the same
command with MM_STEP = MM_END - MM_START. Put the command's script in work/sources/ (instance data),
or in scripts/sources/ if it is general enough to ship with the kit.
"""

import json
import os
import subprocess

from lib.mm import DEF, WORK


class Source:
    name = "command"

    def __init__(self, conf):
        self.timeout = int(conf.get("command_timeout") or 600)

    def _run(self, cmd, start, end, step):
        env = {**os.environ, "MM_START": str(int(start)), "MM_END": str(int(end)), "MM_STEP": str(int(step)),
               "MM_WORK": WORK}
        p = subprocess.run(["bash", "-c", cmd], cwd=DEF, env=env, capture_output=True, text=True, timeout=self.timeout)
        if p.returncode != 0:
            raise RuntimeError(f"command exited {p.returncode}: {p.stderr.strip()[-800:]}")
        rows = []
        for line in p.stdout.splitlines():
            if line.strip():
                rows.append(json.loads(line))
        return rows

    @staticmethod
    def _split(row):
        labels = {k: str(v) for k, v in row.items() if k not in ("t", "value")}
        return labels, (None if row.get("value") is None else float(row["value"]))

    def range(self, query, start, end, step):
        merged = {}
        for row in self._run(query, start, end, step):
            labels, v = self._split(row)
            key = tuple(sorted(labels.items()))
            merged.setdefault(key, {"labels": labels, "points": {}})["points"][int(row["t"])] = v
        return [{"labels": s["labels"], "points": sorted(s["points"].items())} for s in merged.values()]

    def window(self, query, start, end):
        out = []
        for row in self._run(query, start, end, end - start):
            labels, v = self._split(row)
            out.append({"labels": labels, "value": v})
        return out

    def raw(self, query, at):
        return self._run(query, at - 3600, at, 3600)
