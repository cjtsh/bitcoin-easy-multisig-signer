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
  The proof is taken at the first receive path under the wallet origin
  (`…/0/0`), not the all-hardened BIP48 account node. Trezor Safe 3 and
  OneKey (Trezor firmware) answer `forbidden key path` for `signmessage`
  on an account path; ordinary address paths are allowed. The child sits
  under the same account xpub `getxpub` already matched, so a valid
  signature still proves the device holds the key. Ledger and Jade
  accept both paths. Owner practice-network walkthrough on candidate
  `37474707538`: Trezor Safe 3 and Ledger Nano both signed and the
  payment broadcast. The signing screen now says the device will ask for
  a short test message before the payment, so the pause does not look
  like a hang.

## Break-and-watch transcripts

Each control below was broken on a disposable copy, the named test was
observed red, and the file was restored green. `PYTHONPATH=tests:.
.venv-ci/bin/python -m unittest <test>`.

| Gate | Break | Test that went red |
| --- | --- | --- |
| CT-14 | removed the `prove_signer_holds_key` call from `verify_signer_device` | `DeviceProofPins.test_identity_check_also_demands_the_proof_before_returning` (1 != 2 calls); `test_identity_check_refuses_when_the_proof_fails` (ProbeError not raised) |
| CT-14 (Trezor path) | moved the proof back to the bare account node `m/48h/1h/0h/2h` | `DeviceProofPins.test_the_proof_signs_at_the_first_receive_path_not_the_account_node` (`['m/48h/1h/0h/2h'] != ['m/48h/1h/0h/2h/0/0']`); `test_identity_check_also_demands_the_proof_before_returning` (same path mismatch) |
| CT-30 | removed the `LARGE_AMOUNT_SATS_UNTRUSTED_QUOTE` trigger from the prepare handler | `LargeAmountGateTests.test_a_lying_low_price_cannot_hide_a_large_payment_under_one_bitcoin` (200 != 400) |
| CT-30 | raised `LARGE_AMOUNT_SATS_UNTRUSTED_QUOTE` above the absolute floor | `LargeAmountPins.test_the_untrusted_quote_floor_is_below_the_absolute_floor` (20_000_000 not less than 10_000_000) |
| CT-13 | moved `verify_selected_outpoints` back inside the session lock | `SendFlowTests.test_broadcast_prechecks_do_not_hold_the_session_lock` (outpoint depth 1 != 0) |
| CT-29 | made `_verify_hwi_identity` always accept | `HwiIdentityPins` (4 failures: planted helper reached JSON parsing instead of the identity refusal) |
| CT-34 | disabled the `_is_low_s` gate | `LowSPins.test_a_high_s_signature_is_refused_with_the_low_s_message` ("low-S" does not match generic "invalid signature") |
| CT-33 | unpinned `pip-tools` in `windows-inputs.yml` | `PipToolsPinTests.test_every_lock_job_pins_the_same_piptools_release` |
| CT-46 | stale `AGENTS.md` source-revision string | `VersionStringPins.test_agents_names_the_tree_revision_from_version_py` |

After each restore the named test returned OK.

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

Published as tag `v0.6.6` on commit `93cf67af63a15aac0912a6fbc270f7e5485e2fc1`
via `.github/workflows/build-candidate.yml` promote run
[37486264639](https://github.com/cjtsh/bitcoin-easy-multisig-signer/actions/runs/37486264639)
(`publish=true`, `candidate_run_id=37482475884`). The release page carries
macOS, Windows, Linux, the source archive, one `SHA256SUMS` with
`SHA256SUMS.asc`, and `BUILD-SBOM*.json`. Not a draft, not a prerelease.

### Candidate attempts

- Run [37464977050](https://github.com/cjtsh/bitcoin-easy-multisig-signer/actions/runs/37464977050)
  from `26ed211` **failed** the Windows and source-archive jobs. Two
  tripwire tests were not portable: `HwiIdentityPins` wrote `#!/bin/sh`
  helpers that CreateProcess cannot exec (WinError 193), and
  `PipToolsPinTests` read only `.github/workflows/` while the source
  archive ships recipes under `ci/`. The macOS DMG job still passed.
  Fix is `f1dc627`; both rules are now canaried in
  `tests/test_windows_portability.py` (`HardeningPinPortabilityTests`).
- Candidate run [37467030340](https://github.com/cjtsh/bitcoin-easy-multisig-signer/actions/runs/37467030340)
  from `f1dc6278829d85414b476df7dbb2d88c057c0fc3` **succeeded** all jobs
  (notarized Apple Silicon DMG, Windows x64, Linux AppImage, source archive
  and in-archive tests, candidate SHA256SUMS). It published nothing
  (`publish=false`): no tag, no release. **Superseded** before promotion:
  the owner Trezor Safe 3 walkthrough failed with HWI `forbidden key path`
  because the CT-14 proof signed at the all-hardened account node. The
  proof now signs at `…/0/0`; a fresh candidate is required.
- Candidate run [37474707538](https://github.com/cjtsh/bitcoin-easy-multisig-signer/actions/runs/37474707538)
  from `cee43a09fc2f920d08951e5b7abb940ef62abcd0` **succeeded** all jobs
  and the owner practice-network walkthrough passed on it (Trezor Safe 3
  and Ledger Nano signed; broadcast accepted). **Superseded** before
  promotion so the signing screen can name the real device press count
  instead of the old "asked twice" banner.
- Candidate run [37482475884](https://github.com/cjtsh/bitcoin-easy-multisig-signer/actions/runs/37482475884)
  from `93cf67af63a15aac0912a6fbc270f7e5485e2fc1` **succeeded** all jobs
  and carries the honest press-count copy. It published nothing
  (`publish=false`). Promote with `candidate_run_id=37482475884` once the
  owner glances at the new signing screen (device behaviour is unchanged
  from the walkthrough that passed).
