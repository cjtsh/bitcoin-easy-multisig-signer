# Documentation map — which document owns which subject

> One page, no facts of its own. Every row points at the file that is the authority
> for that subject. If this page and a file disagree, **the file is right** and this
> page gets fixed.

## Four classes of writing

| Class | Files | Editable? | Read it for |
|---|---|---|---|
| **Living** — always current | `CURRENT-STATUS.md`, `README.md`, `AGENTS.md`, `CONTROLS.md`, `SIGNING.md`, `USER-MANUAL.md`, `RELEASE-PROCESS.md`, `HWI-DEPENDENCY.md`, `CHANGE-ADDRESS-REVIEW.md`, `PRIVACY.md`, `SECURITY.md`, `DISCLAIMER.md` | Yes, under the rules in `AGENTS.md` | What is true **now** |
| **Append-per-release** | `RELEASE-HISTORY.md`, `ROADMAP.md`, `PROJECT-HISTORY.md` | Append a new entry; never retro-edit an old one | How a version came to be, and what is planned |
| **Immutable evidence** | `audit-history/`, the current `*-colorteam-audit-{report,plan,lock}-*` and `-security-statement-*` set, `releases/`, `OWNER-ACCEPTANCE-*` | **No** — not even to correct a typo | What was true at one past revision |
| **Index** — points, never argues | `bitcoin-easy-multisig-signer-colorteam-findings-ledger.md`, this file | Yes, but only rows and pointers | Where to look next |

Evidence records a past revision. It is never current instruction, and it is never
edited: a correction is a new dated record.

## Who owns which subject

| Subject | Authority | Do not read for this |
|---|---|---|
| Current version, evidence, open gates | `CURRENT-STATUS.md` | `releases/` (past revisions only) |
| User-visible behaviour and supported scope | `README.md`, `USER-MANUAL.md` | `PROJECT-HISTORY.md` |
| Build, promotion and publish rules | `RELEASE-PROCESS.md` | any audit report |
| Signatures, notarization, provenance, release keys | `SIGNING.md` | `RELEASE-HISTORY.md` |
| The security controls the code claims | `CONTROLS.md` | audit reports (they describe the controls as they were) |
| BSMS/change trust boundary and the mainnet change gate | `CHANGE-ADDRESS-REVIEW.md` | `README.md` |
| Python version, device list, dependency pins and rebuild triggers | `HWI-DEPENDENCY.md` | `AGENTS.md` prose (it summarizes, it does not own the pin) |
| Status of a finding by `CT-NN` | `bitcoin-easy-multisig-signer-colorteam-findings-ledger.md`, then the report it cites | `CURRENT-STATUS.md` |
| Per-version record | `RELEASE-HISTORY.md` | `audit-history/` for feature behaviour |
| Forward plan | `ROADMAP.md` | anything phrased as a promise about the past |
| Narrative history | `PROJECT-HISTORY.md` | current status |
| Agent and tool working rules | `AGENTS.md` | `CONTRIBUTING.md` (human contribution flow) |
| Terms of use | `DISCLAIMER.md` (kept in step with `cjtsh/software-disclaimer`) | `PRIVACY.md` |
| Privacy and security reporting | `PRIVACY.md`, `SECURITY.md` | `DISCLAIMER.md` |
| Platform portability rules | `WINDOWS-PORT.md`, `LINUX-PORT.md` | `RELEASE-PROCESS.md` (build contract) |
| Version evidence per release | `releases/` | `RELEASE-HISTORY.md` (the summary index) |

## Rules of the map

1. **Links point downward only**: a living document may point at evidence, never
   paraphrase it into a second home for the same fact.
2. **One subject, one owner.** A second document may summarize; it may not be the
   place a correction lands.
3. **New subject → new row here.** If a subject has two plausible homes, the map is
   wrong until it names one.
4. **History is not deleted.** When a file moves to `docs/archive/` (a later phase),
   this map is updated in the same commit.
