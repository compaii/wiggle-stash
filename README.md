# Quest Book — a garden of possibilities

A separate web surface for selected public ideas, under `/questbook/` in CompAII's home. Nicolás selected this route on 2026-10-12. The book keeps capture separate from commitment and spans all life domains.

The public edition opens into an interactive particle field: a woven 3D knot, floating quest seeds, orbit gestures, pinch zoom and light ripples. Optional synthesized sound responds to deliberate interactions. Field and Pages are complementary views. Pages retains search, Seeds, In progress, What next and direct quest links.

Nicolás clarified that each quest is an exploratory space: a loose bag of notes, audio, links and discoveries around a theme. Preserve the arrival and source of each fragment, and explore the whole until it finds the shape of a project. The first two quest spaces show attributed notes drawn from the selected public conversation. The broader Quest Book and cross-harness skills observatory remain seeds. Shared writing, audio capture and attachment ingestion are still to be designed.

A possible future convergence with Nexus is retained as a field note, not a selected integration. This visual work continues independently of the source I/O goal.

Source is `public/questbook/`. The public JSON holds the same selected records shown in the interface. It contains no memory exports or private references. There is no user data capture, browser storage, authentication, reminder, scheduler, automatic observation or model activation. Shared capture, private audiences and collaboration need further product design.

Run `python3 -m http.server 8843 --bind 127.0.0.1 --directory public` and open `/questbook/` for local inspection. Publish only the selected `public/questbook/` directory through the existing daimon-home publisher. A host route maps `/questbook/` and its files to that selected artifact without extending the publisher's audience model.

The design follows the maintained Daimon Matrix palette, with a generative light weave and loosely arranged paper notes. Native WebGL shaders draw deterministic particles; no graphics framework or external service is required. Public quest controls remain labeled HTML buttons. SVG provides a reading fallback when WebGL is unavailable. Motion respects the initial reduced-motion preference and can be paused; rendering stops while the document is hidden, Pages is selected or a quest is open. Sound begins only through a deliberate user action. Space Grotesk is reused from the owning Cluster assets; its SIL Open Font License accompanies the font in the public files.

Development and publication evidence is retained in one local `operations/record.md` file. Further increments should be driven by human feedback on this experience.
