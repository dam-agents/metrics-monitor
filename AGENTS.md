# Agent entry point

This repository is an **agent definition**, not an application. Read
**[`CLAUDE.md`](CLAUDE.md)** first, under any harness.

Reading order:

1. **[`CLAUDE.md`](CLAUDE.md)**: always, before anything else.
2. **`work/CONFIG.md`**: the data source, dashboard and Slack settings this
   instance was set up with. Written during onboarding; never guessed.
3. **`work/CLAUDE.md`**: this instance's own notes: what its data means, its
   quirks and the decisions made about it. Written by the agent as it learns.
4. **[`ONBOARDING.md`](ONBOARDING.md)**: only on a fresh instance with no
   `$HOME/.metrics-monitor-onboarded` marker.

`/etc/AGENTS.md`, which the platform ships in the image, describes the sandbox
itself: what is installed, what survives a restart, the browser. It is not
repeated here.

This file is a pointer: nothing here overrides `CLAUDE.md`.
