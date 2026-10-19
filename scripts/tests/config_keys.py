"""Print the keys CLAUDE.md -> Runtime configuration documents: in each bullet,
the backticked names before the first "`:" (e.g. "- `title`, `subtitle`: ...")."""
import re
import sys

text = open(sys.argv[1]).read()
sec = text.split("## Runtime configuration", 1)[1].split("\n## ", 1)[0]
keys = set()
for bullet in re.split(r"\n(?=- )", sec):
    if bullet.startswith("- `"):
        head = bullet.split("`:", 1)[0] + "`"
        keys.update(re.findall(r"`([a-z_]+)`", head))
print("\n".join(sorted(keys)))
