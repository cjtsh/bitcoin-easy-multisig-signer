# Windows 0.6.5 candidate: hide hardware helper consoles

The Windows 0.6.4 owner walkthrough reported correct wrong-network rejection
and successful transaction signing with Jade and Trezor 3. Broadcast and chain
confirmation were not reported. Repeated blank terminal windows appeared during
hardware use.

Windows 0.6.5 adds CREATE_NO_WINDOW to both HWI launch paths: the desktop
capability probe and discovery, identity verification and signing requests.
Captured stdout/stderr, stdin PSBT transport, timeouts and device authorization
remain intact. Wallet, transaction, signature verification and broadcast logic,
dependency pins and the macOS source branch are unchanged.

Regression coverage checks both launch paths, non-Windows options, and an actual
Windows child process with no attached console and working stdin/stdout/stderr.
Candidate packaging and owner verification remain required before promotion.
Build through build-windows.yml with publish=false; promote the same tested bytes
through that workflow only. Never replace v0.6.4 assets.
