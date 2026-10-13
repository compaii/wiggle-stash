# Situated reading traversal — version 1

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

The checkpoint stores the selected bag revision/digest and consulted source IDs/versions, plus the discovery boundary. Issue #5 compares those versions through supported cheap source adapters without generating another reading. It reports confirmed selected-input changes, known-source changes, potentially relevant new context and unavailable/unknown coverage separately. An unchanged tracked set never proves that nothing relevant happened elsewhere.

## Qualification on a real bag

Use an existing selected bag, inspect every factual anchor, generate its reading, then regenerate after a real selected change or an explicitly identified qualification branch. Verify preserved earlier records and unchanged input. A qualification branch must not add synthetic input to the human's actual bag or be described as human feedback. Publication and human evaluation remain distinct from technical generation evidence.
