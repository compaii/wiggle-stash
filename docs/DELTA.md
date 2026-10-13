# Foreground delta checks

A delta check compares a retained reading checkpoint with the current selected bag. It never performs the reading recipe or regenerates an interpretation. Ask for it in conversation; the operator uses `delta --bag ID` (latest reading), optionally `--reading ID`, `--skip-sources` or `--discovery-limit 0..128`.

Added, corrected and retired entries retain stable IDs. Other package changes, including derivative corrections, still change the package digest even when no entry ID changed. `retire` requires explicit human selection, a reason, source, operation ID and expected revision; earlier revisions keep the original.

Known external sources are checked only through explicitly registered cheap adapters. `register-source --bag ID --id SOURCE --uri CHECKPOINT_URI --file LOCAL_COPY --visibility public` binds a consulted source to its maintained local copy. The URI identifies the reading's original checkpoint; the local file is the current version of that source. SHA-256 comparison streams bytes without semantic reading. A different URI, unsupported adapter, missing file or incompatible audience yields unavailable/unknown, never unchanged. The source binding remains private and is not included in public reports. Registration defaults to human-only. An immutable checkpoint URI does not mean the checked local copy is that old remote revision: remote state is not fetched or claimed.

The same scoped registration index supplies bounded candidate discovery: registered sources not consulted in the reading are potential context, not established connections. Incompatible candidates are omitted. Report truncation and unknown coverage outside this index. There is no global memory, conversation or network watcher.

Each successful check is immutable, dated and audience-scoped. It records input/source checkpoints, known changes, candidates, unavailable checks and inspected-byte/candidate counts. The human edition and `raw/<bag>-delta.json` contain the identical selected report. A check predating the displayed bag version is marked stale. A new reading remains a separate conversational request.

Qualification covers unchanged/changed input, correction and explicit retirement, changed known source, missing/unselected source, private rebinding, changed source identity, invalid bounds, and candidate truncation. Current adapter cost is proportional to selected file bytes, not model tokens; no model traversal occurs.
