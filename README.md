# Wiggle Stash — ideas in continuous creation

Wiggle Stash is the shared space; each collection is a **Wiggle bag**. Nicolás selected these names on 2026-10-12, connecting bags of developing ideas to the **Jpsh!** that gives rise to a new project or plan.

The public reading surface is https://compaii.dmn.homes/wiggle-stash/. Source is `public/wiggle-stash/`. `bags.json` contains the same selected records displayed by the notebook, under `wiggle-stash.public-edition/v1`. Fragments select a bag, note or section: `#bag/wiggle-stash/note/5`. Existing notes in this edition are attributed summaries, labeled as such.

The accepted explorer notebook provides bag selection, note navigation, search and references. Keep the shared **Star Trek / Resonancia** design direction until Nicolás selects another: a deep-space canvas, readable instrumental panels, ivory text and restrained cyan, amber and mauve accents. Maintain the useful notebook navigation. Earlier visual iterations and naming remain in Git and publication history.

## Selected direction

Capture is separate from commitment and spans all life domains. A bag contains its name and only the notes, audio, files, content and links Nicolás explicitly asks to retain or associate. Preserve original wording, provenance and arrival history. Human and AI views should expose the same complete selected input package and version.

Conversation or a future Nexus experience can consume a bag. Resulting work belongs in its chosen repositories, issues, documents, publications or other output destinations. Outputs join a bag only when explicitly associated with it.

A separate, attributed view should show CompAII’s understanding and connections. Its designed foreground traversal should record generation time, input version, consulted sources and method, preserve earlier readings, and allow regeneration on request. A cheap delta check should compare input and known source versions without repeating the full traversal, distinguishing confirmed changes, potentially relevant new context and unknown coverage.

The stash should preserve the human’s ongoing intuition and continuous creation, including directions that projects only partly capture. Keep original human material distinct from CompAII’s interpretation so others can understand how the ideas developed.

The first foreground capture increment now stores selected text notes and links in immutable, attributed revisions. The public reader consumes the same package exposed to AI readers, with matching revision/digest. Existing notes migrated as summaries, retaining that distinction. A private default and public-generation checks preserve chosen disclosure; capture does not publish automatically. Files/audio, generated readings, delta, qualified portability and Nexus integration remain in the [roadmap](ROADMAP.md). The skills observatory is one bag stewarded by AlterMundi/Skills, rather than an owner of the general space.

## Development and publication

Run `python3 -m http.server 8843 --bind 127.0.0.1 --directory public` and open `/wiggle-stash/` locally. Publish the selected directory through the installed daimon-home publisher and established home route, retaining the selected audience and stable artifact identity. The receiving viewer isolates content; shared links use the stable public address.

Nicolás visits and maintains the experience through conversation with CompAII. Technical data files are not visitor controls. Source graphics are HTML/CSS/SVG, Space Grotesk is self-hosted with its SIL Open Font License, and Georgia is the journal fallback. Content transitions respect reduced motion.

One private local `operations/record.md` preserves development, validation and publication evidence.

The [roadmap issue](https://github.com/compaii/wiggle-stash/issues/1) and seven implementation issues define acceptance and dependencies. [Daimon Field](https://github.com/orgs/AlterMundi/projects/13) carries the coordination link and D013, while this repository owns executable implementation. See [capture operations](docs/CAPTURE.md) for the foreground mechanism and [AGENTS.md](AGENTS.md) for conversational maintenance.
