# Wiggle Stash operator instructions

Read README.md, ROADMAP.md and the owning issue before changes. Reuse the current checkout and Python standard-library store. The repository owns implementation; the linked Daimon Field decision owns cross-project coordination.

Humans maintain bags by conversation. Do not add code editors, command forms or selected-files controls to their reading surface. Preserve the selected Star Trek / Resonancia direction and useful navigation.

Capture only material the human explicitly selects. Ordinary conversation or a related project does not automatically enter a bag. Require the intended bag ID; use `python3 -m wiggle_stash list` to resolve the human's name, and clarify ambiguity instead of choosing silently. Keep exact bytes/wording and author/source attribution. Mark a supplied summary as `summary`; an assistant interpretation is a future separate reading, not a human original.

The supported foreground commands are `create`, `capture`, `correct`, `attach`, `annotate`, `record-reading`, `readings`, `reading`, `prepare-visit`, `retain-visit`, `visits`, `archive`, `restore`, `custody`, `delta`, `register-source`, `retire`, `show`, `list`, `import-edition` and `export-edition`. Consult `--help`, docs/MEDIA.md and docs/READING-RECIPE.md. A selected message/material gives an operation its stable ID; retries reuse that ID. Read the current version before mutation and supply `--expected-revision`. Reconcile conflicts rather than silently overwriting another writer. A correction preserves entry ID and original capture time; earlier wording remains retrievable by revision.

Storage is private by default. The store binding comes from `--store` or `WIGGLE_STASH_STORE`, otherwise the local user's data directory. Never commit the live store, private packages, scratch notes, credentials or operational receipts. `public/wiggle-stash` contains only explicitly selected public edition assets. Public generation rejects non-public bags. Private generation requires the identical selected audience and an owner-only output directory; follow docs/CONTINUITY.md and publish with that same scope. Generation grants no access and publishes nothing itself.

For ordinary contents questions, retrieve the package matching the edition the human is looking at. `public/wiggle-stash/raw/<id>.json` is the exact package embedded in the current reading edition. A newer canonical revision may be pending publication: say so and explicitly select that revision before working from it. Do not describe an unpublished revision as the human's current web view. Foreground capture can be followed by selected generation/publication using the established home publisher and unchanged audience. Verify served bytes before claiming delivery.

Before future generated readings or Nexus adapters, follow their owning issues. This workflow adds no scheduler, inbox listener, memory watcher, private-session ingestion or autonomous peer reply.

For a request to access your retained reading, use `reading --bag ID` (or the explicitly selected `--reading ID`) first: it performs only the cheap foreground check and returns the unchanged reading plus its dated reuse/stale/unverified state. Disclose coverage limits and candidates. Regenerate only when requested under the selected task; never silently change a date or interpretation.

For a generation or regeneration request, actually follow docs/READING-RECIPE.md: inspect the selected package and bounded relevant sources, then write your considered interpretation with evidenced connections and uncertainty to a private draft. `record-reading` retains that traversal with immutable input/source checkpoints and an exact input snapshot. Never substitute a template for the actual traversal. Regeneration uses a new ID and explicit changes, retaining earlier readings. Non-public contextual evidence requires a compatible private reading audience; public generation omits private readings. Published AI reading history is `raw/<id>-readings.json`, identical to the human edition. An explicitly chosen historical input requires `--allow-historical-input`; never silently use a newer version than the human selected.

Qualification: `python3 -m unittest discover -s tests -v`; `node --check public/wiggle-stash/app.js`; check the affected browser behavior and human/AI package parity after publication.

For a delta request, follow docs/DELTA.md. Bind only explicitly scoped source copies and preserve their classification. Report known changes, potential candidates and unknown coverage separately; do not imply a checked local copy proves remote freshness. Delta does not authorize a new reading.

Follow docs/CONTINUITY.md for recovery and access. Consult the current custody policy before creating private bags or sharing copies. Archive export is private and creates no grant; preserve originals and use a new destination for restore.

For optional Nexus work, follow docs/NEXUS.md and the receiving maintained contract. Distinguish prepared package, imported encounter, observed exploration and actual human/native reply. Retain outputs separately; a recorded Jpsh! performs no external action and never adds output to input implicitly.

Delivery priority: complete standalone capture, original media, genuine readings with cached-reading freshness, continuity/access and the accepted design before returning to Nexus. Preserve existing Nexus preparation; finish its acceptance last.
