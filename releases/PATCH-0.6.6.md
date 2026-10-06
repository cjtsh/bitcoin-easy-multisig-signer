# 0.6.6: Color Team cycle-2 remediation

Version 0.6.6 answers the cycle-2 Color Team audit of the 0.6.5 tree
(report in the repository root). That cycle graded CONDITIONAL: three of the
four Mediums were release-channel findings and the fourth was an unpinned
BIP-143 digest. The Lows were either unpinned money-path controls or
deferred design items. This release fixes them in code and pins every fix
with a test demonstrated able to fail.

## Release-channel hygiene (Mediums)

- CT-27: the out-of-gate `v0.6.5-windows-x64` release and tag are deleted.
  It carried same-named different-byte Windows assets from a retired
  workflow. CT-01/CT-02: the manually uploaded Windows and Linux assets on
  the `v0.6.4` page are deleted and the page carries a supersession banner.
  There is now exactly one `SHA256SUMS` covering every platform.
- CT-26: `tests/test_bip143_vectors.py` pins published BIP-143 P2WPKH and
  P2WSH digests and recomputes them without the library under test. A
  digest substitution in embit now fails the suite.

## Money-path and tooling pins (Lows)

- CT-28/CT-31/CT-32: `tests/test_money_path_pins.py` pins the full-xpub
  device-identity comparison, the outputs≤inputs gate, the 2–3-key
  sign-time scope, the BIP-141 vsize formula, the broadcast hex/size gates,
  and the build-time prevout/ownership binding.
- CT-29: source-mode HWI resolves the interpreter-sibling helper first and
  refuses any helper that does not identify as HWI 3.2.0 before it sees an
  account xpub or PSBT.
- CT-17: runner images are `ubuntu-24.04`, `windows-2022`, `macos-15` —
  never a `-latest` alias.
- CT-33: both lock-generation jobs pin `pip-tools==7.6.1`.
- CT-34: imported signatures must be BIP-62 low-S. The gate parses DER
  itself so a backend that accepts high-S cannot reach finalisation.
- CT-30: a lying-low BTC/USD quote cannot suppress the large-amount prompt.
  The prompt also fires at 4,000,000 sats (0.04 BTC), the amount $10,000
  reaches at a conservative $250,000 BTC/USD ceiling no feed can push
  higher.
- CT-43: a saved PSBT that carries verified signatures is named `-signed`,
  not `-unsigned`.
- CT-45: README-LINUX points at the one `SHA256SUMS` and `BUILD-SBOM.json`
  the release actually ships.
- CT-46: this tree names its own revision. Stale "current published
  version" strings are findings; `version.py`, `AGENTS.md`, release notes
  and user-facing references move together.

## Deferred design items now fixed (Lows)

- CT-13: explorer pre-checks (selected outpoints, Esplora genesis) run
  outside the session lock. Only the irreversible submit holds it, so a
  slow explorer cannot stall the owner's UI, while a concurrent refresh
  still cannot swap the payment mid-send.
- CT-14: before any PSBT is sent, the device must sign a fresh random
  challenge and the signature is verified against the wallet's known
  public key. Echoing an account xpub is no longer enough to receive the
  payment. This adds one on-device message-signing step to every signing
  attempt and needs an owner practice-network hardware walkthrough before
  publication (already required when app behavior changes).

## Process

`RELEASE-PROCESS.md` §5 and the matching `AGENTS.md` invariant memorialise
the cycle-2 lessons so 0.7.0 inherits them: a test that cannot fail does
not count as a fix; external oracles catch what shared code cannot;
release-channel hygiene is part of the release; pin what used to float;
stale version strings are findings; the audit ledger is the backlog.

The wallet, transaction, signing and broadcast engine changes above are
safety hardening only. No new payment capability is added. Owner
practice-network hardware walkthrough is required before publication
because signing now includes a key-proof step and the large-amount prompt
fires earlier for amounts between 0.04 and 0.1 BTC.

## Publication

Build only through `.github/workflows/build-candidate.yml` (candidate
`publish=false`, then promote `publish=true` with that candidate's run ID).
Record both run URLs and the commit SHA here after publication. Never
publish by hand.
