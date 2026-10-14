# Shared objects, selected relationships and useful recall

Nicolás requested this extension on 2026-10-14: preserve heterogeneous references, recover useful bookmarks from selected group archives/accounts/address books, and reuse one object across multiple Wiggle bags. This is a new roadmap, not implemented functionality or authorization to ingest accounts now. The earlier standalone capture/readings remain delivered; the native goal remains paused. Nexus stays deferred.

## Current behavior and verified gap

The store currently retains notes, HTTP(S) links and original attachments as entries within immutable bag revisions. Originals are content-addressed, so identical attachment bytes already share storage. Transcripts and previews have separate attributed coverage. Readings retain versioned contextual sources and associations separately from human input.

There is no first-class shared identity for a video, person, channel, paper or repository, no versioned many-to-many bag membership, and no Telegram/X/address-book importer. Capturing the same URL in two bags currently creates two entries. A person without a URL can be retained as a literal note; structured identity/contact relationships are new work. A saved URL does not mean its contents have been inspected.

## Object, occurrence, relationship and representation

An **object** identifies the referred thing, with a stable local ID and attributed external identifiers/aliases. Extensible types include content (paper, audio, video, post, document), people, organizations, channels/accounts, repositories, events and otherwise unclassified references. A YouTube channel is distinct from each video; a person is distinct from their account/channel and private contact details. A source/channel selection does not silently subscribe to all future material.

An **occurrence** preserves how it reached us: an exact selected message/bookmark/address-book record, its author, source account/chat identity, source date, import date, locator, selection context and original bytes where available. Repeated recommendations remain distinct occurrences of one object. Their comments may explain its importance even when the external page disappears.

A **relationship** records subject, predicate, target, brief reason, attribution, supporting occurrence/evidence, date, audience and status. Predicates are extensible: linked to a bag, authored by, published through, discusses, contradicts, develops, possible coverage interest, introduction through another person. Human-selected links and assistant-proposed interpretations remain distinguishable. A proposal joins a bag's raw input only by explicit selection or a deliberately chosen bounded import policy. An imported corpus can remain available for requested searches without assigning every item to a bag.

A **representation** is a versioned page snapshot, original file, excerpt, transcript or preview. Keep URL identity, exact versions and inspection coverage distinct. A DOI can identify a paper while a preprint and published edition remain distinct versions. A repository has separate branches/commits/artifacts. A YouTube timestamp belongs to the selected locator, not to video identity.

No graph database is assumed. Extend the current supported SQLite/store APIs after inspecting their contracts. Stable object identity must not rewrite historical bag packages or readings; selected packages pin object/relationship revisions, exposing the same resolved evidence to humans and AI.

## Identity, history and selected disclosure

Normalize known platform IDs/DOIs conservatively, retain original URLs and aliases, and avoid destructive URL parameter removal. Equal bytes mean equal bytes, not proof of equal authorship/context. Never merge people on names alone. Uncertain matches stay separate candidates; reviewed merge/split and relation corrections retain history and old identifiers.

Shared identity grants no access. Keep each occurrence, relationship, representation and contact field within its selected audience. A public video can have private recommendations; a public person profile can have a restricted phone number. A bag edition only resolves accessible material and must not reveal hidden bag membership, source titles, relationship counts or contact existence. Combining editions does not union their grants. Removal/correction of a relation is independent of deleting the shared object or another bag's relation; support explicit removal of imported private source data and derived indexes with a clear account of retained histories/backups.

## Imports and useful queries

All first connectors are finite, human-directed imports. Select source/account, time or item bounds, audience and destination policy. Use stable origin IDs and import receipts so retries/resumption do not duplicate objects, occurrences or relations. Preserve edited/deleted/unavailable source states and exact omissions. Preview proposed bag assignments; allow a chosen policy to accept a bounded batch without repeated per-item approval. Never transfer the source's entire audience implicitly into the stash.

For a Telegram group archive, retain chosen bookmark messages and sufficient selected reply/context to understand their reasons, not every surrounding conversation by default. Telegram Desktop provides JSON/HTML chat exports: [official export description](https://telegram.org/blog/export-and-more). An actual AlterMundi source/account/export and selection rule remain to choose. Do not confuse this with the Matrix Tribe inbox or inspect either merely to create this roadmap.

For X, import bookmarks using each account holder's authorized read access. The [official bookmark documentation](https://docs.x.com/x-api/posts/bookmarks/introduction) describes private user bookmarks and user authentication; the [lookup endpoint](https://docs.x.com/x-api/users/get-bookmarks) provides pagination. Actual account/API availability, access conditions and cost must be verified before selecting a connector. Do not assume an account archive contains all bookmarks. A supplied export or explicitly authorized browser extraction can be assessed as alternatives, with their actual coverage retained; no login, scraping or subscription is started here.

For contacts, start with selected vCard/CSV records or an authorized provider adapter. [Google People API](https://developers.google.com/people/api/rest/v1/people.connections/list) supports read-only contacts and paged/incremental results; Google is an option, not the selected address-book provider. Separate a person from contact methods, preserve ownership, keep unknown identity/contact facts unknown, and never infer a working communication route from a name or public handle alone.

Retrieved content needs a separate inspected state. A title/description can aid navigation; claims about the content need inspected originals or attributed derivatives with coverage. Reuse existing media/transcription and reading/source-check machinery rather than silently downloading/transcribing every external channel.

A requested query such as 'Who might cover this topic?' searches the chosen accessible bags and imported source corpus, traversing documented links through content, creators, people and channels. Return candidates with specific reasons/evidence, known contact or introduction route if accessible, uncertainties, corpus bounds and last inspection dates. Observed subject coverage differs from our inference of potential interest and from confirmed interest. A bookmark is not endorsement. No outreach follows from retrieval.

Readings can incorporate inspected imported sources and proposed cross-bag relationships. Cheap checks compare pinned object/relationship/representation revisions plus bounded source discovery; corrected identities or changed reasons can stale a reading without new bytes. Existing reading diffs remain distinct from source freshness. No observer, recurring generation or automatic publication is selected.

## Implementation sequence

The [extension umbrella #9](https://github.com/compaii/wiggle-stash/issues/9) retains the implementation checklist.

1. [#10](https://github.com/compaii/wiggle-stash/issues/10): versioned shared objects, occurrences and relationships; compatible bag selection, identity corrections and audience boundaries.
2. [#11](https://github.com/compaii/wiggle-stash/issues/11): finite import pipeline and selected Telegram bookmark archives, with exact provenance, resumable retries and explicit inclusion policy.
3. [#12](https://github.com/compaii/wiggle-stash/issues/12): people/contact identity and a selected address-book import route, including people without contact details.
4. [#13](https://github.com/compaii/wiggle-stash/issues/13): X bookmarks through verified per-account access; preserve account attribution and pagination/coverage limits.
5. [#14](https://github.com/compaii/wiggle-stash/issues/14): evidence-backed conversational retrieval and readings, including the prospective-coverage query and cheap object/relation delta.
6. [#15](https://github.com/compaii/wiggle-stash/issues/15): Resonancia navigation for shared objects and cross-bag bridges, identical human/AI projections, independent recovery and end-to-end qualification.

The smallest useful increment is one object selected into two bags with independent reasons and exact history, then a small human-selected bookmark batch. Importers share the core pipeline; contacts/X can proceed independently after identity/import contracts exist. Retrieval begins with the available corpus rather than waiting for every connector. Qualify with synthetic fixtures first and a selected real source second, without treating synthetic data as human bookmarks or inspected sources. Nexus is not a dependency.

## Acceptance example

Retain a selected video once, with two chosen bag relationships and their different reasons; preserve two independent recommending messages as occurrences. Connect its attributed creator/channel to a distinct person record, with a restricted contact method if selected. A question about possible coverage returns a sourced candidate and honest uncertainty. Public and private editions show only their authorized portions, including no hidden cross-bag clues. A repeated import adds no duplicates; corrections preserve previous packages/readings, and independent recovery reproduces the exact selected human/AI package and comparison.
