# The definition, its version, and `work/`

Read this when you are asked for your version or an update, or for a change to
this definition itself.

## Two places, never mixed

| Path | Kind | Holds |
| --- | --- | --- |
| `$HOME` | the definition, a git checkout (`origin`) | `kit.yaml`, `CLAUDE.md`, `AGENTS.md`, `ONBOARDING.md`, `README.md`, `LICENSE`, `VERSION`, `CHANGELOG.md`, `.gitignore`, `docs/`, `scripts/`, `dashboard/`, `examples/`, `.github/` |
| `$HOME/work` | runtime state, a plain directory | `CONFIG.md`, `metrics.json`, `CLAUDE.md` (this instance's notes), `AGENTS.md`, `VERSION`, `artifacts.json`, `.claude/settings.json`, `data/`, `dist/`, `logs/`, `sources/`, `reference/` (what the person showed at onboarding), optionally `dashboard/template.html` |

The `.gitignore` at `$HOME` is an allowlist, so `work/` and the home's secrets
(`.ssh`, `.claude`, `.config`) are invisible to the definition. **Never
`git clean` in `$HOME`**, and never `git add` outside the paths in the table.

`$HOME` survives a restart of the sandbox; nothing else does. `work/` is not
backed up anywhere else: `CONFIG.md`, `metrics.json`, `CLAUDE.md` and the
requirements log are the instance's memory. A lost snapshot costs one full
pull (`scripts/fetch.py --full`); a lost `CONFIG.md` costs one onboarding:
delete `$HOME/.metrics-monitor-onboarded` and follow `ONBOARDING.md`.

`scripts/browser/node_modules` is installed by the kit's install command and
lives in `$HOME`, so it survives a restart too. If it is missing, run
`cd "$HOME/scripts/browser" && npm ci`.

## Definition version & upgrade

`VERSION` is the definition's version; `work/VERSION` is the one this instance
last adopted.

**Check:**

```sh
branch="$(git -C "$HOME" ls-remote --symref origin HEAD | sed -n 's#^ref: refs/heads/\([^[:space:]]*\).*#\1#p')"
git -C "$HOME" fetch -q origin "$branch"
git -C "$HOME" show FETCH_HEAD:VERSION | head -1   # latest
head -1 "$HOME/VERSION"                            # checked out
head -1 "$HOME/work/VERSION"                       # adopted
```

Checked out behind latest: tell the person both versions, and update only
when they ask. Adopted behind checked out: migrate now.

**Update** a clean checkout by fast-forward:

```sh
git -C "$HOME" status --porcelain            # must be empty, otherwise stop and ask
git -C "$HOME" merge --ff-only FETCH_HEAD
```

**Migrate:** apply the `CHANGELOG.md` **Upgrade** blocks of every version
crossed, oldest first; run `bash "$HOME/scripts/verify-onboarding.sh" --live`
and apply every fix; run one refresh; only then write the new version to
`work/VERSION`.

## Evolving the definition

**First read [self-modification.md](self-modification.md).** A change to the
definition goes to the person as a patch, never as a push. Work in a clone of
its own, never in `$HOME`:

```sh
d="$(mktemp -d)"; git clone "$(git -C "$HOME" remote get-url origin)" "$d"
# edit in "$d", run self-modification.md §5's checks there
git -C "$d" diff > /tmp/definition.patch
```

Show the patch and hand it to the person. They open the pull request; `$HOME`
takes it at the next **Update**, once merged. A change that only this
instance needs (its own template, a source script) goes in `work/` instead,
where it never needs a pull request.
