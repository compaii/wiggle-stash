# Quest Book — first public edition

A separate web surface for selected public ideas, under `/questbook/` in CompAII's home. Nicolás selected this route on 2026-10-12. The book keeps capture separate from commitment and spans all life domains.

This first edition supports Seeds, In progress and What next views, search, attributed quest details, references and shareable quest links. Two retained public seeds ground the experience: the Quest Book and the cross-harness skills observatory. Both remain seeds. This is an exploratory public edition, not a shared writable application.

Source is `public/questbook/`. The public JSON holds the same selected records shown in the interface. It contains no memory exports or private references. There is no user data capture, browser storage, authentication, reminder, scheduler, automatic observation or model activation. Shared capture, private audiences and collaboration need further product design.

Run `python3 -m http.server 8843 --bind 127.0.0.1 --directory public` and open `/questbook/` for local inspection. Publish only the selected `public/questbook/` directory through the existing daimon-home publisher. A host route maps `/questbook/` and its files to that selected artifact without extending the publisher's audience model.

The design follows the maintained Daimon Matrix palette, with a seed and orbital motif. Space Grotesk is reused from the owning Cluster assets; its SIL Open Font License accompanies the font in the public files.

Development and publication evidence is retained in one local `operations/record.md` file. Further increments should be driven by human feedback on this experience.
