# Selected original media and derived evidence

Issue [#3](https://github.com/compaii/wiggle-stash/issues/3) extends the foreground capture loop. Original files/audio enter a bag only when explicitly selected. There is no network scraper or automatic transcription job.

## Original bytes

`attach` preserves a regular source file as a content-addressed immutable object, with SHA-256, byte count, supplied/detected media type, original filename, author/source and capture time. The default original limit is **256 MiB per operation**, configurable through `--max-bytes` for a deliberate larger capture. Partial copies are discarded on limit failure. Existing same-digest objects are verified before reuse; missing or changed originals fail generation instead of publishing a misleading inventory.

```sh
python3 -m wiggle_stash attach --bag example --entry recording-one --title 'Selected recording' --author 'Human author' --source 'selected source reference' --file recording.wav --operation-id selected-recording-one --expected-revision 2
```

Links remain selected URLs without scraping. A separately selected snapshot can use `attach --snapshot-of <HTTP(S)-URL>` after the source bytes have been explicitly fetched through an appropriate authorized tool. Snapshot source and capture time are retained independently of the live URL.

## Transcripts and previews

`annotate` stores a transcript or preview separately from original input, bound to the original entry and its exact digest. It records authored provenance, creation time, explicit received/processed coverage, review status and uncertainty. Updating an annotation creates a new bag revision; earlier derivatives and the unchanged original remain retrievable. Later note capture also preserves those annotations.

```sh
python3 -m wiggle_stash annotate --bag example --entry recording-one --annotation transcript-one --author 'Attributed transcriber' --source 'reviewed transcription job reference' --file transcript.txt --coverage-file coverage.json --operation-id selected-transcript-one --expected-revision 3
```

Coverage requires `review` (`unreviewed`, `samples-reviewed` or `fully-reviewed`), `received`, `processed` and an explicit `uncertainty` list. Received/processed values may be descriptions or structured coverage including measured seconds/intervals. Unknown, missing or unresolved material stays explicit. These are attributed processing statements, not inferred proof that every word was heard.

Reuse the installed audio-transcription workflow for real recordings: probe streams and decode health, retain originals and raw provider results, review seams/uncertainty and preserve actual timestamp alignment. This store consumes explicitly selected outputs; it neither chooses a provider nor sends audio to one. Provider processing never grants publication.

## Shared inventory and byte delivery

The human edition and its AI package contain the same original inventory and derivative references. Generation verifies every referenced object, then copies only selected bytes under `media/<digest>.<safe-type-extension>`. Unknown/active formats use `.bin`; original names stay in metadata. Originals are not converted or overwritten to create previews. Omitted media are removed from the next generated edition, while store/publisher history remains.

The Materials view plays original audio/video, shows safe image formats and opens attributed transcripts with their review/coverage state. Downloads use the trusted home parent's manifest of files from the **same exact resource and version**. The child keeps `sandbox="allow-scripts"`; no credentials, owner operation, different resource or current pointer can be selected by a message. An older viewer that lacks this capability leaves download controls unavailable.

The receiving home authority enforces actual metadata and byte access. Non-public bags are refused by public generation; chosen private audiences require their supported home adapter instead of a visibility downgrade. Media and private derivatives stay outside source commits unless independently selected for public source distribution.

## Evidence and remaining qualification

Behavioral tests cover exact WAV-byte retention, restart/retry, transcript corrections with earlier retrieval, lost/corrupt object rejection, limits, explicit snapshot source and private/public separation. A loopback browser fixture verifies playback, transcript loading, original download/digest and mobile layout through an opaque sandbox. Its synthetic silence is explicitly identified; it is not a human recording or a source-quality benchmark.

The shared viewer dependency is [Cluster #216](https://github.com/nicoechaniz/daimon-cluster/pull/216). Its CI, merge and live deployment are separate from the local fixture evidence. Portable history/restore is qualified under #7; a real human recording is handled only when selected, never substituted with this fixture.
