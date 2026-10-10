# 0.6.8: Color Team cycle-4 remediation

Version 0.6.8 answers the cycle-4 Color Team audit of the `v0.6.7` tree
(`bitcoin-easy-multisig-signer-colorteam-audit-plan-d525f31.md`). The
cycle's finding set is worked through in `releases/PLAN-0.6.8.md`; this
ledger records, item by item, what changed and the test that was watched
failing without it.

The cycle-4 grade was set on the build process again: what the release
workflows install, and what they leave unchecked. The wallet,
transaction, signing and broadcast engine is unchanged apart from the
hardening items below. No new payment capability is added.

## Finding → fix → test

Every row below is closed either by a test demonstrated able to fail or
by a dated owner acceptance note. Nothing is closed by silence.

| ID | Sev | Fix | Closing evidence |
| --- | --- | --- | --- |
| CT-87 | Med | The container proof runs a digest, not a moving tag. The runner's apt set is declared once (`SYSTEM_PACKAGES` in `scripts/build-linux.sh`), asserted to be exactly what the workflow installs, and the version each resolved to is written into the SBOM by `dpkg-query` (fail closed if a declared package is absent). Exact apt version pins are **declined** for the runner image and recorded below as accepted floating inputs. | `tests/test_workflow_config.py::ToolchainPinTests::test_the_container_proof_runs_a_digest_not_a_moving_tag`, `…test_the_runner_packages_are_the_ones_the_build_script_declares`, `…test_every_floating_input_is_written_down`; `tests/test_build_sbom.py::SystemPackageTests` |

## CT-87: the build's floating inputs

### The container proof runs a digest, not a tag

`ubuntu:24.04` is a moving pointer: it is republished as the image is
rebuilt, so a proof run against the tag says nothing durable about what
ran. The proof now names the manifest-list digest
`sha256:534baea6a22c03a63003dbc8dbe78fe34bc0d7e595d9a9dc9834884ff530eb55`
(published 2026-10-04), and the recipe records the command that refreshes
it so the next reader moves it deliberately:

```
docker buildx imagetools inspect ubuntu:24.04 --format '{{.Manifest.Digest}}'
```

### The runner's packages are declared once and recorded

The four packages the Linux build installs — `squashfs-tools`,
`librsvg2-bin`, `build-essential`, `fuse3` — are declared once, in
`scripts/build-linux.sh` as `SYSTEM_PACKAGES`. The workflow installs
exactly those names (a test compares the two lists), and every Linux
build writes the version each one resolved to into
`dist/BUILD-SBOM.json` with `dpkg-query`, failing closed if a declared
package is not installed. A reader of the SBOM can therefore see the
build's OS inputs even though they are not pinned.

### Accepted floating inputs

Pinning the runner's packages to exact versions is **declined**. The
runner image's `noble-updates` and `noble-security` archives move as
Canonical ships fixes; a pinned version would fail the build on a runner
refresh without making the AppImage's bytes reproducible, because the
package is only one input among many and the pin would have to be
re-derived by hand on every refresh anyway. A pin that breaks the build
and buys nothing is not a control.

What is accepted, and what stands in for the pin:

- **The runner image's packages**: `squashfs-tools`, `librsvg2-bin`,
  `build-essential`, `fuse3`, resolved from the `ubuntu-24.04` runner's
  archives. Recorded per build in the SBOM (name and version). Declared
  once in `scripts/build-linux.sh`; a test asserts the workflow installs
  exactly that set.
- **The proof container's packages**: `fuse3` and `ca-certificates`,
  installed inside the digest-pinned `ubuntu:24.04` container. Printed
  into the run log; the proof is a pass/fail assertion about the
  AppImage, not shipped bytes.
- **The container image**: pinned by the digest above; refresh command
  recorded beside the pin and in this section.

A review of this release should re-run the refresh command, move the
digest, and, if any of the four runner packages changes, update
`SYSTEM_PACKAGES`, this section, and the SBOM expectations in the same
commit.
