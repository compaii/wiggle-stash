# Foreground capture and shared editions

The first increment uses a local SQLite store and Python's standard library. No service, dependency environment, form or background process is needed. CompAII uses the operator commands under a human request; the human visits the existing reading surface and maintains it through conversation.

## Storage and revision contract

`python3 -m wiggle_stash --help` lists supported operations. Select a receiving store with `--store` or `WIGGLE_STASH_STORE`; by default it lives in the local user's data directory. Bag input is private unless a chosen audience says otherwise. SQLite transactions serialize writers. A stable operation ID makes exact retries return the original operation result; conflicting reuse fails. Expected-revision checks reject stale input.

Every successful write creates a new immutable revision. `show --bag <id> --revision <n>` retrieves earlier wording. Corrections preserve entry identity and original capture time, recording correction time separately. A canonical SHA-256 digest covers the bag, complete entry list and separately identified legacy presentation metadata. The wrapper adds revision and commit time.

The `wiggle-stash.bag/v1` package contains:

- `bag`: stable ID, name and selected audience/targets.
- `entries`: exact notes or selected links, stable IDs, original author, source reference/date, capture time and `literal`/`summary` representation.
- `presentation`: separately identified earlier display context, retained without claiming it is raw human input.
- `version`: revision, digest and creation time.

## Example operator loop

Write the human's selected exact UTF-8 text to a private scratch file. Do not interpolate a note through shell code. Choose a stable operation ID from the selected source message and entry; reuse it on retries.

```sh
python3 -m wiggle_stash create --bag example --title 'Example ideas' --operation-id example-create
python3 -m wiggle_stash capture --bag example --entry note-one --title 'A selected note' --author 'Human author' --source 'selected message reference' --text-file selected-note.txt --operation-id example-note-one --expected-revision 1
python3 -m wiggle_stash show --bag example
```

The default example is human-only. To capture a link, use `--url` instead of `--text-file`; the target is preserved without fetching it. `correct` uses the same selected entry ID and a new operation ID. `--source-date` retains a source date when known. An existing summary must be explicitly marked `--representation summary`.

## Public edition

`import-edition` migrates the original selected edition without inventing literal originals: every existing note remains an attributed summary. The original source date and display context are retained. Migration uses an operation prefix and stable entry IDs.

```sh
python3 -m wiggle_stash export-edition --bag wiggle-stash --bag skills-observatory --output public/wiggle-stash
```

Only explicitly selected public bags may enter this edition. `bags.json` embeds each full package; `raw/<bag-id>.json` contains the identical object. The reader derives its notes/links from that embedded package and shows the edition date/revision. Technical file controls do not appear in the visitor UI. The AI can retrieve the matching standalone package through the existing home artifact endpoint, preserving the same audience enforcement. A newer canonical revision and a published edition are distinct until selected publication succeeds.

Generation changes only selected data files and never publishes. Use the installed daimon-home publisher for `public/wiggle-stash` under the existing `wiggle-stash` artifact ID and selected public audience, retaining resource identity/history. Verify the served edition, raw package bytes and affected reader behavior. The source repository and current public edition are backed by Git/publisher history; full live-store recovery/portability qualification remains #7.

## Qualification and remaining scope

Tests verify exact Unicode/line-ending retention, persistent retrieval, idempotent retry after later writes, stale concurrent writers, preserved corrections, immutable revisions, source-summary migration, unsafe link rejection, private default/public refusal and package parity. Browser checks qualify deep links, search, literal/summary labels, edition state and mobile navigation.

The CLI is a foreground operator mechanism, not an automatic chat interceptor. Files/audio, generated readings, cheap delta and Nexus handoff are separate issues. No AI-memory import or cross-being pooling is introduced.
