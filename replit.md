# Agent entry point

Read `AGENTS.md`, `PHASE-HANDOFF.md`, `SECURITY-REVIEW-0.2.0.md`, then source and tests. `PROJECT-HISTORY.md` and the earlier phase detail in `ROADMAP.md` are archives. The app's user is a nontechnical spouse or estate professional; keep descriptor complexity in automatic checks, not on the main screen.

One engine serves Testnet4 and mainnet. The app reads an existing BSMS wallet, scans via Esplora, builds a PSBT, asks HWI hardware signers to sign, verifies the returned signatures and final transaction, and broadcasts only to Testnet4. Mainnet broadcast is refused. It never creates wallets or requests seeds/PINs. Receive-only exports are Send All only because they do not establish change ownership.

0.2.0 is the hot-audit-fix milestone. Do not claim physical-device acceptance until the owner completes one controlled Testnet4 walkthrough. Use 0.2.x for a correction after publication, 0.3.0 for warm items and 0.4.0 for nice-to-have items. The Mac workflow is manual dispatch only, with hash-locked dependencies and a required libusb digest. Do not republish an existing version or put wallet material in source, diagnostics or CI.
