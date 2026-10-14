# Wiggle Stash — ideas in continuous creation

Wiggle Stash is the shared space; each collection is a **Wiggle bag**. Nicolás selected these names on 2026-10-12, connecting bags of developing ideas to the **Jpsh!** that gives rise to a new project or plan.

The public reading surface is https://compaii.dmn.homes/wiggle-stash/. Source is `public/wiggle-stash/`. `bags.json` contains the same selected records displayed by the notebook, under `wiggle-stash.public-edition/v1`. Fragments select a bag, note or section: `#bag/wiggle-stash/note/5`. Existing notes in this edition are attributed summaries, labeled as such.

The accepted explorer notebook provides bag selection, note navigation, search and references. Keep the shared **Star Trek / Resonancia** design direction until Nicolás selects another: a deep-space canvas, readable instrumental panels, ivory text and restrained cyan, amber and mauve accents. Maintain the useful notebook navigation. Earlier visual iterations and naming remain in Git and publication history.

## Selected direction

Capture is separate from commitment and spans all life domains. A bag contains its name and only the notes, audio, files, content and links Nicolás explicitly asks to retain or associate. Preserve original wording, provenance and arrival history. Human and AI views should expose the same complete selected input package and version.

Conversation or a future Nexus experience can consume a bag. Resulting work belongs in its chosen repositories, issues, documents, publications or other output destinations. Outputs join a bag only when explicitly associated with it.

A separate, attributed view should show CompAII’s understanding and connections. Its designed foreground traversal should record generation time, input version, consulted sources and method, preserve earlier readings, and allow regeneration on request. A cheap delta check compares input and known source versions without repeating the full traversal, distinguishing confirmed changes, potentially relevant new context and unknown coverage. Each retained reading has a dated reusable, stale or unverified cache state; tracked local copies cannot establish complete upstream freshness.

The stash should preserve the human’s ongoing intuition and continuous creation, including directions that projects only partly capture. Keep original human material distinct from CompAII’s interpretation so others can understand how the ideas developed.

Foreground capture now stores selected notes, links and original media in immutable, attributed revisions, with separate transcripts/previews and explicit coverage. The public reader consumes the same package exposed to AI readers. Existing notes remain marked as summaries. Original downloads depend on the qualified shared viewer release described in [media operations](docs/MEDIA.md).

My reading retains CompAII's foreground associations through the [v2 recipe](docs/READING-RECIPE.md): related memories, documents, bags and developments, with a brief reason and the inspected source/version, provenance and selected excerpt. Optional observations remain brief; earlier v1 readings stay in history. Public and selected-reader editions each preserve their chosen raw input; they may select different bags. A fresh human-selected one-paper bag and its first private reading also qualify that flow. Source inspection resolves to preserved evidence, complete recorded coverage remains inspectable, and each edition's AI reading history matches its complete human inventory. External references can be copied from the isolated viewer; page links retain the chosen edition and reading. A private default and audience checks preserve chosen disclosure; neither capture nor interpretation publishes automatically. The [roadmap](ROADMAP.md) keeps Nexus last. The skills observatory remains one bag stewarded by AlterMundi/Skills.

## Development and publication

My reading also offers **Only changes** against its exact selected predecessor: new connections, connection/evidence changes, text updates with before/now inspection, omitted material and changed observations, sources or aperture. The same comparison is available to AI at `raw/<bag-id>-reading-changes.json`. Reading history and raw input stay immutable. This is separate from the dated source-freshness check.

Run `python3 -m http.server 8843 --bind 127.0.0.1 --directory public` and open `/wiggle-stash/` locally. Publish the selected directory through the installed daimon-home publisher and established home route, retaining the selected audience and stable artifact identity. The receiving viewer isolates content; shared links use the stable public address.

Nicolás visits and maintains the experience through conversation with CompAII. Technical data files are not visitor controls. Source graphics are HTML/CSS/SVG, Space Grotesk is self-hosted with its SIL Open Font License, and Georgia is the journal fallback. Content transitions respect reduced motion.

One private local `operations/record.md` preserves development, validation and publication evidence.

The [original roadmap issue](https://github.com/compaii/wiggle-stash/issues/1) and seven implementation issues define the initial acceptance and dependencies. The [shared-reference extension](https://github.com/compaii/wiggle-stash/issues/9) plans reusable objects, multiple bag relationships, selected bookmark/contact imports and evidence-backed queries; see [the design](docs/OBJECTS-AND-RELATIONS.md). These importers and shared identities are not implemented yet. [Daimon Field](https://github.com/orgs/AlterMundi/projects/13) carries the coordination link and D013, while this repository owns executable implementation. See [capture operations](docs/CAPTURE.md) for the foreground mechanism and [AGENTS.md](AGENTS.md) for conversational maintenance.

Cheap foreground change checks are available separately from interpretation: see [docs/DELTA.md](docs/DELTA.md). The same dated report and per-reading cache decisions appear in the human edition and selected AI export, with explicit unknown coverage. Foreground reading access checks first and returns the unchanged interpretation; regeneration remains a separate full traversal.

Full selected-history export, independent recovery and human-selected stewardship are described in [docs/CONTINUITY.md](docs/CONTINUITY.md). Archives remain private and publication uses the existing shared access authority.
