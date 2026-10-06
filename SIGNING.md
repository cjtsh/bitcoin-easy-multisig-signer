# Signing and provenance — every platform, one process

This file is the project's signing policy. It exists so a release never again
depends on who happened to build it or which machine it came from. It is written
for two readers: the owner preparing a release, and any coding agent asked to
touch a build or release file. **Agents: read this before editing anything under
`.github/workflows/` or `scripts/build-*`.**

## The principle

Provenance first, signatures where they exist. Every download must be provably
the bytes the gated pipeline produced from the tagged commit — nothing built by
hand, nothing uploaded by hand, nothing checksummed by hand. Where a platform
also supports a real code signature, we use it; where it does not (yet), we say
so plainly and let the provenance chain carry the trust.

## What each platform carries today

| Platform | Code signature | Provenance (all platforms) |
|---|---|---|
| macOS | Developer ID signing **and Apple notarization** — full platform signature | Built from the tagged commit in one dispatch-only workflow run; covered by CI-generated `SHA256SUMS`; `SHA256SUMS.asc` signed by the release key; Sigstore build attestation per asset |
| Windows x64 | **Unsigned** (no Authenticode certificate; a future Windows Store submission would be signed at store level) | Same chain |
| Linux x86_64 | **Unsigned** (conventional for Linux distribution) | Same chain |

"Unsigned" here is a policy state, not a process failure: the bytes are
CI-built from the exact tagged commit, hash-covered, release-key-signed at the
manifest level, and attested. What an unsigned asset does *not* prove is
publisher identity to the operating system, which is why Windows and Linux
first-launch may show an OS warning, and why the verification steps below
matter.

## The one release pipeline

`.github/workflows/build-candidate.yml` is the **only** build and publish path.
It is dispatch-only; a push can never publish. One run builds macOS, Windows,
Linux and the source archive from the same commit, generates one `SHA256SUMS`,
and — on the publish path only — signs it and attests every asset. The retired
per-platform workflows (`build-windows.yml`, `build-linux.yml`) must not
return: a second publish path is how unverified bytes once reached a tagged
release (audit CT-01/CT-02).

Release flow, unchanged from the audited macOS process, now covering all three:

1. Dispatch `notarize=true, publish=false` → a signed, notarized candidate for
   every platform. Test it.
2. Dispatch `publish=true` with that candidate's run ID → the pipeline verifies
   the candidate's identity and bytes, signs `SHA256SUMS.asc`, attests every
   asset, and publishes one release carrying all platforms.

## The release GPG key (one-time setup)

`SHA256SUMS.asc` lets anyone verify the checksum manifest with `gpg`, the
standard Bitcoin-community verification habit. Publishing **fails closed**
without this key.

1. Generate a dedicated release key (sign-only, 4096-bit):
   ```bash
   gpg --full-generate-key
   # RSA (sign only), 4096 bits
   # Name:  Bitcoin Easy Signer release key
   # Email: release@bitseeker.com
   ```
2. Commit the **public** key to the repository root so downloaders can import it:
   ```bash
   gpg --armor --export release@bitseeker.com > signing-key.asc
   git add signing-key.asc && git commit -m "Add the release signing public key"
   ```
3. Add two repository secrets (Settings → Secrets and variables → Actions):
   - `GPG_PRIVATE_KEY` — the armored **private** key
     (`gpg --armor --export-secret-keys release@bitseeker.com`)
   - `GPG_PASSPHRASE` — the key's passphrase (empty secret if none)

Guard the private key like the Apple credentials: it is publisher identity.
The public key in the repo is how a downloader checks `SHA256SUMS.asc`; the
release job verifies the signature against that committed key before anything
is published.

## How a downloader verifies any asset

```bash
# 1. The checksums match the CI-generated manifest
shasum -a 256 -c SHA256SUMS

# 2. The manifest was signed by the release key committed in the repo
gpg --import signing-key.asc
gpg --verify SHA256SUMS.asc SHA256SUMS

# 3. Each asset is attested to the exact workflow run and commit
gh attestation verify Bitcoin-Easy-Signer-v<version>-windows-x64.zip \
  --repo cjtsh/bitcoin-easy-multisig-signer
```

macOS users get a fourth check for free: Gatekeeper verifies the Developer ID
signature and notarization ticket on first launch.

## Hard rules for agents

- **Never** upload, edit, or delete release assets by hand — the pipeline is
  the only writer. If assets are wrong, fix the pipeline and re-run it.
- **Never** edit `SHA256SUMS` outside CI, and never create a workflow that
  calls `gh release create`, `gh release upload`, or `gh release edit`.
- A published tag is never rebuilt or replaced. Bump `version.py` instead.
- Windows and Linux assets stay labeled unsigned until a real certificate
  exists; do not describe them as signed, and do not hide the OS warning in
  documentation.
- Actions stay pinned to full commit SHAs; dependency locks stay hash-locked.
- The macOS gates (notarize-then-publish, candidate promotion, no-overwrite)
  are load-bearing for every platform now; do not relax them for one platform
  "just this once."
