# Easy Bitcoin Multisig Signer — read-only hardware proof

**Experimental. Do not use with production funds.** This first commit is a
command-line proof for inspecting a BSMS 1.0 wallet export and identifying
matching USB hardware signers. It cannot sign, create, or broadcast a
transaction. It is not yet the recovery app.

The intended Mac app will eventually give a family member a short guided
flow for **sending from an existing multisig wallet**. It will not create a
wallet, generate keys, or ask for recovery words. This proof keeps hardware
communication in the existing [Bitcoin Core HWI][hwi] tool and descriptor
parsing in [embit][embit]; it contains no USB driver or signing code.

## Run on a Mac

1. Install Python 3 and, in a Terminal opened in this repository, run:

   ```sh
   python3 -m venv .venv
   source .venv/bin/activate
   python -m pip install -r requirements.txt
   ```

2. For the device check, get the official **HWI 3.2.0** macOS binary for
   your Mac's architecture (arm64 or x86_64) from the
   [HWI releases][releases]. Follow its release verification instructions;
   do not download a wallet tool from an untrusted mirror. You may instead
   use an existing `hwi` command on your PATH. HWI is separate from this
   Python environment.
3. Use a **nonproduction test BSMS file** created from the test devices:

   ```sh
   python probe.py inspect /path/to/test-wallet.bsms
   python probe.py devices /path/to/test-wallet.bsms --hwi /path/to/hwi
   ```

   For a `tb1` test wallet, the device command defaults to HWI's `signet`
   chain; you can use `--chain test` instead. A `bc1` file uses `main`, but
   this probe remains strictly read-only. If a device is locked, unlock it
   using its own normal procedure. This app never requests a PIN or seed.

The program displays only a policy summary, validation status, and signer
match results. It does not display extended public keys, fingerprints, or
the reference address. Do **not** commit any actual BSMS file or PSBT:
wallet exports contain privacy-sensitive public keys and addresses.

The uploaded example that motivated this proof has a reference address
that matches a common `/0/0` receive-branch convention but **not** the
literal first address of its `/*` descriptor. The probe will warn about
that difference; it will never treat a guessed branch as validation.
Resolve the wallet-export convention before any future signing feature.

Run offline tests with:

```sh
python -m unittest discover -s tests -v
```

## What this proves—and what it does not

- A strict BSMS 1.0 format and descriptor checksum check.
- A local reference-address comparison for native-SegWit multisig.
- HWI device enumeration and full public-key matching at the key-origin
  path, not a vendor-name-only or fingerprint-only match.
- No balance scanning, transaction construction, signing, or broadcasting.
  Those need separate, tested off-the-shelf components and a guided UI.

[hwi]: https://github.com/bitcoin-core/HWI
[releases]: https://github.com/bitcoin-core/HWI/releases/tag/3.2.0
[embit]: https://github.com/diybitcoinhardware/embit