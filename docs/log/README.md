# Evidence and phase-history index

[WORK_LOG.md](../../WORK_LOG.md) owns current status, approvals and the next task.
These files retain dated observations, validation and earlier decisions. Old
checkpoints, proposals, local process IDs and temporary artifact paths describe
their original sessions; they are not current instructions or deployment state.

| Evidence | Contents |
|---|---|
| [Baseline and old summary](baseline-and-old-summary.md) | Original environment, tracker, approval ledger and deviations before the work-log restructure |
| [Provider feasibility](provider-feasibility-evidence.md) | P0 evidence, accepted personal-use scope and P3 live-adapter canary |
| [P2–P4](p2-p4.md) | Persistence, durable worker, REST, real adapters and initial React implementation |
| [P4.5](p4.5.md) | Design handoff, integration, visual validation and owner acceptance |
| [Research/cache/P4.6/P4.7](research-cache-p4.6-p4.7.md) | Provider research, cache/OctoTrip integration, source chooser, observation expiry and merged PRs |
| [P4.8 interval review](p4.8.md) | Earlier concurrency-1 interval samples and initial scheduling proposal |
| [P4.8 throughput experiment](p4.8-throughput-experiment.md) | Concurrency/interval comparison, Python stress tests, failure injection and architecture assessment |
| [Latest P4.8 follow-up](p4.8-throughput-experiment.md#follow-up--requested-c31s-trials-and-swoop-retry-2026-11-11-jakarta) | Requested C3/1s trials and two successful swoop parallel retry batches; latest experimental candidates and remaining gates |
| [P4.9 scheduler](p4.9.md) | C3 scheduling implementation, performance/reliability evidence, owner merge handoff and deferred Google Flights transport issue |
| [P4.10 smart locations](p4.10.md) | Offline typed lookup, curated Major coverage, scope validation, tests and UI evidence |
| [Swoop transport follow-up](swoop-transport.md) | Current-main/Fli evaluation and explicit Google traffic-check blocker; fare retrieval unresolved |
| [P4.11 Fli provider](p4.11.md) | Merged PR #5 (`4c98386`); fourth-source integration, C3/1s verification, HTTP/2 trials, usable API/UI quotes and owner acceptance |
| [P4.12 shared global pool](p4.12.md) | Per-provider cap removal, admission review, P4.9-vs-P4.12 synthetic benchmark, G100 profile, risks and owner decisions |
| [P5.05 native iOS feasibility](p5.05.md) | Provider GO/NO-GO for standalone iOS, engine port invariants, iOS lifecycle limits, Rust-vs-Swift shared-core ADR and spike plan (analysis only, nothing run) |
| [P5.06 native engine spikes](p5.06.md) | S1 Fli on iPad via URLSession 3/3 PASS, S2 wreq iOS build, S3 macOS 3/3 PASS, S4 Rust money via PyO3 parity; S5 on hold |

## Reporting convention

Keep WORK_LOG.md under about 80 lines; latest checkpoint has at most five short bullets with
an evidence pointer. Append long reports to the relevant file here. Preserve
historical measurements and label later corrections/follow-ups explicitly.
At phase close, leave one tracker row and replace the current checkpoint/next task.

No raw provider payloads, booking selectors, tokens or credentials belong here.
Code, contracts, redacted fixtures and screenshots may live in their existing
artifact directories. Experimental settings remain proposals until separately
approved for implementation and rollout.

## Documentation publication — 2026-11-11

- Owner requested the experiment push first, then documentation cleanup and a
  second push. Experiment scripts, sanitized evidence and the owner's work-log
  restructuring were published as
  [0c93892](https://github.com/farhaniqbalta/CheapWings/commit/0c93892).
- Cleanup corrects current runbook statements for HTTP 200 expired metadata,
  independent observation/job budgets, the web source chooser, admission quotas
  and existing provider timing defaults. Benchmark proposals remain unapproved.
- Agent instructions and the initialization template now preserve completed
  phases and the compact work-log rules. Moved links are repaired, archived
  recommendations are labeled historical, and numerical experiment evidence is
  retained. The original V4 reference is unchanged.
- Validation: local Markdown paths and heading anchors checked, compact work-log
  size checked, and whitespace diff checks passed. This documentation-only change
  needs no new provider traffic or application rollout; no production code changed.
