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

## Publication and owner acceptance

Published as v0.6.5-windows-x64 through workflow 37264663578, promoting
candidate 37264196917 from commit 897e9e6. Published ZIP SHA-256:
`af4ee135c485b99176ffe1114af9cff09670b44a56302d8fa3d9425f94475679`.
On 2026-10-05 the owner downloaded the release from GitHub and reported
"worked great no popups!" The owner clarified this was startup only; no transaction was completed
in 0.6.5. Hardware-flow console suppression remains unverified. Linux testing
is next. Transaction network, broadcast and confirmation were not supplied.
macOS 0.6.4 branch, tag and published assets remain unchanged.
