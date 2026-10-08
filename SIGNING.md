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
per-platform workflows (`build-windows.yml`, `build-linux.yml`) are deleted
from every branch and must not return on any branch: a second publish path is
how unverified bytes once reached a tagged release (audit CT-01/CT-02).
`scripts/check-publish-paths.sh` enforces this as a gate on every dispatch and
names the offending ref if one reappears. Historical tags freeze their
commit's workflow text, so the dispatch ref is always `main` and never a tag.

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

1. Generate a dedicated release key (sign-only, 4096-bit) in the company
   name — publisher identity is Bitseeker LLC, matching the Apple Developer
   ID, not an individual:
   ```bash
   gpg --full-generate-key
   # RSA (sign only), 4096 bits
   # Name:  Bitseeker LLC
   # Email: release@bitseeker.llc
   ```
2. Commit the **public** key to the repository root so downloaders can import it:
   ```bash
   gpg --armor --export release@bitseeker.com > signing-key.asc
   git add signing-key.asc && git commit -m "Add the release signing public key"
   ```
3. Add the two secrets to the **`release-signing` environment**, never as
   repository secrets (Settings → Environments → `release-signing` → Environment
   secrets — see "Where the release credentials live" below):
   - `GPG_PRIVATE_KEY` — the armored **private** key
     (`gpg --armor --export-secret-keys release@bitseeker.com`)
   - `GPG_PASSPHRASE` — the key's passphrase (empty secret if none)

Guard the private key like the Apple credentials: it is publisher identity.
The public key in the repo is how a downloader checks `SHA256SUMS.asc`; the
release job verifies the signature against that committed key before anything
is published.

## Where the release credentials live (CT-97)

The signing credentials are **not** repository secrets. They live in two
protected environments, each deployable only from `main`:

| Environment | Credentials | Deployment rule |
|---|---|---|
| `release-signing` | `GPG_PRIVATE_KEY`, `GPG_PASSPHRASE` | `main` only, and the owner approves each deployment |
| `apple-signing` | `MAC_CERT_P12_BASE64`, `MAC_CERT_PASSWORD`, `MAC_APP_SPECIFIC_PASSWORD` | `main` only, no approval |

`.github/workflows/build-candidate.yml` declares the environment on the job that
needs it: `macos` → `apple-signing`, `checksums` → `release-signing`. The GPG
step already runs only under `if: ${{ inputs.publish }}` and the Apple steps only
under `if: ${{ inputs.notarize }}`, so the approval pauses a promotion and never
a candidate build. A repository-level secret is handed to a job on **any** ref,
so without this a dispatch at a historical tag would run that tag's own frozen
workflow text with today's signing keys; all 66 tags from `v0.1.0` on carry a
dispatchable `build-candidate.yml` and the pre-0.6.4 ones lack the
default-branch guard. Tags are immutable history and cannot be repaired, so the
fix is a rule about which ref a run is on: an old tag never declares the
environment and gets nothing, and a **future** tag inherits the workflow text
that does declare it but still cannot deploy, because the environment admits
`main` only. That is what makes this hold for tags that do not exist yet.

Rules:

- **Never** add a release credential back as a repository secret. Environment
  secrets are *added to* repository secrets, so a surviving repository-level copy
  would keep supplying every ref.
- A credential can only be moved by re-entering its value: GitHub never returns a
  secret's value, not even to an administrator.
- `scripts/check-release-credentials.sh` is the standing, read-only check. Run it
  before every promotion and in every audit cycle. It refuses (exit 1) if a
  release credential sits at repository level, an environment is missing, an
  environment's branch policy is not exactly `main`, an environment's secret set
  is not exactly the expected one, or `release-signing` has no required reviewer.
- `tests/test_workflow_config.py` fails the build if a job names one of these
  credentials without declaring its environment, if the job→environment map
  changes, or if any other workflow file names a credential at all.

**Moving the credentials (owner, one time).** The two environments exist and admit
`main` only, but the values still sit in the repository-level secrets. GitHub never
returns a secret's value to anyone, so each one is re-entered:

1. Settings → Environments → `release-signing` → Environment secrets: add
   `GPG_PRIVATE_KEY` (the armored private key) and `GPG_PASSPHRASE`.
2. Settings → Environments → `apple-signing` → Environment secrets: add
   `MAC_CERT_P12_BASE64`, `MAC_CERT_PASSWORD`, `MAC_APP_SPECIFIC_PASSWORD`.
3. Run `scripts/check-release-credentials.sh`. It will name every
   repository-level copy it can still see.
4. Settings → Secrets and variables → Actions: delete the five repository-level
   copies. **The control is not armed until this step**, because environment
   secrets are added to repository secrets.
5. Run `scripts/check-release-credentials.sh` again. It must print
   `ok: the release credentials are environment-scoped, main-only, and
   unreachable from any tag`. Do this before the next promotion.

With the `gh` CLI the same move is one command per secret, reading each value
from a file so it never enters the shell history:

```bash
gh secret set GPG_PRIVATE_KEY --env release-signing --repo cjtsh/bitcoin-easy-multisig-signer < ~/gpg-private-key.asc
gh secret delete GPG_PRIVATE_KEY --repo cjtsh/bitcoin-easy-multisig-signer
```

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
