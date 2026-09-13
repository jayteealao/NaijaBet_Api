<!-- sdlc:wf-rules v1 START - managed by sdlc-workflow; edit outside this fence -->
## Working in this repo (sdlc-workflow)

- `/wf` is the lifecycle entry point. Workflow artifacts live under `.ai/`; treat rendered or
  generated output as read-only — regenerate, don't hand-edit.
- Ground facts in real source instead of guessing: reach for **study-sources** before asserting
  how a library, framework, SDK, or API actually behaves.
- Durable per-workflow constraints (vetoes, preferences) go in `.ai/workflows/<slug>/steer.md`.
<!-- sdlc:wf-rules v1 END -->
