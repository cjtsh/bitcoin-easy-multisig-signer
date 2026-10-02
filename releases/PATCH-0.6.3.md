# v0.6.3 — legal and privacy disclosure updates

**Source update; not built or published.** The latest published app remains
v0.6.2. This patch updates the source and packaging recipe; it does not change
transaction construction, signing, or broadcast behavior.

## Changes

- Identifies Bitseeker LLC as project maintainer and publisher in current legal,
  website, manual, and app copy. The public project materials do not print the
  member-manager's personal name.
- Replaces stale “experimental” language in the app source and current screenshots
  with measured wording about open source, no warranty, and the absence of a
  recorded independent end-to-end review of the current release.
- Adds a project privacy notice describing website hosting, local data handling,
  public explorer requests, broadcasts, optional diagnostics, and saved PSBTs.
- Adds private security reporting and contribution guidance.
- Includes the safety and privacy notices in the next Mac app bundle recipe and
  checks for their presence in the packaged resource directory.
- Clarifies that the third-party summary is not a replacement for upstream
  license terms, and removes an overbroad statement about LGPL compliance.

## Evidence and release gate

No build, automated test suite, device walkthrough, or security audit is claimed
by this source-only record. Before publishing a v0.6.3 binary, run the required
release checks, review third-party license materials for every bundled
component, build and verify the Apple Silicon app, and publish the matching
source and artifact checksums. A source update does not change the already
published v0.6.2 DMG.
