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
| CT-88 | Low | Every digest `vendor/README.md` states was prose with nothing checking it. `tests/test_vendor_pins.py::VendorPinTests` hashes the committed bytes, asserts the README states each digest, and refuses a file in `vendor/` that no digest covers. The README's regeneration command is real: `scripts/vendor-digests.py` is run by the test and must reproduce the recorded digests. | `tests/test_vendor_pins.py::VendorPinTests` (byte-flip break-and-watch in a disposable copy) |
| CT-89 | Low | `probe.py` claimed to refuse a BSMS whose receive and change branches used different multisig keys. Both branches are expanded from the one `/**` template, so the refusal could never fire. It was **deleted** rather than left in place: a check no accepted input can trip is a claim, not a control. Two tests hold the ground it claimed — the change branch is the receive wallet by construction, and the deleted claim cannot come back unargued. | `tests/test_probe.py::ProbeTests::test_the_expanded_change_branch_is_the_receive_wallet`, `…test_no_refusal_claims_a_key_agreement_the_template_cannot_violate`; `CONTROLS.md` records that no control is claimed here |

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

## CT-88: the vendored digests were prose

`vendor/README.md` stated seven SHA-256 digests and nothing checked any
of them. Each is an input to a signed release — two embit archives, the
embit wheel both lock files require, the libusb dylib, the libusb source
tarball, the Windows DLL, and the AppImage runtime — so a changed byte
would have shipped against a README that still claimed the old value.

`tests/test_vendor_pins.py::VendorPinTests` now asserts three things,
each one a way a prose digest goes wrong:

- every registered file hashes to the digest the README states;
- the README states every registered digest, so editing the prose alone
  breaks the check rather than silently changing what is claimed;
- every file in `vendor/` is either registered or listed in the test
  with a reason it is not (the README itself, `libusb-COPYING`, and the
  generated `hwi-payload-3.2.0.json`, which `build-hwi-manifest.py
  --check` already covers).

The regeneration command the README documents is not prose either:
`scripts/vendor-digests.py` prints `digest  name` for the directory, and
the test runs it and requires it to reproduce the recorded digests.

Break-and-watch, per the plan, is a flipped byte in a disposable copy
rather than in the committed file:

```
cp -R vendor /tmp/vendor-scratch
python -c "from pathlib import Path; p = Path('/tmp/vendor-scratch/embit-upstream-2b375a.tar.gz'); d = bytearray(p.read_bytes()); d[100] ^= 0xFF; p.write_bytes(bytes(d))"
VENDOR_DIR=/tmp/vendor-scratch python -m unittest tests.test_vendor_pins
```

which reports the flipped file as

```
AssertionError: '5e51f2fe3ee28b9e36dd5127efc215c4df1185e151485c99146c67f1bb425068'
!= '3323c77583432be513b346bdc54f86f7ef5fb259e1db0e60975dc51bcbceb0a3' :
embit-upstream-2b375a.tar.gz does not match its recorded digest
```

## CT-89: a refusal that could never fire

`parse_bsms` accepted a BIP 129 `/**` template by expanding it twice —
once to `/0/*` for receive and once to `/1/*` for change — and then
claimed to refuse the result if the two branches did not use the same
multisig keys:

```python
if change_descriptor is not None:
    ...
    raise ProbeError("BSMS receive and change descriptors do not use the same multisig keys.")
```

Both branches come from the same `descriptor_text` through `str.replace`,
so their key sets and thresholds are equal by construction. A BSMS record
cannot express a change branch with different signers, which means the
`if` had no input that could reach it. The audit row named the choice:
make the rejection reachable, or delete it. **It was deleted.**

The reason is the rule this cycle is applying elsewhere: a check no
accepted input can trip is a claim about the code, not a control over it,
and a reader who trusts it stops looking. What the claim was standing in
for is now a stated invariant with a test on it — the change branch is
the receive wallet:

- `test_the_expanded_change_branch_is_the_receive_wallet` asserts the
  `/1/*` branch carries the same signer set, the same threshold, and the
  same native-SegWit `wsh` shape as the `/0/*` branch. If the expansion
  ever stops guaranteeing that, this fails and the refusal has to come
  back as a check that can actually fire.
- `test_no_refusal_claims_a_key_agreement_the_template_cannot_violate`
  reads `probe.py` and fails while the deleted message is present. That is
  the test that was watched failing first:

```
self.assertNotIn("do not use the same multisig keys", source)
AssertionError: 'do not use the same multisig keys' unexpectedly found in '...'
```

`break_and_watch.py` carries two defeats for it: reinstating the deleted
refusal (caught by the removal pin) and expanding the change branch with
a threshold of its own (caught by the invariant test). The comment left
at the expansion site says why no key-agreement check is needed, and
`CONTROLS.md` records that no control is claimed here.
