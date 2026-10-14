# Situated reading traversal — version 1

## Comparing retained readings

The reader derives `wiggle-stash.reading-comparison/v1` from the current reading and its exact selected predecessor. This comparison never checks live sources or generates another interpretation. Stable association IDs distinguish new connections, removed connections, changed relationship/evidence and text updates. Text updates are not assumed to be semantically unimportant; they expose the exact earlier and current explanation. Changes to a referenced source version, excerpt, locator or provenance count as evidence changes even when the association wording stays the same.

My reading offers **Full reading** and **Only changes**, with counts and inspectable source bases. The focused view shows new/updated connections, folds text edits into before/now details, and reports changes to strong points, questions, uncertainty, source inventory, aperture and selected input. Removed material remains in the previous reading; raw input is untouched. Links ending in `/understanding/READING_ID/changes` retain that view.

The human and AI edition share the exact deterministic comparison in `reading_changes` and `raw/BAG_ID-reading-changes.json`. Export/restore rebuilds it from immutable history. The comparison only uses predecessors visible to the selected edition audience; an unavailable/private predecessor or a different historical recipe is explicitly reported without inventing an empty or complete comparison. The first reading has no predecessor. This is distinct from **Since my reading**, which reports the dated foreground check of input and known sources.

This is the delivered historical recipe. The human clarified the association-centered direction on 2026-10-13 in [ASSOCIATIONS.md](ASSOCIATIONS.md). The delivered v2 recipe and reader prioritize retrieved related knowledge with provenance and brief optional observations. Existing v1 readings remain intact.

This is the foreground generation recipe for issue [#4](https://github.com/compaii/wiggle-stash/issues/4), selected for implementation under Nicolás's roadmap goal. It produces an attributed reading and connection map, separate from bag input. It is a representation of CompAII's current considered understanding, rather than a complete dump of a model's internal state.

## Input and scope

1. Select one bag and its immutable revision/digest. State whether it matches the human's published edition or is a newer explicitly selected working revision.
2. Read the complete package: every selected note/link/file, its author/source, literal-versus-summary status, originals and derivative coverage. Count what was inspected and record unavailable bytes, unresolved hearing or uninspected media. Reading a summary does not establish the absent original wording.
3. Select a bounded set of relevant context sources. Start with the bag's selected references and the maintained owning project sources. Foreground HMK recall may help navigate prior relationships when authorized, but private memory is not implicitly publishable. Record each included source's stable reference, immutable version/digest, reason and inspected anchors. Record meaningful exclusions and unknown coverage. Do not import whole sessions or collect other beings' private history.

## Understanding and connections

4. Form an attributed reading: what the idea appears to be developing toward, how its parts relate, what changed in interpretation, and what remains uncertain. Preserve unresolved alternatives instead of choosing an unsupported answer. Distinguish human selection from CompAII's inference.
5. For each connection, name the target and explain the relation. Mark it as supported by inspected material, an interpretation or a possibility. Attach evidence references with source ID and locator. Support, nuance and tension can coexist. Every factual anchor must resolve to the inspected source/version; related-sounding labels alone are insufficient evidence.
6. Record open questions and conditions for further useful exploration. A question or resting idea is a useful outcome; generation does not create a project, task assignment or schedule.

## Retention and regeneration

7. Store a new immutable reading ID with generation time, author/body attribution, recipe version, input revision/digest, consulted source checkpoints, coverage/exclusions, understanding, connections and uncertainty. Apply the chosen audience to the derived record too; a public bag does not authorize publishing private contextual evidence.
8. Preserve earlier readings. On regeneration, follow this recipe again against the selected input and sources, then explain differences from the previous reading. Do not silently refresh generation dates or replace human notes. UI history and the AI-accessible edition expose the same selected reading records.

The operator mechanism persists the reading produced by the foreground daimon traversal; it does not manufacture interpretation from templates, call an unattended model or claim that storing a JSON object performed source inspection. Technical validation checks the contract and resolvable selected-entry anchors. The generating daimon remains responsible for the actual traversal and attributed judgments.

## Checkpoint and cheap delta

The checkpoint stores the selected bag revision/digest and consulted source IDs/versions, plus the discovery boundary. For an access request, `reading --bag ID` first performs the cheap foreground check and returns the retained interpretation with its dated cache decision; it does not follow this generation recipe again. A request for regeneration follows the full recipe and retains a new reading ID. Issue #5 compares those versions through supported cheap source adapters without generating another reading. It reports confirmed selected-input changes, known-source changes, potentially relevant new context and unavailable/unknown coverage separately. An unchanged tracked set never proves that nothing relevant happened elsewhere.

## Qualification on a real bag

Use an existing selected bag, inspect every factual anchor, generate its reading, then regenerate after a real selected change or an explicitly identified qualification branch. Verify preserved earlier records and unchanged input. A qualification branch must not add synthetic input to the human's actual bag or be described as human feedback. Publication and human evaluation remain distinct from technical generation evidence.

## Retained contract and operator path

`record-reading --bag <id> --file <private-draft.json> --expected-revision <n>` stores the traversal; `readings --bag <id>` retrieves its complete history. Drafts include ID, author/body, recipe version, understanding, consulted sources with version/classification/reason/anchors, connections with explained epistemic status and evidence, questions, uncertainty, coverage, exclusions and changes. A repeated identical ID returns its original record; conflicting reuse fails. A bag that changed during traversal requires regeneration or explicit historical input selection.

Each record retains an exact `input_snapshot`, so inspecting an earlier connection shows the source wording/version it actually used, even after later corrections. Sources and quoted bases remain versioned; they do not silently follow a mutable current pointer. Source excerpts are factual quotations or clearly identified locators, never invented supporting text. A public record cannot broaden a private source's audience.

The My reading view exposes current and earlier readings, dated input, supported connections, interpretations, possibilities and their inspectable basis. Stable fragments include the selected reading ID. Unknown/unselected IDs show an honest unavailable state. The AI receives the identical selected history at `raw/<bag-id>-readings.json`; raw bag input remains independently accessible.

On 2026-10-13, CompAII followed this recipe on the real Wiggle Stash revision 1. The first reading inspected all five retained summaries, the selected home link and the public definition. The second followed the continuity question into the public roadmap, adding that checkpoint, a stronger Jpsh! basis and explicit continuity/Field connections. Both readings preserve the same unchanged raw revision; neither is simulated human feedback. Factual excerpt/checkpoint verification and browser history/evidence checks are retained with the delivery evidence.

## Selected reading audience

`record-reading` defaults to the selected input's audience. Explicit `--visibility` and resolved `--recipient` or `--tribe` flags select a private reading of public input. A private input requires its identical selected reading audience, checked against the authoritative package independently of the draft's source classification. Generation never reclassifies raw input or grants new readership. Public editions omit private readings; selected private editions retain compatible interpretations.

## Association recipe v2 contract

The retained record accepts `wiggle-stash.association-recipe/v2` alongside historical v1. It keeps the same input snapshot, authorship, audience, dates and source checkpoints. Legacy `understanding` and `connections` remain empty for v2; `associations` carries the complete identified inventory and `observations` contains zero to three brief strong points.

Each association has a stable ID, original/recognizable title, kind (memory, conversation, document, bag, development or material), supported/interpretation/possibility relationship, brief `why` and inspected source/anchor evidence. Sources retain title and original provenance plus a faithful excerpt or locator for every external anchor. HMK sources use `hmk://POOL/RECORD_UID` as retrievable memory identities, not fictional public links.

`generation_reason` explains the occasion. `discovery` retains actual provider/query/date/status and limits for each search route. Empty inventory and no generated observation are valid outcomes; unavailable or limited evidence stays explicit. The generator daimon still performs the real traversal; persistence does not manufacture knowledge. Human/AI editions retain identical v2 records and independent archives retain both methods.
