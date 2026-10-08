# Bitcoin Easy Signer 0.6.8

This release answers the Color Team's fourth audit, which reviewed v0.6.7
and graded the repository BLOCKED. This time the grade was not set by
process: two independent things set it, and both are fixed here. One lane
proved that the check on the hardware helper could be made to **pass**
while substituted code ran inside the check itself. Another found a wallet
file that could display as an honest 2-of-2 wallet while **one** device
approval was enough to pay. Every fix is held by a test that was shown able
to fail. The wallet, signing, and broadcast policy is unchanged, and no new
payment capability is added.

## What changed

- **A wallet file that names the same signer key twice is refused.** The app
  used to count the fingerprint labels attached to keys, so the same key with
  two labels looked like two different cosigners. It counts the keys
  themselves now — a fingerprint is a label, the key bytes are the signer.
- **The helper identity check no longer runs the library it is checking.**
  It locates the library files and hashes them without executing them, and
  the check and the helper now run under the same isolated interpreter. A
  substituted library can therefore no longer execute inside the check and
  then lie about which file it is.
- **A helper swapped during a signing session is no longer trusted.** Each
  cached identity is re-hashed before it is believed.
- **The two public reference feeds now require the session token**, like
  every other route, and a request whose token header carries unusual
  characters gets the ordinary "local access only" refusal instead of a
  dropped connection.
- **The release guards are pinned one refusal at a time** — a guard that
  stops refusing fails a test; the publish-path sweep now recognizes REST
  and third-party publishers and requires a read-only token from any
  non-main branch that carries a workflow; the CI container proof runs a
  digest-pinned image; and the release dispatcher's run id reaches its check
  as data, never as code.
- **Every per-platform SBOM now records the toolchain that built it**, so
  drift inside a runner image is visible in the artifact, and the source
  download now includes `signing-key.asc`, which the verification
  instructions already told a tarball-only verifier to import.

## One item the owner had to decide

Historical release tags can still be dispatched, and a workflow frozen at such a
tag reads whatever secrets the repository holds today. All 66 tags from
`v0.1.0` on carry a dispatchable publisher and the pre-0.6.4 ones lack the
default-branch guard, and those tags cannot be edited without moving published
tags, which this project forbids. The owner directed the fix on 2026-10-07: the
signing credentials are scoped to two protected GitHub environments —
`release-signing` (the release GPG key, `main`-only, owner approval required)
and `apple-signing` (the Apple identity, `main`-only, no approval) — and the
jobs that use them declare their environment. An old tag never declares the
environment, and a tag created in the future still cannot deploy to it, so the
protection extends to tags that do not exist yet. What remains is the owner's
value move: re-enter the five secrets into the environments (GitHub never
returns a secret's value) and delete the repository-level copies, then run
`scripts/check-release-credentials.sh`, which refuses until that is complete.
See [`SIGNING.md`](../SIGNING.md) and
[`releases/PATCH-0.6.8.md`](PATCH-0.6.8.md).

## Downloads

**Not yet published.** When it is, verify every download against
`SHA256SUMS` and its `SHA256SUMS.asc`; the release carries one checksum
file covering macOS, Windows, and Linux, plus `BUILD-SBOM.json`. See
[`SIGNING.md`](../SIGNING.md) for the signature and provenance policy.
