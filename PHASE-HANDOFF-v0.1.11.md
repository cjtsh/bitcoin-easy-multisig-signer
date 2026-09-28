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
| 9 | **High** | **Regression introduced during this work, caught only by testing the shipped artifact:** the bundled `certifi` CA store was never actually used. `build_opener()` constructs an `SSLContext` eagerly at import time, but the packaged app sets its bundle later, inside `main()`. HTTPS therefore depended on whatever CA files the host machine happened to have — the build self-check passed on the runner and the app failed on the owner's Mac | **Fixed.** The HTTP opener is now built on first use and the bundle is loaded explicitly (`safe_http.set_trust_bundle`); the packaged self-check asserts the configured store *is* the bundled one; and CI re-runs the network check with the ambient trust paths removed so this cannot regress silently |

Two review passes agreed the following were already clean: loopback-only bind with
an ephemeral port, Host and Origin checks, `nosniff`/CSP/no-store headers, TLS
verification never disabled, no `shell=True`/`eval`/`exec`/`pickle`/archive
extraction, no request field reaching a filesystem path or subprocess, atomic
`0600` settings writes, `O_EXCL` PSBT save that refuses to overwrite, no
signing or broadcast endpoint, and no xpub, descriptor, fingerprint or origin ever
leaving the machine (only derived addresses and public txids, and only to the
configured explorer, after explicit consent).

### Post-mortem: the trust-store regression (finding 9)

Worth recording because the *verification* failed, not just the code.

The previous self-check only asked "did an HTTPS request succeed?". On the GitHub
runner that was true — the runner has ambient CA files where OpenSSL looks — so
the check passed while the app was ignoring the CA store it ships. On a Mac
without that ambient configuration, every HTTPS request failed with
`CERTIFICATE_VERIFY_FAILED`, which would have broken balance scans, fee quotes and
price quotes: the app would have looked completely dead.

The replacement check asserts the *configured* store is the bundled one and that
it contributes trusted CAs, and CI additionally repeats the network check with
`SSL_CERT_FILE`/`SSL_CERT_DIR` pointed at nonexistent paths. That last step is the
one that actually distinguishes "HTTPS works here" from "HTTPS will work
anywhere", and it is reproducible locally:

```sh
SSL_CERT_FILE=/nonexistent/ca.pem SSL_CERT_DIR=/nonexistent/certs \
  "dist/Bitcoin Easy Signer.app/Contents/MacOS/Bitcoin Easy Signer" --check-network
```

Verified: the fixed build passes that command; the previously published v0.1.11
artifact built by CI fails it.

---

## 5. Evidence

- `python -m unittest discover -s tests -q` → **88 tests pass** (was 51).
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
2. **Partially resolved.** The control did appear for the owner's real wallet and
   they used it successfully (see the observations below). What has *not* been
   checked is the change-branch evidence line against a wallet that has spent
   before, and the review/save steps.
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

### Observed on the real Mac (owner report, v0.1.11 DMG)

This is the first evidence from the native app with a real wallet rather than
synthetic fixtures.

- The owner imported their wallet on Apple Silicon. The app showed the
  send-eligibility blockage together with the change-branch confirmation control,
  which **confirms the diagnosis in section 1 against the real file**: the wallet
  is the receive-only `/*` form, so `can_prepare` was false and the send screen
  could never appear before this work.
- After confirming the control, the send flow became available and the owner
  reached the "prepare a send" screen. That is the Phase 2 acceptance-gate
  behaviour — a receive-only wallet explains itself, offers the control, and a
  confirmed wallet reaches the send form — observed in the shipped app.
- **Reported friction:** the owner did not understand *why* they were being asked
  to confirm. That is a genuine usability finding from first live use, and the
  wording has been rewritten in plain language as a result. The control is a
  safety gate for how change is addressed, so it must be understood, not clicked
  through.
- **Second real-Mac finding: the save button did nothing.** Two fragile
  dependencies were involved. The page silently fell back to a browser blob
  download, which WKWebView ignores without any error, and the native save dialog
  could return nothing while reporting no error either. Saving now goes through
  `POST /api/save` — the same local API every other action in that window already
  uses, so it cannot depend on the pywebview bridge being injected. It writes a
  new file into the user's **Downloads** folder and names the full path on screen.
  The bytes come from server-side state, so nothing the page sends can influence
  what is written or where, and an existing file is never replaced. The pywebview
  bridge remains only as a fallback path and shares the same implementation.
- Still unobserved: the hardware signer screen.


### Interface simplification (owner request)

The owner's standing design criterion is that this is **not** a wallet for a
Bitcoiner: it is a guided "send from an existing wallet" tool for a lawyer, a bank
officer, or a family member, possibly under stress. The first live build had drifted
into showing the policy, reference/receive/change addresses, three cosigner xpubs
with derivation paths, scan statistics and a full per-address activity list all on
the main screen.

- All of that now lives behind a **See wallet details** button, which opens a
  panel. Two entry points (the wallet card and the balance card) open one dialog.
- The main screen shows: network, balance in BTC with satoshis and an approximate
  dollar line, one short coverage sentence, and the send flow.
- The four step chips are gone (the cards are numbered), the duplicated Refresh
  button is down to one, several paragraphs of small print were cut, and the
  "Signer Signer" typo from the repository rename is fixed.
- **Nothing safety-critical was hidden.** Destination, amount, fee and the change
  address remain visible in the review, as do errors, warnings, the high-value
  confirmation and the change-branch confirmation.

Alongside it, two safety-ergonomics additions the owner asked for:

- The send step recommends a **small test transaction first** — advisory, never
  blocking.
- The review shows the **final transaction ID** (for segwit the witness is not part
  of the txid, so it is already known before signing) plus a **public explorer
  link**, and explains that the app does not broadcast, so the link is how the
  result is confirmed afterwards.

Verified by rendering the real page in headless Chrome and inspecting it, since the
native window cannot be driven from here.

---

## 7. Build status

**The GitHub Actions DMG is built, published and verified.** Release `v0.1.11` is
the repository's current release, carrying the Apple Silicon DMG, the matching
source archive, and `SHA256SUMS`.

- Final workflow run `36453605797` — **all five jobs green** on the current
  commit: read version (5s), source archive and tests (25s), Apple Silicon DMG
  (2m1s), SHA256SUMS (5s), publish release (15s). CI runs the full suite on
  Python 3.12, so the tests are verified on Linux and macOS, not only this Mac.
- The published DMG was then downloaded and verified as a user would receive it:
  its SHA-256 matches the published `SHA256SUMS` (`hdiutil verify`: VALID); the
  app inside is valid under `codesign --verify --strict`; `CFBundleShortVersionString`
  reads `0.1.11`; and both self-checks pass.
- **The decisive check passes on the published artifact**: `--check-network`
  succeeds with `SSL_CERT_FILE` unset *and* with it pointed at a nonexistent
  path, with `SSL_CERT_DIR` nonexistent, which proves the shipped app trusts the
  CA store it carries rather than the host's configuration. The same command
  failed on the artifact built before the fix and on the artifact CI published
  from the previous commit.
- The downloaded DMG matches its published `SHA256SUMS` digest, `hdiutil verify`
  reports the checksum VALID, and the app inside is valid under
  `codesign --verify --strict` with `CFBundleShortVersionString` correctly
  recorded as `0.1.11`.
- A local build was also produced and verified end to end on this Mac
  (Apple Silicon, macOS 27). That is what exposed the trust-store regression:
  every CI check was green while the app could not verify any certificate here.

**The workflow is deliberately simple**, per the owner's request: pushing to
`phase2-transaction-builder` builds the app, verifies it, and publishes an
ordinary (non-pre-release) release. The version and tag are read from
`version.py`, no version number is hardcoded, and re-running for an existing
version replaces that release, so iterating is a single push.

### Two build bugs found by running the build for real

1. **Wrong Python.** `hwi 3.2.0` declares `Requires-Python >=3.9,<3.13`. On this
   Mac `python3` is 3.14, so the build died deep inside pip with an unreadable
   error. The script now fails immediately with the required range and the fix.
   This is also why the CI workflow is genuinely necessary here: it pins 3.12.
2. **Stray extended attributes.** macOS FileProvider (this repo lives in
   `~/Documents`) attaches `com.apple.FinderInfo` to bundle contents, and
   `codesign --verify --strict` rejects that as unsealed "detritus". The build now
   strips xattrs before signing and again on the staged copy. A CI runner would
   not have hit this; a local build did.

### Remaining non-blocking notes

- `main` is still at `version.py 0.1.6` and its copy of the workflow is a
  *different, older* file named "Build release candidate (no publishing)". That
  stale name is what GitHub displays in the workflow list. `main` should be
  brought current as part of any release tidy-up.
- GitHub reports a deprecation notice: the pinned actions target Node 20 and are
  being forced onto Node 24. Harmless today; the pins will need refreshing.
- `CFBundleIdentifier` is still `Bitcoin Easy Signer` (with spaces) rather than a
  reverse-DNS identifier. Cosmetic for an ad-hoc-signed local build, but it should
  be fixed before any notarized distribution.
- The release DMG is unsigned and unnotarized, so Gatekeeper blocks a
  double-click launch. The user must right-click → Open, or allow it once in
  System Settings → Privacy & Security.

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
