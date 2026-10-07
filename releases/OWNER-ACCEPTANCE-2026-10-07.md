# Owner acceptance — observations that are design properties, not defects

**Signed:** Bitseeker LLC
**Date:** 2026-10-07
**Applies to:** the Color Team findings ledger, cycle 2 carried items and
cycle 3 Infos, as published in
`bitcoin-easy-multisig-signer-colorteam-audit-report-v0.6.6.md`.

## Why this note exists

The audit framework closes an open finding in exactly two ways: a test that
can fail, or a written, dated owner acceptance. This note is the second
mechanism, and it is used only where the first one does not apply — where the
observation is a property of the product's design, not a defect that a code
change would remove.

Everything else is fixed in code, with a fail-capable test, in the same
revision this note lands in. Owner preference, unchanged across cycles: fix
the issue rather than write about it. The items below are the ones where
"fixing" would mean redesigning a working product that a lawyer, accountant
or spouse is expected to use.

No wallet material, address, transaction identifier, device identifier,
setting or diagnostic file is recorded here.

---

## Carried cycle-2 observations (closable by dated owner acceptance)

These were filed in the v0.6.5 cycle and explicitly left open on the
framework's own reading that a dated owner note closes them. Each is accepted
as a design property.

| ID | Accepted as |
| --- | --- |
| **CT-35** | The local loopback API serves `/api/price` and `/api/fees` without the session token. Both are public reference data, cache-bounded, Host-pinned, and carry no wallet state. The interface needs them before a wallet is imported. This is deliberate. |
| **CT-36** | The fee-quote parser's clamp (1000 sat/vB) is a sanity bound, not the policy cap (25 sat/vB). A quote inside that range can only affect availability of a fee suggestion, never an amount or an output. Deliberate separation of "is this parseable" from "is this sensible". |
| **CT-37** | `_same_xpub` compares the key material and ignores serialization version bytes. It is a comparison helper with no downstream effect on what is signed or sent. |
| **CT-38** | The bundled trust-store pin fails open to the platform's own CA defaults when the bundle cannot be used. TLS verification is never disabled. Requiring a custom bundle to be present would make the app refuse to start on a machine the OS already trusts. |
| **CT-39** | The DesktopBridge URL pin passes when the window URL cannot be read. The load-bearing control is byte-equality of the served interface, which is pinned. When the URL is unreadable there is nothing to compare against and refusing would blank the owner's screen. |
| **CT-40** | The client renderer's version identity cannot be established from inside the app. No security decision — not signing, not broadcast, not file access — is taken on it. |
| **CT-41** | Vendored embit reports master-key fingerprints as `0x00000000`. A BSMS record cannot reach that code path; the note exists to stop a future reader mistaking it for a real fingerprint. |
| **CT-42** | In source mode, a malformed request body or a dropped connection prints a full traceback to the operator's own console. No secret value exists in the process that could appear in one. This is the standard Python development server doing its job. |
| **CT-44** | The loopback server uses the operating system's default listen backlog. Under a 160-connection burst, one connection was reset. This is the resilience of the operator's own local interface, not a network service. |
| **CT-47** | The three platform dependency locks resolve slightly different patch versions of the same packages (for example `cryptography` 50.0.1 against 50.0.2). Every one is hash-pinned, the signed macOS DMG runs the set that was locked for it, and the difference is the expected consequence of resolving one lock per platform. |

---

## Cycle-3 observations that are properties of the design

| ID | Accepted as |
| --- | --- |
| **CT-61** | A BSMS record that names an attacker's key is accepted as a valid wallet definition. This is the definition. A BSMS file *is* the wallet's declaration of who must sign; the application cannot know which of the three named keys belongs to the person it is talking to. The trusted delivery of the BSMS file is the security boundary, and the product says so. Adding a second, contradictory source of wallet truth would be a worse product, not a safer one. |
| **CT-63** | `bundled_capabilities` is readable without passing the device identity gate. It is set at build time from what was compiled into the bundle and carries no wallet data, no device identity and no key material. |
| **CT-64** | `pending_by_wallet` is not pruned within a single app session. It is bounded by the number of wallets imported in one session, holds only public pending-transaction state, and disappears when the app closes. |
| **CT-65** | Two transaction-id clauses are redundant and unpinned in isolation. Under `SIGHASH_ALL` neither can fire alone. They are defence in depth; pinning one of them in isolation would freeze a line whose only job is to be impossible. |
| **CT-66** | The key-proof parser has strict contract corners that a malformed device reply can reach. Every one of them fails closed and refuses the signer. No real device emits those shapes. |
| **CT-67** | The key proof is taken at the first receive path (`…/0/0`) rather than the account node. This is a documented tradeoff: Trezor and OneKey on Trezor firmware refuse `signmessage` on an all-hardened BIP48 account path, so the proof travels where every supported device will answer it. The proof is still bound to the same account xpub that was matched a moment earlier. |
| **CT-68** | Signature R-minimality relies on embit's strict DER parser. The dependency is hash-pinned and vendored with exactly two documented edits. Re-reviewing on any embit bump is already a standing rule (`HWI-DEPENDENCY.md`, `RELEASE-PROCESS.md` §5). |
| **CT-69** | A bound device is matched on type and path. If the same type reappears at the same path within one signing session, the earlier verification is reused. The device still has to prove it holds the wallet key before any PSBT is sent, and a new signing session re-identifies it. |
| **CT-70** | In browser mode the session token can survive in that browser's own history. It is a session-only token for a loopback-only server on the operator's own machine, it expires with the app, and the packaged desktop app does not use a browser at all. |

---

## Deferred, with the reason

| ID | Deferred because |
| --- | --- |
| **CT-54** | Rebuilding `vendor/libusb-1.0.0.dylib` from pinned upstream source is the right change and is scheduled for the next dependency bump, which is when the pin has to move anyway. The current dylib's symbol set is identical to the pinned build and its provenance chain is recorded in the SBOM. The audit's own remedy is "build from pinned source next bump". Accepted as a dated deferral, not as a permanent property. |
| **CT-59** | A stalling explorer can make one balance scan slow. The scan is bounded per request and fails closed: if it cannot get a complete answer it claims **nothing** about the balance. This is an availability limitation of a light-client scan, not a correctness one — the dangerous direction (claiming a balance the explorer never confirmed) is already refused. A hard deadline would trade one availability limit for another (a slow-but-honest scan would be killed), so the residual is accepted as it stands. Revisit if an owner ever reports a scan that feels stuck. |

---

## One disclosure the note should carry

While closing CT-48 the repository was swept ref by ref. Every publish-capable
workflow file is now deleted from every branch. One residual cannot be removed
without doing something the release contract forbids: **historical tags freeze
their commit's workflow text.** GitHub runs a workflow from the ref you name,
so tags from `v0.1.0` to `v0.6.3` still contain their era's pipeline, and
those before v0.6.4 lack the default-branch guard. Moving or deleting a
published tag is itself a CT-01/CT-27-class finding — "Never replace an
existing release's assets" — so those tags stay as they are.

The control that answers this is the one that was missing: the dispatch ref is
always `main`, `scripts/check-publish-paths.sh` keeps every *branch* free of a
second publisher and fails the release gate if one reappears, and the publish
job refuses every ref but `refs/heads/main`. Naming this here rather than
implying the sweep covers tags is deliberate. A comment or a note that
overclaims a control is itself a finding.

---

*This note is evidence of an owner decision about one revision's findings. It
is not a certification, not a guarantee, and not a statement that these items
are not worth thinking about. Each one was read, understood and accepted as
the design property it is.*
