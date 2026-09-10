---
name: claude-memory-synced-through-this-repo
description: This project's Claude memory directory is a symlink into the repo so it syncs across Aranya's home and work machines via git
metadata:
  type: project
---

Aranya uses this private repo from **two machines** (home + work) and wants Claude's
project memory to travel with it.

**Setup:** `~/.claude/projects/<slug>/memory` is a **symlink** to `.claude/memory/` inside
the repo, so every memory file written here is a normal tracked file that syncs on push/pull.
`<slug>` is the repo's absolute path with each non-alphanumeric character replaced by `-`
(e.g. `/mnt/d/Sem 7/EPP-7th-Sem` -> `-mnt-d-Sem-7-EPP-7th-Sem`), which is why the link has
to be re-created per machine rather than committed.

**On a new machine:** clone, then run `bash .claude/sync-memory.sh` (it derives the slug from
wherever the repo sits, preserves any pre-existing memories, and is safe to re-run).
Pass `--sessions` to also link a transcript directory - off by default because session
`.jsonl` files are large and rewritten constantly, which makes for noisy diffs.

**Why:** memory is the part worth syncing; session transcripts mostly are not.
**How to apply:** after a session that adds memories, commit `.claude/memory/` along with
any other work so the other machine picks it up.
