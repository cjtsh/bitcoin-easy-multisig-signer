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
| CT-91 | Info | The vendored embit's Liquid/PSET copy kept upstream's `sequence=(self.sequence or 0xFFFFFFFF)`, which rewrites a legal `nSequence=0`; the fork had already fixed that shape in `src/embit/psbt.py`. Both properties in `src/embit/liquid/pset.py` (`vin`, `blinded_vin`) now carry the same explicit check, and the fork's whole delta is machine-held: the wheel must be the archive's `src/embit` tree in both directions, the implicit form must appear nowhere, and no shipped module may import the Liquid surface. | `tests/test_embit_vendor.py::EmbitVendorTests::test_source_diff_is_only_the_declared_version_and_sequence_fixes`, `…test_no_liquid_input_rewrites_a_legal_sequence_of_zero`, `…test_the_wheel_carries_the_source_it_was_built_from`, `…test_the_documentation_states_the_liquid_delta`, `…test_the_application_does_not_import_the_liquid_surface` |
| CT-92 | Low | The source-mode install pinned one library and guarded one library. `requirements.lock` carried the embit wheel and nothing else, `Start Easy Multisig.command` guarded only that version, and `probe.py` refused with "Install hwi 3.2.0 to use devices." — no command, and a venv created before the device library was wanted was never repaired. Added `requirements-source.txt` → `requirements-source.lock`: hwi 3.2.0 and its whole closure under `--require-hashes`, every version and hash set constrained to the reviewed `requirements-desktop.lock`; the launcher now guards both libraries and installs the source lock; the refusal names the exact command. | `tests/test_launcher.py` (9 tests), `tests/test_build_source.py::ArchiveCompletenessTests::test_the_source_mode_lock_reaches_the_archive`; break-and-watch: the lock loses hwi, the lock drifts, the guard drifts, the refusal loses the command |

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

## CT-91: the vendored Liquid copy rewrote a legal sequence

Upstream embit writes a PSBT input's sequence as
`sequence=(self.sequence or 0xFFFFFFFF)`. When the field is a legal
`0` — the value that says the input is final and does not signal
BIP 68 — Python's `or` replaces it with the maximum, so the sequence
that was read is not the sequence that is written. The fork had already
corrected that shape in `src/embit/psbt.py`:

```python
sequence=(0xFFFFFFFF if self.sequence is None else self.sequence)
```

but the Liquid/PSET copy in `src/embit/liquid/pset.py` still carried the
upstream form in both `vin` and `blinded_vin`. The audit row (CT-91,
Info) offered two closes: patch the vendored copy as part of the next
embit delta, or record it with an explicit trigger. **It was patched,
because the fork should ship one behaviour rather than two and the fix
is one line.**

What holds it now is not the patch but the tests around it:

- `test_no_liquid_input_rewrites_a_legal_sequence_of_zero` asserts the
  implicit form appears zero times and the explicit form twice, in
  **both** the source archive and the built wheel, so a corrected
  archive with a stale wheel cannot pass.
- `test_the_wheel_carries_the_source_it_was_built_from` compares every
  packaged `embit/**` file against the archive's `src/embit/**` tree in
  both directions — missing, mismatched and extra each fail. That is the
  `diff -r` the plan asked for, held rather than performed once.
- `test_source_diff_is_only_the_declared_version_and_sequence_fixes`
  narrows the whole fork delta to three files and reproduces each of the
  three edits from upstream bytes, so a fourth edit cannot arrive
  unrecorded.
- `test_the_application_does_not_import_the_liquid_surface` keeps the
  reason `Info` is honest: if a shipped module ever imports embit's
  Liquid surface, this delta is on a money path and the row has to be
  re-graded.

The artifacts changed, so all four locks, `vendor/README.md` and
`tests/test_vendor_pins.py` moved with them:

| Artifact | SHA-256 |
| --- | --- |
| `vendor/embit-0.8.2+besa.1.tar.gz` | `6974ac6dec0866ebbb5ab1f6e17cc78b187bedb40a31e514c94d50d2a3df0ad6` |
| `vendor/embit-0.8.2+besa.1-py3-none-any.whl` | `41a5e7e850a09f58cae0819ead68a96c4600f90b4e83a5a82f6af49b9d5660ba` |

The archive was rebuilt by rewriting the one changed member in place, so
every other member's path, bytes, mode and timestamp are what they were
— the delta really is one file. The tests were watched failing first,
against the old artifacts:

```
AssertionError: 0 != 2 : the Liquid/PSET copy keeps upstream's
`or 0xFFFFFFFF` in vin or blinded_vin
AssertionError: 2 != 0 : the source archive still rewrites a legal
nSequence=0 to 0xFFFFFFFF
AssertionError: 0 != 1 : vendor/README.md does not name the
Liquid/PSET edit exactly once
```

and `break_and_watch.py` carries the defeats for the claims that a text
mutation can reach: the readme stops naming the Liquid file, the notices
stop counting the edits, and a shipped module imports the surface. The
artifact claims are broken the same way CT-88's were — a scratch copy
holding the pre-CT-91 wheel and archive makes three controls fail
(`test_source_diff_is_only_the_declared_version_and_sequence_fixes`,
`test_no_liquid_input_rewrites_a_legal_sequence_of_zero`, and the older
`test_bundled_wheel_is_hash_locked_and_contains_no_native_code`, which
is what pins the wheel hash in the locks).

## CT-92: the source install pinned one library and guarded one library

`requirements.txt` is one line — the vendored embit wheel — and
`requirements.lock` was compiled from it, so source mode installed embit and
stopped. `Start Easy Multisig.command` guarded exactly that:

```
if ! .venv/bin/python3 -c 'import importlib.metadata as m; raise SystemExit(0
if m.version("embit") == "0.8.2+besa.1" else 1)' >/dev/null 2>&1; then
```

A venv created before the device library was needed therefore satisfied the
guard forever and never installed HWI, while the refusal the user actually
meets said:

```
The pinned hardware-wallet library is not installed in this environment.
Install hwi 3.2.0 to use devices.
```

Neither the message nor `HWI-DEPENDENCY.md` named an install command.

**What changed.** A source-mode lock set, in the shape of the existing desktop
one: `requirements-source.txt` is `-r requirements.txt` plus the two extras and
`-c requirements-desktop.lock`; `requirements-source.lock` is the resolved,
hash-verified closure (22 entries: 21 packages plus the wheel file line). The
constraint is the load-bearing part. A fresh resolve today picks *newer* builds
than the release was reviewed with — `charset-normalizer 3.5.2`,
`cryptography 50.0.2` and `pycparser 3.11` against `3.5.1`, `50.0.1` and `3.0`
in `requirements-desktop.lock` — so an unconstrained source install would run a
different build of the same library than the bundle. With the constraint every
source entry is identical in version *and* hash set to its desktop counterpart,
and a test checks that rather than an eye. `Start Easy Multisig.command` now
tests both libraries through `importlib.metadata` (never importing them, so the
launcher cannot be the first thing to execute the library `probe.py` hashes) and
installs `--require-hashes -r requirements-source.lock`; `probe.py` names that
same command; `HWI-DEPENDENCY.md` gains an "Installing it, by mode" section and
its bump procedure now says the pin has three consumers and every lock is
regenerated, the source lock last. The three CI test jobs deliberately stay on
`requirements.lock` and its `hwilib` stub: installing hidapi and libusb1 into
every runner would have changed the environment under test to prove a point
about a different one.

**Red first.** With the fix absent (HEAD plus only the new lock files), the new
module ran `FAILED (failures=8)`:

```
AssertionError: 'm.version("hwi") == "3.2.0"' not found in '#!/bin/zsh…'
AssertionError: 0 != 1 : the launcher must install the source lock exactly once
AssertionError: 'python -m pip install --require-hashes -r requirements-source.lock'
                 not found in '"""Read-only BSMS and USB signer discovery proof.…'
```

plus `test_the_guards_read_metadata_and_never_import_the_package` and the four
`test_every_install_path_names_the_source_lock` subtests (launcher, `probe.py`,
`README.md`, `HWI-DEPENDENCY.md`). The three lock-shape tests passed on the new
lock itself, and the embit guard test passed because that guard is unchanged and
the source lock names the same wheel.

**Break and watch.** Four defeats, each caught by its named test: the source
lock loses the device library (`hwi==3.2.0` and its two hashes deleted) →
`SourceLockTests.test_the_device_library_is_pinned_with_hashes`; the source lock
drifts from the reviewed desktop lock (`cryptography==50.0.1` → `50.0.2`) →
`test_every_source_entry_matches_the_reviewed_desktop_lock`; the launcher's hwi
guard drifts (`"3.2.0"` → `"9.9.9"`) →
`LauncherTests.test_hwi_guard_matches_the_locked_pin`; the refusal loses the
command →
`DocumentedInstallPathTests.test_the_refusal_names_the_command_that_installs_the_library`.
The test module is also its own control: its first run failed with
`AssertionError: 'm.version("embit")' not found in ' command -v python3 >/dev/null 2>&1'`
because the guard test took the first `if !` in the launcher rather than the
install condition; it now anchors on the text before the install string.
