# Agent guide

## Read order

1. `README.md` for current user-visible behavior and supported scope.
2. `PHASE-HANDOFF.md` for current status, version gates and owner test.
3. `SECURITY-REVIEW-0.2.0.md` for the audit finding-to-fix map and evidence.
4. Current source and tests. `ROADMAP.md` and `PROJECT-HISTORY.md` preserve history and can describe older releases.

## Architecture

One engine serves Testnet4 and mainnet. `probe.py` parses BSMS and checks public hardware identities; `wallet_service.py` resolves wallet paths, scans via Esplora and builds PSBTs; `signing.py` binds and verifies HWI signing updates and finalizes native-SegWit multisig. `gui.py` owns loopback API/session state, fee/price references, signing and broadcast gates; `ui.html` is the shared interface; `desktop.py` wraps it in a Mac WebKit window. `network_config.py` is the network parameter switch. `safe_http.py` refuses redirects and keeps TLS verification on. Never create a second transaction or signing engine for mainnet.

## Invariants

- No seed, PIN or private key input, wallet creation, silent signing, or unapproved mainnet broadcast.
- A receive-only reference address proves only receive. Partial sends need declared change ownership. Without it, only a no-change Send All of confirmed outputs found by the scan is available.
- A PSBT input must match an independently fetched historical transaction and the wallet's derived script/value. A signer may add valid partial signatures but may not change the reviewed PSBT metadata or remove prior signatures.
- Before broadcast, verify every signature, witness/prevout, output, fee and txid against immutable reviewed state. The final screen must show the same fields. A concurrent request must not change the payment during submission.
- Treat public explorers and fee quotes as observations. Never call a gap-limited scan a complete wallet sweep. Never silently fall back to a different server.
- Do not commit or emit BSMS records, xpubs, addresses, PSBTs, raw transactions, settings, device paths, or real wallet/test artifacts. Diagnostic reports use only fixed codes and timestamps.

## Development and release

Use Python 3.12 for HWI 3.2.0. Run the full suite, JS syntax, `bash -n`, source archive tests and packaged Apple Silicon checks. Dependency locks are hash-verified. `LIBUSB_SHA256` is mandatory for the Mac build. The GitHub workflow is manually dispatched; pushes alone must not publish. Never replace an existing release's assets. Use 0.2.x for hot-fix corrections, 0.3.0 for warm items, and 0.4.0 for nice-to-have items.

Keep the nontechnical operator's screen simple. Make technical checks automatic and explain unsupported conditions in plain English. The owner wants one Mac install and transaction walkthrough per milestone after extensive automation, not repeated manual tests for small revisions. No agent may claim 0.2.0 hardware acceptance before the owner reports it.
