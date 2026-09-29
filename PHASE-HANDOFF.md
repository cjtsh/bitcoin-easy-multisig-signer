# Handoff — Bitcoin Easy Multisig Signer

**Read this file first.** It carries the current state, what is proven, what is not,
and the next work in priority order. The detailed records from earlier phases are in
`PROJECT-HISTORY.md`, which is an archive rather than a starting point.

| | |
| --- | --- |
| Repository | `cjtsh/bitcoin-easy-multisig-signer`, branch `phase2-transaction-builder` |
| Version | `0.1.27` — `version.py` is the single source; CI derives tag and artifact names from it |
| Artifact | `~/Downloads/Bitcoin-Easy-Signer-v0.1.27-UNSIGNED-TEST.dmg`, sha256 `52185c46c853a29677102b81a42ff84f4b67b95018d7114ea69d45e6c5a99df3` |
| Tests | 135, all passing (`python -m unittest discover -s tests`) |
| Proven on | the owner's Apple Silicon Mac, three hardware wallets, GitHub Actions CI |
| Last updated | 29 September 2026 |

## 1. What this is

A small Mac app that lets someone who is not a Bitcoiner — a lawyer, a bank officer, a
family member, possibly under stress — send Bitcoin from an **existing** 2-of-3
multisig wallet. It opens a BSMS wallet file, shows the balance, prepares a
transaction, gets it signed on hardware devices, and broadcasts it.

It never creates a wallet, never asks for seed words or a PIN, and has no access to
private keys. The design criterion is the owner's: the main screen shows a balance and
a send flow; every wallet path, xpub and address lives behind **See wallet details**.

## 2. Where it stands

| Phase (see `ROADMAP.md`) | Status |
| --- | --- |
| 1 — Framework and balance view | **Complete** — owner-approved |
| 2 — Send eligibility explained and unblocked | **Complete** |
| 3 — Prepare, review and save an unsigned transaction | **Complete** — accepted on the owner's Mac |
| 4 — Signing and broadcast (Testnet4) | **Complete** — accepted on hardware, two confirmed payments |
| 5 — Real Bitcoin: dry run, then the deliberate switch | **NOT STARTED** |

**Phases 1 to 4 are complete and accepted on real hardware.** The app prepares,
signs, finalises and broadcasts, and two real Testnet4 payments have confirmed.
**Phase 5 is the only work outstanding**; section 5 lays it out as X, Y and Z.

### Standing by on the owner — not a coding task

**The owner is waiting for Apple Developer Program confirmation.** Until it arrives the
app cannot be signed with a Developer ID or notarized, so the released DMG still trips
macOS security and the user must right-click → Open. Enrolment is in progress; the
outcome is a human dependency, not something an agent can resolve by writing code.

Do **not** work around it: no self-signing tricks, no instructing users to disable
Gatekeeper globally, no renaming the artifact to look official. The current
right-click → Open instruction in `README.md` is the honest interim position.

When confirmation arrives, the work is Phase 5, item Z. It needs, in order:

1. A **Developer ID Application** certificate, and the app built with the hardened
   runtime.
2. `CFBundleIdentifier` changed from `Bitcoin Easy Signer` to a reverse-DNS identifier
   — notarisation rejects the spaced form.
3. Every nested Mach-O signed individually with the Developer ID, including the bundled
   `hwi` and `libusb`. The build already signs nested binaries individually before
   sealing the bundle (it must not use `codesign --deep`), so this is mostly a change of
   identity rather than of structure. Expect to need an entitlement or two so the
   bundled Python runtime loads — `allow-unsigned-executable-memory` and possibly
   `disable-library-validation` are the usual ones to try.
4. The app **and** the DMG notarized with `notarytool`, then the ticket stapled.
5. **Signing secrets added to the GitHub repository by the owner** — certificate,
   password and an App Store Connect API key. CI cannot sign without them, so this is a
   second thing only the owner can do.
6. The artifact name drops `UNSIGNED-TEST` once it is genuinely signed.

| Capability | State |
| --- | --- |
| Open a BSMS wallet, scan the balance, explain coverage in plain words | Works, on the owner's real wallet |
| Check the hardware devices *before* building a payment | Works |
| Prepare a payment, live fee tiers, Send All | Works |
| Review: destination, amount, fee, change, final txid, explorer link | Works |
| Sign with the devices, finalise at threshold, re-check the final transaction | Works, proven with all three devices |
| Broadcast to Testnet4 | Works, two confirmed sends |
| Broadcast to mainnet | **Refused in code, deliberately** (`gui.py`, `_broadcast`) |

## 3. What is proven, and how

**Two confirmed Testnet4 payments, using three different devices between them.**

| Send | Devices | Result |
| --- | --- | --- |
| 28 Sep, v0.1.24 | Jade + Trezor Safe 3 | **Confirmed in block 154322**, change returned to the wallet's own change branch |
| 29 Sep, v0.1.25+ | Jade + Ledger Nano S Plus | **Confirmed in block 154330**, txid `493bddeda158b0ad04cac4c74ae6c3408bd97e1f88f792e1e7fd8c9642f6a825` |

Both were verified **after broadcast, without trusting the app**: the raw transaction
was fetched and every signature checked against the wallet's own witness script. The
second decode also identified which cosigner produced which signature, confirming the
pair the owner reported.

The Ledger signed only after the global-xpub fix (section 7), so that fix is proven
against the device it was written for — not merely against hwilib's acceptance logic.

The app's own figures were cross-checked against **Sparrow** on the same wallet and
agreed exactly: confirmed balance 20,744, mempool −2,570, spendable 18,174.

## 4. What is deliberately NOT done

- **No mainnet transaction has ever been prepared or signed.** Everything proven is
  Testnet4. Note that only *broadcast* refuses mainnet: prepare, sign and finalise all
  work on mainnet today, which is why a dry run needs no code change (section 5).
- **The DMG is unsigned and unnotarized.** Gatekeeper blocks a double-click launch;
  the user must right-click → Open. `CFBundleIdentifier` is `Bitcoin Easy Signer`
  (with spaces) rather than a reverse-DNS identifier, which blocks notarisation.
- **No fee-bump flow in the app.** Transactions signal replaceability (BIP125), so a
  stuck payment *can* be replaced, but only from another wallet that supports it.
- **Not audited.** Experimental software handling real money.
- **macOS only.** No Windows or Linux build exists.
- **The testnet4 node and mining helper are side projects**, documented in section 10
  because they exist on the machine, not because the app depends on them.

## 5. Next work, in priority order

**This section is Phase 5 of `ROADMAP.md`** — the only phase not yet complete.

### X. Mainnet dry run — no broadcast, no code change, highest value

The app has never touched real Bitcoin. Prepare a real mainnet payment, sign it with
two devices, finalise it in memory, and verify the result independently.

1. Load a **mainnet** 2-of-3 BSMS (a real wallet holding a small balance). The app
   refuses a cross-network wallet by design, so a Testnet4 file will not do.
2. Prepare a small payment **to one of the owner's own addresses**.
3. Sign with two devices. **Read both device screens**: destination, amount and fee
   must match what the app displayed.
4. Finalise and verify independently (see below).
5. **Do not broadcast.** The app cannot broadcast mainnet, which is the point.

Verification, without trusting the app: decode the raw transaction; check each input's
witness against the wallet's own witness script; compare every output, the change
address and the fee against the review screen; and confirm the txid shown *before*
signing equals the txid after signing (for SegWit the witness is not part of the txid,
so it cannot change). The method used for the Testnet4 send is described in section 3.

**Treat a signed-but-unbroadcast mainnet transaction as sensitive:** anyone holding
those bytes can broadcast them.

### Y. Real Bitcoin: the deliberate switch

Only after X, and only on the owner's explicit instruction:

- **Open mainnet broadcast behind a deliberate opt-in** — per transaction, visibly
  distinct, naming mainnet. Keep the refusal as the default, keep the network checks,
  and keep the rule that the confirmed txid must equal the prepared one. Tests must
  prove mainnet broadcast is impossible without the opt-in.
- **Settle the fee behaviour.** Live mainnet fee guidance already exists
  (`fetch_fee_rates`, labelled `mempool.space mainnet`), but the user's rate is bounded
  to **1–25 sat/vB** (`wallet_service.py`). In a busy mempool the recommended fastest
  rate can exceed 25, so the app would clamp or refuse exactly when the user needs to
  pay more. Decide deliberately — raise the bound, surface the recommendation, or
  explain the limit — and test the busy-mempool path with a stubbed high quote.
- **Decide about fee bumping.** Either implement a replacement (same inputs, higher
  fee, re-signed on the devices) or state plainly that a stuck payment must be bumped
  in another wallet.
- **Acceptance:** a completed mainnet send, verified independently, with the owner's
  authorisation recorded in this file.

### Z. Make it safe to hand to the person it is for

- **Developer ID signing + notarisation**, so the DMG opens with a double-click. The
  current Gatekeeper warning is precisely the friction that stops a non-technical user.
  **Blocked on a human dependency:** the owner is awaiting Apple Developer Program
  confirmation, and CI will also need signing secrets that only the owner can add. See
  *Standing by on the owner* in section 2 for the full sequence.
- **Fix `CFBundleIdentifier`** to a reverse-DNS identifier first.
- **A one-page plain-language guide**: what the wallet is, the three devices, why a
  test payment is recommended, what to do when a device is not found, and that a
  payment is not finished until it confirms.

### Smaller, ready when wanted

Cut **v1.0.0** (the owner's stated criterion was a completed send; there are two, with
all three devices). Refresh the pinned GitHub Actions (Node 20 → 24 deprecation).
Bring the stale `main` branch current. Decide whether the testnet4 node and mining
helper stay as project tools.

## 6. Rules that must not be broken

1. **A local, existing-wallet app.** No seed words, no private-key entry, no hosted
   upload, no silent background signing, no wallet creation.
2. **Never commit wallet data** — BSMS exports, xpubs, addresses, PSBTs, settings,
   credentials. Redact sensitive values from issues, logs, screenshots and CI output.
   No log files are written, by design.
3. **Testnet4 for live development** unless the owner explicitly authorises a specific
   mainnet operation. Never silently switch networks or explorers, and never fall back
   from a failed custom endpoint to a public one without telling the user.
4. **Broadcasting real Bitcoin is refused** until the owner changes that boundary
   deliberately. It is a code change, not a setting.
5. **Every published build carries a new version.** CI refuses to overwrite a
   published tag, which is what caught a near-miss where a fix would have been shipped
   under an already-published version.
6. **Never claim hardware verification that has not happened.** The evidence in
   section 3 is what was exercised; keep it that way.

## 7. Decisions and their reasons — do not silently undo

| Decision | Why |
| --- | --- |
| Every input signals replaceability (`nSequence 0xFFFFFFFD`) | A payment built with `0xffffffff` is final: the owner's second send sat stuck with no remedy available to anyone. A test asserts it. |
| The PSBT publishes every cosigner's **global xpub and origin** | A Ledger rebuilds the wallet policy from them. Without them hwilib skips every input **silently** — no error, no prompt. Trezor and Jade do not need them, so only a Ledger exposes the omission. |
| The balance check allows a shortfall that unconfirmed spends explain | A confirmed output spent by an unconfirmed transaction still counts in the explorer's address totals but is gone from its UTXO list. Calling that corruption hid the whole prepare card and locked the owner out of his own wallet until the spend confirmed. Genuine disagreements are still refused. |
| HWI is asked for chain **`test`**, never `testnet4` | Jade's client has no testnet4 entry and errors with `Unhandled network: testnet4`. Testnet and testnet4 share the `tpub` version bytes and `tb1` prefix, so the xpub comparison stays byte-exact. Trezor and Ledger treat any non-mainnet chain as testnet. |
| A descriptor **checksum is optional** | Sparrow writes the descriptor without one and states restrictions separately; Nunchuk writes one and says "No path restrictions". Both are valid. The reference address is the real integrity check, and the app computes and prints the checksum for the owner to compare. |
| The app **resolves** the change branch instead of asking the owner to declare it | The earlier control asked a non-technical owner to assert a derivation detail they had no way to check. The change address stays visible in the review and a test payment is recommended while it is unconfirmed. |
| `_select_inputs` is the single source of truth for preview and build | The live preview once overstated the size by 34%, so the previewed fee did not match the transaction actually built. |
| The high-value prompt also fires on a local absolute floor (0.1 BTC) | A misreporting or compromised price feed must not be able to suppress it. |
| `safe_http.py` refuses every redirect and keeps TLS verification on | Otherwise an explorer could downgrade HTTPS to plaintext or move the request to another host, exposing derived addresses. |
| The local API token travels in the URL fragment | It must never be sent to the server or be readable by another local process from an unauthenticated `GET /`. |
| HWI's own error text is shown verbatim | Guessing at device faults wasted time twice; the device's own words identify plumbing problems. |

## 8. How to build, verify and release

1. **Bump `version.py`.** Required for any publish; CI refuses an existing tag.
2. **Push to `phase2-transaction-builder`.** GitHub Actions builds the Apple Silicon
   DMG plus the source archive and `SHA256SUMS`, runs the tests **from the extracted
   archive**, and publishes the release. The workflow ignores `**/*.md`, so a
   docs-only commit does not trigger a build.
3. **Verify the artifact as a user receives it** — not merely that CI was green:
   download it, `shasum -a 256 -c SHA256SUMS`, mount with `hdiutil`, copy the app out,
   `xattr -cr`, confirm `CFBundleShortVersionString`, and run the bundle's own
   `--check-bundle`. Also run `--check-network` **with `SSL_CERT_FILE` pointed at a
   nonexistent path**, which is the only check that distinguishes "HTTPS works here"
   from "HTTPS will work anywhere" (see the trust-store regression in
   `PROJECT-HISTORY.md`).
4. **Keep the archive complete.** `scripts/build-source.sh` fails the build if a root
   module is missing; that guard exists because the published tarball was once
   unimportable.

## 9. Hardware devices — what each one needs

| Device | Signer | Notes |
| --- | --- | --- |
| Blockstream Jade | 1 (`a54cf273`) | Needs the HTTP relay, so `requests` must be bundled; the guard is the bundled tool's `--dsh-capabilities` (`jade_http_relay`). PIN and passphrase are entered **on the device**; HWI never accepts a PIN from the host. |
| Trezor Safe 3 | 2 (`20616230`) | Unlock it first. A Trezor that locks on a timeout re-enumerates USB, and the failed close used to abort the whole device scan (patched in `scripts/hwi_entry.py`). |
| Ledger Nano S Plus | 3 (`66a53fec`) | Must be unlocked **and** have the Bitcoin Testnet app open for a testnet wallet. Error `0x5515` means locked. Requires the PSBT global xpubs (section 7). |

All three were verified byte-identical to the cosigner xpubs in the owner's
`3HWKeys.bsms` (a Sparrow-created 2-of-3 Testnet4 wallet, descriptor checksum
`dvthsm8x`). That file is wallet data and must never be committed.

Diagnosing a device means running the **bundled** HWI directly, because no log files
are written. That is deliberate: no wallet data in logs.

## 10. Environment facts

- **App repository:** `~/Documents/deepseek-harness/default-workspace/bitcoin-easy-multisig-signer`.
  The built DMG is staged in `~/Downloads`.
- **A synced Testnet4 node exists on this machine** (Bitcoin Core 31.1), datadir on the
  Thunderbolt drive at `/Volumes/TBolt-1TB-Fun/Testnet4`, config at
  `~/.bitcoin/bitcoin.conf`, RPC on `127.0.0.1:48332`. This matters for the project's
  own rule — *verify with your own node rather than trusting an explorer* — and it is
  the fastest way to check a transaction or a balance independently.
- **Mining helper (not part of the app):** `~/bitcoin-testnet-miner.sh` is a menu over
  `~/mine-testnet4.sh`; the miner binary is `~/bin/cpuminer`. The miner is **stopped**.
- **Why Testnet4 mining was abandoned**, recorded so nobody restarts it hopefully: the
  min-difficulty rule allows a difficulty-1 block once 20 minutes have passed since the
  parent, and the miners winning that race future-date their blocks roughly 115 minutes
  ahead of real time. A node with a correct clock therefore only ever offers
  **full** difficulty, which is ~651 years per block on this Mac. The winning behaviour
  depends on a forged clock. A [proposed soft fork](https://batmanbytes.github.io/testnet4-softfork/)
  would invalidate those blocks and has passed its activation height without being
  adopted.
- **Operational note that cost time:** match processes by exact name (`pgrep -x`), not
  by command-line substring. `pgrep -f cpuminer` matched a helper script that merely
  mentioned the word, which made the miner look like it was already running. Related:
  editing a shell script while a process is reading it can kill that process — read the
  file, then restart the process.

## 11. Archive

`PROJECT-HISTORY.md` holds the detailed records: the security findings and their
dispositions, the trust-store regression post-mortem, the build bugs found by running
the build for real, the usability bugs found in live use, and the phase-by-phase
narrative. Read it when you need the reasoning behind something in section 7, or when
you want to know what was already tried.
