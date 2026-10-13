# Foreground delta checks

A delta check compares a retained reading checkpoint with the current selected bag. It never performs the reading recipe or regenerates an interpretation. Ask for it in conversation; the operator uses `delta --bag ID` (latest reading), optionally `--reading ID`, `--skip-sources` or `--discovery-limit 0..128`.

Added, corrected and retired entries retain stable IDs. Other package changes, including derivative corrections, still change the package digest even when no entry ID changed. `retire` requires explicit human selection, a reason, source, operation ID and expected revision; earlier revisions keep the original.

Known external sources are checked only through explicitly registered cheap adapters. `register-source --bag ID --id SOURCE --uri CHECKPOINT_URI --file LOCAL_COPY --visibility public` binds a consulted source to its maintained local copy. The URI identifies the reading's original checkpoint; the local file is the current version of that source. SHA-256 comparison streams bytes without semantic reading. A different URI, unsupported adapter, missing file or incompatible audience yields unavailable/unknown, never unchanged. The source binding remains private and is not included in public reports. Registration defaults to human-only; selected individual/tribe sources require the same explicit resolved targets with `--recipient` or `--tribe`. An immutable checkpoint URI does not mean the checked local copy is that old remote revision: remote state is not fetched or claimed.

The same scoped registration index supplies bounded candidate discovery: registered sources not consulted in the reading are potential context, not established connections. Incompatible candidates are omitted. Report truncation and unknown coverage outside this index. There is no global memory, conversation or network watcher.

Each successful check is immutable, dated and audience-scoped. It records input/source checkpoints, known changes, candidates, unavailable checks and inspected-byte/candidate counts. The human edition and `raw/<bag>-delta.json` contain the identical selected report. A check predating the displayed bag version is marked stale. A new reading remains a separate conversational request.

Qualification covers unchanged/changed input, correction and explicit retirement, changed known source, missing/unselected source, private rebinding, changed source identity, invalid bounds, and candidate truncation. Current adapter cost is proportional to selected file bytes, not model tokens; no model traversal occurs.

## Reading cache decisions

`reading --bag ID` checks the selected latest retained reading's input and sources before returning that unchanged interpretation. `--reading ID` explicitly selects history. The response includes the reading, the exact delta and `wiggle-stash.reading-state/v1`; it performs no model traversal. This foreground access neither publishes nor regenerates.

- `reusable`: selected input and all consulted registered local copies were unchanged at the matching check. This is bounded reuse, not global freshness.
- `stale`: selected input or a known source copy changed. The interpretation remains retrievable with its original generation date.
- `unverified`: a matching check is absent, predates the selected input version, or a consulted source is unavailable/unchecked. A confirmed change takes precedence while unavailable sources remain explicit.

Potential new context and truncated discovery are separate reasons to consider revisiting. Outside-index context and unqueried upstream state remain unknown in every state. A public edition can show only public checkpoints; a private reading on public input checks within its own selected audience.

Generation reconstructs a state for each retained reading from that reading's latest compatible check, without touching source files. An old check is never silently refreshed and another reading's check is never reused. My reading shows the same dated state provided in `raw/<bag>-reading-states.json`. Publication remains selected foreground work; the web page performs no background checking.
