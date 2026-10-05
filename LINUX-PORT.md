# The Linux port

> **Do not merge this branch into `main`, ever.** The v0.6.4 audit judges *how*
> the app is built -- the script, the gate order, the kept file set -- not only
> the source it builds. Merging a second platform's build into `main` would ship
> construction the audit never saw, and would delete `scripts/build-macos.sh`,
> which the macOS release still depends on. Linux artifacts come from this
> branch and are attached to the version's release page.

## What this branch is

A build of the audited v0.6.4 source for Linux x86_64. Nothing in the signing,
wallet or network code is platform-specific; what changes is how the app is
started and packaged:

* On Linux the app is `gui.py`, which serves the interface on `127.0.0.1` and
  opens the user's own browser. No window toolkit is bundled, so the Linux
  environment has no `pywebview`, no WebKit and no GTK dependency.
* `scripts/linux_entry.py` is the frozen entry point. It is `gui.main()` plus
  the same self-checks the other platforms run, reporting to a file because a
  frozen app may have no console.
* `scripts/hwi_entry.py` gained a Linux branch: the helper loads the system
  `libusb-1.0.so.0` instead of a bundled copy, because Linux distributions
  ship and update libusb themselves.

## Artifacts

Two files per version, both named for the platform they are:

* `Bitcoin-Easy-Signer-v<version>-linux-x86_64.AppImage` -- one file, `chmod +x`
  and run. The launcher is the pinned statically linked runtime in
  `vendor/appimage-runtime-x86_64`, so the host's `libfuse.so.2` is never
  loaded. If the machine has no usable `/dev/fuse`, the app can still run with
  `APPIMAGE_EXTRACT_AND_RUN=1` or `--appimage-extract`.
* `Bitcoin-Easy-Signer-v<version>-linux-x86_64.tar.gz` -- the same app unpacked,
  with `run-me.sh`, a `.desktop` entry and `udev/` rules, for a machine where an
  AppImage cannot mount itself at all.

Both carry hwilib's udev rules. Installing them needs root once:
`./<appimage> --dsh-install-udev-rules` (or
`sudo cp udev/*.rules /usr/lib/udev/rules.d/`).

### First launch on Ubuntu and other Linux desktops

After downloading the AppImage, mark it as a program before opening it. In
Ubuntu's Files app, right-click the `.AppImage`, choose **Properties**, open
**Permissions**, and enable **Allow executing file as program**. Close
Properties, then double-click the AppImage and choose **Run** if prompted.
Other Linux file managers have a similar executable-permission setting. From a
terminal, the equivalent is `chmod +x <file>.AppImage`; then double-click it
or launch it from that directory. No installation step is needed.

The owner reports completing a transaction with the Linux AppImage. In that
walkthrough, hardware discovery and signing felt nearly instantaneous and
faster than on the owner's Mac and Windows systems. This is owner-reported
experience, not a cross-platform benchmark; the network, devices, transaction
details and identifiers were not recorded. The full acceptance note is in
[`releases/LINUX-0.6.4-ACCEPTANCE.md`](releases/LINUX-0.6.4-ACCEPTANCE.md).

## Building

`scripts/build-linux.sh <version>` refuses to run anywhere but Linux x86_64. It
installs `requirements-desktop-linux.lock` with `--require-hashes`, builds
libusb 1.0.30 from the vendored source, runs PyInstaller for the app and for
`hwi`, runs every self-check (`--dsh-check-bundle`, `--dsh-check-network`,
`--dsh-check-save`, `--dsh-check-devices`, `--dsh-check-udev`), then packs the
AppDir with `mksquashfs` and concatenates it onto the pinned runtime. A check
that reports nothing is a failure: a silent pass is not a pass.

`.github/workflows/linux-inputs.yml` resolves the lock on a Linux runner;
`build-linux.yml` runs the suite (refusing skips) and builds the candidate. The
Linux lock is resolved on Linux and is not reusable on another platform.

## Releasing

One version, one page, every platform. The audited macOS pipeline creates the
`v<version>` release; this pipeline attaches to it:

```
gh workflow run build-linux.yml --ref linux-port \
  -f publish=true -f allow_unsigned=true \
  -f candidate_run_id=<candidate run id> -f release_tag=v<version>
```

The promotion downloads the exact bytes of that candidate run, verifies the
manifest it wrote (`version`, `commit`, `run_id`, `publish=false`,
`release_tag=`), re-checks the checksums, refuses any tag other than
`v<version>`, refuses to replace a file that is already on the page, and only
then uploads the four platform-named files and appends a `## Linux x86_64`
section to the release notes. An empty `release_tag` publishes a standalone
`v<version>-linux-x86_64` release instead, which is what this branch did for
v0.6.4 before the one-page policy.

## Audit coverage

A Linux release answers to this branch, not to `main`. The audited v0.6.4
artifacts, its tag and its commit are untouched by anything here, and no file
under `docs/` is modified by the port.
