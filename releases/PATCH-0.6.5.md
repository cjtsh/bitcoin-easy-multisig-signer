# 0.6.5: unified three-platform release and Color Team audit remediation

This record has two parts: the unified 0.6.5 release on main (below), and the
earlier Windows-only `v0.6.5-windows-x64` candidate record (further down),
kept intact as the acceptance evidence for the Windows console fix.

## Part 1 — the unified 0.6.5 (audit remediation, on main)

The Color Team audit of v0.6.4 (report in the repository root) graded the cycle
BLOCKED on release-channel findings: hand-uploaded Windows assets from an
unmerged commit (CT-01), Linux assets from a failed run at another unmerged
commit (CT-02), and a dead substituted-embit guard in the source-mode launcher
(CT-04); it separately capped the grade at CONDITIONAL for unpinned on-path
controls (CT-03, CT-05, CT-15). Version 0.6.5 answers all three classes:

- The windows-port and linux-port branches are merged onto one tree; the ports'
  app-code deltas (platform renderer selection, startup failure reporting,
  per-platform settings paths, `hwi.exe` bundling, `assert_private_file`) are
  reviewed, additive and platform-gated. The macOS build machinery the forks
  had deleted is restored intact.
- `.github/workflows/build-candidate.yml` builds macOS, Windows and Linux from
  the same commit in one dispatch-only run and is the only publish path;
  `build-windows.yml` and `build-linux.yml` are retired. `SHA256SUMS` is
  CI-generated over every asset, GPG-signed at publish (`SHA256SUMS.asc`;
  fails closed without the release key), and every asset carries a Sigstore
  build attestation. `SIGNING.md` is the standing signing/provenance policy.
- CT-04 fixed: the launcher asserts the pinned embit `0.8.2+besa.1`, pinned by
  `tests/test_launcher.py`. CT-03, CT-05, CT-07–CT-12, CT-15 are pinned by new
  fail-capable tests; CT-06 moves diagnostics to a fixed device-class
  whitelist; CT-18/CT-19/CT-24 are corrected. Every pin was break-and-watch
  verified (the guarding test fails when the control is deleted). CT-13 and
  CT-14 are deferred by decision and recorded open in CURRENT-STATUS.md.
- The wallet, transaction, signing and broadcast engine is unchanged from the
  audited 0.6.4.

Owner-reported functional acceptance: the port-built Windows
(`v0.6.5-windows-x64`, Part 2 below) and Linux (AppImage, see
`releases/LINUX-0.6.4-ACCEPTANCE.md`) builds were exercised through signing
and, on Linux, a full transaction; the unified 0.6.5 rebuilds the same code
through the gated pipeline. Publication of the unified 0.6.5, a cycle-2 audit
plan pinned to its tag, and the cycle-2 audit are pending at this writing.

---

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
"worked great no popups!" This closes the console-window acceptance check.
Transaction network, broadcast and confirmation were not supplied.
macOS 0.6.4 branch, tag and published assets remain unchanged.
