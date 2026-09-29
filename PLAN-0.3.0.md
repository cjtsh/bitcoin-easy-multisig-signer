# 0.3.0 warm-work plan — agent and reviewer handoff

## Status and scope

Version 0.2.2 is published. The owner's latest Testnet4 payment was accepted by the broadcaster but has not yet been confirmed; the planned Trezor result has not yet been observed. The owner explicitly wants 0.3.0 work to proceed while Testnet4 confirmation is slow. Keep mainnet broadcast refused. The target user remains a spouse, lawyer, or accountant who should see plain instructions rather than protocol controls. No owner install is requested during intermediate changes; collect one focused walkthrough at the completed 0.3.0 milestone unless the existing device test exposes a defect.

## Work packages in safety order

1. **Private HWI transport.** Send the signing PSBT through HWI 3.2.0's documented `--stdin` path instead of a process command-line argument. Keep its device-type/path and network explicit. Test that subprocess argv contains no PSBT and that signer errors remain understandable. HWI's own 3.2.0 CLI source parses commands from stdin; package self-checks and later physical signing must cover the bundled binary.
2. **Transaction-state boundary.** Replace the parallel mutable `prepared_*` fields with one small immutable prepared-payment record holding the wallet/network, scan generation, review ID, verified selected outpoints and prevouts, outputs, fee, change policy and transaction ID. Check every sign/finalize/broadcast transition against it. A timed-out broadcast must be marked outcome-unknown rather than treated as a safe invitation to retry. Keep the browser flow unchanged.
3. **Current-output verification.** Immediately before preparation and again before broadcast, check selected outpoints are still unspent with a source independent of the scan. Prefer a user-run node when configured; otherwise use a separately operated Esplora backend with explicit disclosure wording. Verify the backend's genesis hash and fail closed on mismatch, stale or unknown status. A second explorer can detect disagreement but is not consensus proof, so call it a cross-check, not absolute verification. Keep the existing scan-limit warning.
4. **Fee and pending-payment policy.** Make the live fee quote age and fee ceiling visible in plain language. Define a bounded, explicit recovery path for congestion or a stuck payment. Never silently raise a fee, resend a transaction after an unknown broadcast result, or bypass the final device review. Document any remaining case that requires an established wallet or expert help.
5. **Release and privacy audit.** Review request/diagnostic surfaces, dependency locks, HWI and libusb provenance, and the supported wallet/device/export matrix. Developer ID signing and notarization still require the owner's Apple account and remain a separate distribution dependency. Build one immutable 0.3.0 DMG only after the full automated suite and source-archive tests pass.

## Acceptance gates

- Synthetic and loopback tests exercise agreement, disagreement, timeout, stale scan, and concurrent import/refresh/broadcast. No alternate network engine or automatic signing path is introduced.
- The GitHub Apple Silicon workflow passes its bundle, HWI, TLS, source, SBOM and checksum checks. Downloaded artifacts are verified independently.
- One owner walkthrough in the completed 0.3.0 Mac app checks the simple instructions, two device displays, final outputs and fee, and any pending-payment behavior. Testnet4 only unless the owner separately authorizes a mainnet operation.

## Work in progress

- HWI signing now passes a validated base64 PSBT on stdin, with no PSBT in subprocess argv. Focused tests and the full 150-test suite passed at the first checkpoint. The bundled HWI 3.2.0 binary from the verified 0.2.2 DMG accepted an option supplied through `--stdin`; physical signing with this change remains untested.
- A broadcast transport failure or malformed response is now an explicit **outcome unknown** state. The prepared payment is cleared so the app cannot blindly retry it, and the main screen directs the user to check the transaction on an explorer. Tests cover the local API lock. This is an initial transaction-state correction, not the full immutable-state refactor.
- The app now checks each selected outpoint immediately after construction and immediately before broadcast. Mainnet uses both the configured explorer and Blockstream's Esplora, after validating the second server's genesis. If Blockstream is the primary, mempool.space is the second. Only selected public transaction IDs and output numbers go to that second server; the UI consent wording discloses this. Testnet4 rechecks with its configured explorer because a reliably available independent public Testnet4 service has not been established. This is a limitation, not independent Testnet4 verification.
- Fee/replacement policy, the immutable prepared-payment refactor, and the final release audit remain open. Do not dispatch a 0.3.0 DMG yet.

## Sources for the transport and output-check design

- Bitcoin Core HWI 3.2.0 `_cli.py` exposes `--stdin` and parses a stdin command with `shlex` (tag `3.2.0`, GitHub commit `59eb7d8f57a898d61e28496a29e80774f782b996`).
- Bitcoin Core's [external signer guide](https://github.com/bitcoin/bitcoin/blob/master/doc/external-signer.md) uses `--stdin` for `signtx`.
- Blockstream's [Esplora API](https://github.com/Blockstream/esplora/blob/master/API.md) defines transaction status and outspend endpoints. Before choosing a second public service, verify its Testnet4/mainnet genesis response, independence and availability; do not silently disclose wallet addresses to it.
