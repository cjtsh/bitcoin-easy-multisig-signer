# Phase 2/3 handoff — v0.1.11

**Repository:** `cjtsh/bitcoin-easy-multisig-signer` (branch `phase2-transaction-builder`)
**Version:** `0.1.11` (`version.py`)
**Status:** code complete and verified with synthetic data and a real loopback HTTP
server. **The Apple Silicon DMG has not yet been built through GitHub Actions** —
this session has no GitHub authentication, and that workflow requires it. A local
build was attempted as a substitute; see *Build status* below.

---

## 1. The blockage, and what actually fixed it

The reported symptom was that the app "provided no functionality to actually
construct a transaction". That was not accurate about the code: the wallet/PSBT
engine and the entire send UI (`ui.html`, `/api/prepare`) already existed and
worked. This was verified by building a transaction with the real engine, signing
it with 2 of 3 synthetic keys, finalizing it, and measuring it.

The real cause was a single eligibility gate. `can_prepare` required a BSMS export
that proves **both** a receive and a change path. A `/*` export marked
`No path restrictions` proves only receive (`reference_status ==
"receive-branch-only"`), so the app classified the wallet as **view-only by
design** and never rendered the send card at all. Retrying could never help, which
is why it read as missing functionality.

**Change:** an owner-confirmed change branch.

- `probe.declare_change_branch()` derives `/0/*` and `/1/*` from the owner's own
  descriptor. It refuses anything that is not a plain `/*` on every key, and the
  existing parser checks the change descriptor uses exactly the same multisig
  cosigners, threshold and policy as receive.
- `parse_bsms(text, declared_change=...)` only applies it for the
  `No path restrictions` + bare `/*` case. Everywhere else the flag is ignored,
  so a redundant confirmation can never break a valid wallet.
- `wallet_service.can_declare_change()` gates the offer to 2-of-3 wallets whose
  receive path is already anchored.
- The UI shows **"Use the standard change branch"** only in that situation, does
  nothing until the box is ticked and the button pressed, marks the change address
  as owner-declared, adds its own review acknowledgement, and reports how many
  previously used change addresses the scan found on that branch — so the branch
  you confirmed is either supported by the wallet's own history or the app says
  plainly that it is not.

The app still never guesses a change path. It asks, and it shows you the result.

## 2. Fee preview now matches the transaction that is built

The live preview sized the transaction using **all** confirmed scanned outputs. In
the verification fixture that reported 412 vB where the transaction actually built
at 307 vB — a 34% overstatement, so the previewed fee did not match the review.

**Change:** `wallet_service._select_inputs()` is now the single source of truth for
input selection and fee, used by both `estimate_fee_preview()` and
`build_unsigned_psbt()`. The preview takes the requested amount, fee rate and
destination, so it selects exactly the inputs the builder will select. Preview and
build are asserted equal at multiple amounts in the test suite.

Send All already deducted the fee correctly; that is now pinned by tests
(`total_spend == confirmed balance`, no change output, `remaining == 0`).

## 3. The high-value confirmation no longer trusts a remote price

The ≥$10,000 gate was computed only from mempool.space's BTC/USD quote, so a
misreporting or compromised feed could suppress the prompt.

**Change:** the gate also fires on an absolute local floor,
`LARGE_AMOUNT_SATS_FLOOR = 10_000_000` (0.1 BTC), enforced in `gui.py` and mirrored
in the UI. Tested with a deliberately lying price feed.

---

## 4. Security findings and dispositions

Two independent review passes covered the whole codebase. Only findings that could
plausibly cause fund loss, code injection, or meaningful disclosure were actioned.

| # | Severity | Finding | Disposition |
|---|---|---|---|
| 1 | High | `urllib` followed 30x redirects, so an explorer could **downgrade HTTPS to plaintext** or move the request to another host, defeating the HTTPS-only rule and exposing derived addresses | **Fixed.** New `safe_http.py` refuses every redirect and asserts the final URL is unchanged; TLS verification stays on. `wallet_service`, `gui` and `network_settings` all use it |
| 2 | High | CI published an unsigned DMG as the repository's **"Latest" release on every branch push**, with `--clobber`, no checksum and no review gate | **Fixed.** Branch pushes build artifacts only; releases are gated on a `v*` tag; `SHA256SUMS` emitted; `--clobber` removed; unsigned test builds now use `--latest=false --prerelease` |
| 3 | High | Build-time Python dependencies and the bundled native `libusb` dylib were unverified before being code-signed and notarized | **Fixed.** `certifi` pinned exactly (it *is* the app's CA trust store); `LIBUSB_SHA256` integrity gate aborts the build on mismatch and warns loudly when unset |
| 4 | High | `codesign --deep` re-signs nested code, so anything injected into the bundle would inherit the Developer ID signature and notarization | **Fixed.** Nested Mach-O signed individually, `hwi` required, `.app` sealed without `--deep`, then `codesign --verify --strict` |
| 5 | Medium | The local API token was embedded in an **unauthenticated** `GET /` response; any local process could read it and then drive the wallet API | **Fixed.** The token now travels in the URL fragment (never sent to the server) and the page contains no token; comparison uses `hmac.compare_digest` |
| 6 | Medium | GitHub Actions pinned to mutable tags; a stale `.build-venv` was reused across builds | **Fixed.** All 12 actions pinned to commit SHAs; venv rebuilt from scratch each build |
| 7 | Medium | The genesis-hash check is one-shot and a malicious custom explorer can echo the public constant | **Accepted, documented.** Fund loss is already blocked: every previous transaction is re-fetched and required to match the wallet's derived script and value, and `utxo_consistent` ties balance to UTXOs. Residual risk is privacy and misleading balances, not fabricated amounts |
| 8 | Low | "Same user on this machine" is the residual trust boundary for the local API | **Accepted, documented.** |

Two review passes agreed the following were already clean: loopback-only bind with
an ephemeral port, Host and Origin checks, `nosniff`/CSP/no-store headers, TLS
verification never disabled, no `shell=True`/`eval`/`exec`/`pickle`/archive
extraction, no request field reaching a filesystem path or subprocess, atomic
`0600` settings writes, `O_EXCL` PSBT save that refuses to overwrite, no
signing or broadcast endpoint, and no xpub, descriptor, fingerprint or origin ever
leaving the machine (only derived addresses and public txids, and only to the
configured explorer, after explicit consent).

---

## 5. Evidence

- `python -m unittest discover -s tests -q` → **77 tests pass** (was 51).
  New: `test_gui_integration.py` (real loopback HTTP server: import → scan →
  estimate → prepare → PSBT, plus token/Origin/Host rejection), 
  `test_declared_change.py` (change-branch derivation and preview/builder
  agreement), `test_safe_http.py` (redirect refusal, TLS verification),
  `fake_explorer.py`.
- **Independent verification**: a separate harness builds a transaction with the
  engine, then *signs it for real* with 2 of 3 synthetic keys and finalizes it.
  Result: amount exact, `packet.fee()` matches, change lands on the wallet's own
  change branch, **305 vB actual vs 307 vB estimated** (conservative), effective
  **5.033 sat/vB against a requested 5** — i.e. no underpayment.
- Send All: 175,000 − 1,845 fee = 173,155 sats, one output, no change,
  `remaining == 0`.
- Every boundary case rejected: rate 0 and 26, amount 545 (below dust), amount
  above balance, mainnet destination on Testnet4, prepare before a scan, and
  settings changes invalidating a prepared review.
- Workflow YAML parses; `scripts/build-macos.sh` and `build-source.sh` pass
  `bash -n`; the two workflow copies are byte-identical; inline UI JavaScript
  passes `node --check`.

## 6. What is deliberately NOT verified

Synthetic fixtures prove code paths, not your wallet. Still unverified:

1. **No Apple Silicon window walkthrough.** Nobody has driven the native WebKit
   window through import → refresh → send form → save.
2. **No real Testnet4 BSMS import.** Whether the confirmation control appears, and
   what the change-branch evidence line reports, is unproven against your actual
   file.
3. **No hardware signer.** HWI recognition has never run against a physical
   device; signing and broadcast remain unimplemented by design.
4. **The token-in-fragment change needs one browser check.** If the fragment did
   not survive the window load, the page now fails loudly with "could not read its
   local access token" instead of silently doing nothing. Watch for that text on
   first launch.
5. **No macOS bundle build has been executed successfully in this session** (see
   below). The PyInstaller/codesign/hdiutil path is verified only by `bash -n`,
   stubbed unit checks of the extracted logic, and the fact that v0.1.9/v0.1.10
   previously built on CI.

---

## 7. Build status and blockers

**Blocker:** GitHub authentication. `gh auth status` reports no logged-in host, and
the macOS keychain credential for `github.com` is stale and belongs to a different
account (`mypbs`), so even `git push` fails with "Invalid username or token". The
workflow cannot be triggered and artifacts cannot be downloaded without it.

**Required human action:** `gh auth login` (GitHub.com → HTTPS → authenticate Git →
login with a web browser) signed in as the account that owns or can write to
`cjtsh/bitcoin-easy-multisig-signer`.

Once authenticated: commit, push the branch, push tag `v0.1.11`, watch the run,
then verify the downloaded DMG against the published `SHA256SUMS`.

Note the deliberate guard in the publish job: it refuses to publish unless the tag
is exactly `v0.1.11`, so version-0.1.11 assets can never be mislabelled. Bumping
the version means updating `version.py` and the workflow together.

**Versioning note:** `main` is still at `0.1.6` while the released line has run to
`v0.1.10` on this branch. `main` should be brought current as part of any release
process.

---

## 8. Next phase entry point

Per `ROADMAP.md`, the acceptance gates that remain require the owner:

- **Phase 2 gate:** on the Mac, import the real Testnet4 BSMS, confirm Refresh
  still works, and record what the wallet card and send-eligibility notice say.
  A receive-only wallet must explain itself and offer the change-branch control;
  a wallet with declared paths must reach the send form.
- **Phase 3 gate:** complete import → fresh scan → partial or Send All → live fee
  and dollar review → high-value confirmation where applicable → **save the
  `.psbt`** → reach the signer-recognition screen. Then decode the saved PSBT with
  an independent tool and compare network, inputs, outputs, change and fee.
- **Phase 4** (signing and broadcast) remains explicitly **not authorised**. Do not
  implement it without the owner changing that boundary.

Hardware keys are expected this afternoon; the signer-recognition screen is the
first thing to try once the DMG is in hand.
