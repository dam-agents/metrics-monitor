"""Offline tests: metrics.json validation, range values, adapters' pure parts, and the checks
catching what they exist to catch. Run by scripts/tests/run.sh (MM_WORK set to a temp dir)."""

import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.dirname(HERE)
DEF = os.path.dirname(SCRIPTS)
sys.path.insert(0, SCRIPTS)

from lib import mm  # noqa: E402
from sources.clickhouse import Source as CH  # noqa: E402
from sources.http import parse_headers  # noqa: E402


def spec_file(obj):
    f = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
    json.dump(obj, f)
    f.close()
    return f.name


BASE = {"metrics": [{"id": "a", "label": "A", "unit": "x", "query": "q"}]}


class Metrics(unittest.TestCase):
    def test_defaults(self):
        s = mm.load_metrics(spec_file(BASE))
        m = s["metrics"][0]
        self.assertEqual((s["step"], m["kind"], m["combine"], m["by"]), (3600, "sum", "sum", None))

    def test_examples_valid(self):
        for d in os.listdir(os.path.join(DEF, "examples")):
            mm.load_metrics(os.path.join(DEF, "examples", d, "metrics.json"))

    def bad(self, obj, needle):
        with self.assertRaises(ValueError) as c:
            mm.load_metrics(spec_file(obj))
        self.assertIn(needle, str(c.exception))

    def test_rejects(self):
        m = BASE["metrics"][0]
        self.bad({"metrics": []}, "non-empty")
        self.bad({"metrics": [m, m]}, "duplicate id")
        self.bad({"metrics": [{**m, "kind": "median"}]}, "kind must be")
        self.bad({"metrics": [{**m, "kpi": {"op": ">=", "target": 1}}]}, "set_by")
        self.bad({"metrics": [{**m, "kind": "avg"}], "derived": [
            {"id": "c", "label": "C", "unit": "$", "op": "times", "a": "a", "factor": 2, "set_by": "x"}]}, "sum metric")
        self.bad({**BASE, "derived": [{"id": "c", "label": "C", "unit": "$", "op": "times", "a": "a", "factor": 2}]},
                 "set_by")
        self.bad({**BASE, "derived": [{"id": "a", "label": "C", "unit": "$", "op": "ratio", "a": "a", "b": "a"}]},
                 "no metric uses")


class RangeValue(unittest.TestCase):
    S = [{"key": "x", "points": [[0, 1], [3600, 2], [7200, 3]]}, {"key": "y", "points": [[0, 10], [7200, 30]]}]

    def test_kinds(self):
        rv = mm.range_value
        self.assertEqual(rv({"kind": "sum", "combine": "sum"}, self.S, 0, 10800), 46)
        self.assertEqual(rv({"kind": "avg", "combine": "mean"}, self.S, 0, 10800), (5.5 + 2 + 16.5) / 3)
        self.assertEqual(rv({"kind": "last", "combine": "max"}, self.S, 0, 10800), 30)
        self.assertEqual(rv({"kind": "sum", "combine": "sum"}, self.S, 3600, 7200), 2)
        self.assertIsNone(rv({"kind": "sum", "combine": "sum"}, self.S, 20000, 30000))

    def test_template_mirrors(self):
        # the page computes a range the same way; a change to one must reach the other
        with open(os.path.join(DEF, "dashboard", "template.html")) as f:
            t = f.read()
        self.assertIn("function rangeValue", t)
        self.assertEqual(t.count("/*__SNAPSHOT__*/null"), 1)


class Adapters(unittest.TestCase):
    def test_headers(self):
        self.assertEqual(parse_headers("X-Scope-OrgID: t; Accept: a/b"), {"X-Scope-OrgID": "t", "Accept": "a/b"})
        self.assertEqual(parse_headers(""), {})

    def test_clickhouse_fill(self):
        sql = CH.fill("SELECT $bucket(ts) AS t, count() AS value FROM r WHERE $range(ts) GROUP BY t", 3600, 7200, 600)
        self.assertIn("intDiv(toUInt32(toUnixTimestamp(ts)) - 3600, 600) * 600", sql)
        self.assertIn("ts >= toDateTime(3600) AND ts < toDateTime(7200)", sql)
        self.assertNotIn("$", sql)

    def test_command(self):
        from sources.command import Source
        cmd = 'echo "{\\"t\\": $MM_START, \\"value\\": 2, \\"k\\": \\"a\\"}"'
        r = Source({}).range(cmd, 3600, 7200, 3600)
        self.assertEqual(r, [{"labels": {"k": "a"}, "points": [(3600, 2.0)]}])
        self.assertEqual(Source({}).window(cmd, 0, 100)[0]["value"], 2.0)

    def test_demo_window_matches_range(self):
        from sources.demo import Source
        s = Source({})
        for q in ("sessions", "signups", "errors"):
            rng = sum(v for x in s.range(q, 0, 86400 * 3, 3600) for _, v in x["points"])
            win = sum(x["value"] for x in s.window(q, 0, 86400 * 3))
            self.assertAlmostEqual(rng, win, places=6)


def run(*args, env=None):
    return subprocess.run(args, cwd=DEF, capture_output=True, text=True, env={**os.environ, **(env or {})})


class Checks(unittest.TestCase):
    """Against the snapshot run.sh built from the demo source."""

    @classmethod
    def setUpClass(cls):
        cls.snap = os.path.join(mm.WORK, "data", "snapshot.json")
        with open(cls.snap) as f:
            cls.data = json.load(f)

    def tamper(self, fn):
        d = json.loads(json.dumps(self.data))
        fn(d)
        return spec_file(d)

    def test_clean_passes(self):
        r = run("python3", "scripts/check_snapshot.py", self.snap, self.snap)
        self.assertEqual(r.returncode, 0, r.stdout)
        r = run("python3", "scripts/verify.py", "--check")
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_total_fell(self):
        def drop(d):
            s = max(d["series"]["sessions"], key=lambda x: sum(v for _, v in x["points"]))
            s["points"] = s["points"][100:]
        r = run("python3", "scripts/check_snapshot.py", self.tamper(drop), self.snap)
        self.assertEqual(r.returncode, 4)
        self.assertIn("fell", r.stdout)

    def test_series_gone(self):
        r = run("python3", "scripts/check_snapshot.py",
                self.tamper(lambda d: d["series"]["sessions"].pop()), self.snap)
        self.assertEqual(r.returncode, 4)
        self.assertIn("series gone", r.stdout)

    def test_stale(self):
        def old(d):
            d["meta"]["end"] -= 6 * 3600
        r = run("python3", "scripts/check_snapshot.py", self.tamper(old), self.snap)
        self.assertEqual(r.returncode, 4)
        self.assertIn("ago (allowed", r.stdout)

    def test_verify_catches_drift(self):
        def inflate(d):
            for s in d["series"]["signups"]:
                s["points"] = [[t, v * 1.05] for t, v in s["points"]]
        r = run("python3", "scripts/verify.py", "--check", "--snapshot", self.tamper(inflate))
        self.assertEqual(r.returncode, 2)
        self.assertIn("FAIL  signups", r.stdout)


class Logo(unittest.TestCase):
    PNG = b"\x89PNG\r\n\x1a\n" + b"\0" * 32

    def setUp(self):
        import build
        self.build = build
        self.made = []

    def tearDown(self):
        for p in self.made:
            os.remove(p)

    def put(self, name, data):
        p = os.path.join(mm.WORK, name)
        with open(p, "wb") as f:
            f.write(data)
        self.made.append(p)

    def test_embeds(self):
        self.put("t-logo.png", self.PNG)
        self.assertTrue(self.build.logo_uri("t-logo.png").startswith("data:image/png;base64,"))

    def refused(self, name, needle):
        with self.assertRaises(SystemExit) as c:
            self.build.logo_uri(name)
        self.assertIn(needle, str(c.exception))

    def test_refuses(self):
        self.put("t-fake.png", b"<html>")
        self.put("t-big.svg", b"<svg>" + b" " * (600 * 1024))
        self.refused("../../etc/hostname", "inside work/")
        self.refused("t-none.png", "no such file")
        self.refused("metrics.json", "use one of")
        self.refused("t-fake.png", "not a png")
        self.refused("t-big.svg", "under 512 KB")

    def test_template_slot(self):
        with open(os.path.join(DEF, "dashboard", "template.html")) as f:
            self.assertEqual(f.read().count("/*__LOGO__*/null"), 1)


class Publish(unittest.TestCase):
    def test_refuses_other_url(self):
        r = run("bash", "scripts/publish_upload.sh", "https://example.com/upload")
        self.assertEqual(r.returncode, 2)
        self.assertIn("refused", r.stderr)

    def test_refuses_other_file(self):
        r = run("bash", "scripts/publish_upload.sh", "https://x.example/platform-artifacts/a?sig=1", "/etc/passwd")
        self.assertEqual(r.returncode, 2)
        self.assertIn("refused", r.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=1)
