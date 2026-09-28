# Easy Bitcoin Multisig Signer — experimental mainnet and Testnet4 GUI

## Latest test release: v0.1.7

Download the [unsigned Apple Silicon Mac DMG](https://github.com/cjtsh/easy-bitcoin-multisig-signer/releases/download/v0.1.7/Easy-Bitcoin-Multisig-v0.1.7-UNSIGNED-TEST.dmg) or the [source archive for Linux and other platforms](https://github.com/cjtsh/easy-bitcoin-multisig-signer/releases/download/v0.1.7/easy-bitcoin-multisig-signer-v0.1.7.tar.gz). See the [v0.1.7 release notes](https://github.com/cjtsh/easy-bitcoin-multisig-signer/releases/tag/v0.1.7). This is an unsigned, experimental test release from the `phase2-transaction-builder` candidate branch; it is not merged into `main`. It prepares unsigned transactions and does not sign or broadcast them.


## Disclaimer — experimental software; use at your own risk

**This is experimental, unaudited software. It is not a production-ready
Bitcoin recovery tool. Bugs, incorrect information, or hardware incompatibility
could lead to irreversible loss of funds. Do not use this proof with production
funds.**

**THE SOFTWARE IS PROVIDED "AS IS" AND "AS AVAILABLE," WITHOUT WARRANTIES OR
GUARANTEES OF ANY KIND, EXPRESS OR IMPLIED, TO THE MAXIMUM EXTENT PERMITTED BY
LAW.** The authors and contributors make no promises about its correctness,
security, fitness for a particular purpose, continued maintenance, or whether
any transaction will succeed.

**TO THE MAXIMUM EXTENT PERMITTED BY LAW, THE AUTHORS AND CONTRIBUTORS ARE NOT
LIABLE FOR LOST OR MISDIRECTED BITCOIN OR OTHER FUNDS, LOST DATA, OR OTHER
DAMAGES ARISING FROM USE OF THIS SOFTWARE.** Nothing here excludes liability
or legal rights that cannot lawfully be excluded.

**Before approving any transaction, independently verify the full destination
address, amount, network, fee, and change output, including what each hardware
signer displays. If anything is unclear or inconsistent, stop.** Never enter
seed words or private keys into this software. Read the full
[risk and liability disclaimer](DISCLAIMER.md). This notice is not legal advice
or a guarantee of enforceable protection; obtain qualified legal and security
review before using software to handle real funds.

The local browser GUI opens a BSMS 1.0
wallet definition, checks public mainnet or Testnet4 balances, and prepares
an **unsigned transaction file** (PSBT, short for Partially Signed Bitcoin
Transaction) for signers to review, only where the supported receive/change
paths are verified.
It cannot sign or broadcast a transaction. It is not yet
a finished, Mac-tested application, and no physical signer has been tested. The
previous command-line proof remains available in `probe.py`.

The intended Mac app will eventually give a family member a short guided
flow for **sending from an existing multisig wallet**. It will not create a
wallet, generate keys, or ask for recovery words. This proof keeps hardware
communication in the existing [Bitcoin Core HWI][hwi] tool and descriptor
and PSBT handling in [embit][embit]; it contains no USB driver or signing code.

## Development roadmap

See [ROADMAP.md](ROADMAP.md) for the current checkpoint, three ordered
development phases, acceptance gates, and handoff instructions for the
next coding agent.

## Mac test releases

**Mac app compatibility: Apple Silicon (M-series) only. Intel-based Macs are
not supported.** The separate Python source archive can also be used on Linux.

Each test release attaches **two matching-version files**:

- `Easy-Bitcoin-Multisig-vX.Y.Z-UNSIGNED-TEST.dmg`: the Mac `.app`, containing its
  Python runtime, dependencies, existing wallet engine, and a small native
  WebKit window. A user opens the app without installing Python or using
  Terminal. The wallet picker uses the macOS WebKit file dialog without a file-type
  filter, so custom `.bsms` files remain selectable. Only `.bsms` or `.txt`
  wallet definitions are accepted after selection; the desktop wrapper uses
  a native save dialog for unsigned PSBTs.
- `easy-bitcoin-multisig-signer-vX.Y.Z.tar.gz`: the source code, tests, older
  command launcher, and build scripts. This is also usable on Linux, but
  source users need Python 3 and `pip install -r requirements.txt`.
  It is **not** a self-contained Linux desktop binary.

Generate the source archive with `bash scripts/build-source.sh X.Y.Z`. On a
Mac, build an **unsigned test** `.app` and DMG with
`bash scripts/build-macos.sh X.Y.Z`. Unsigned test DMGs can be downloaded
without Apple enrollment; signing and notarization reduce first-open macOS
security warnings later. The build script requires both
`MAC_SIGN_IDENTITY` and `MAC_NOTARY_PROFILE` (an already configured macOS
keychain profile) when run with `RELEASE=1`. Keep credentials out of this
repository. Build/test on Apple Silicon. In
particular, verify first launch, BSMS file picking, refresh, and native PSBT
saving on a real Mac. A Linux build environment cannot validate or notarize
the Mac app. The active GitHub Actions workflow builds an unsigned **Apple
Silicon** test DMG and matching source archive on the candidate branch; it
publishes the v0.1.7 prerelease after both build jobs pass; it does not make the app trusted by Gatekeeper.
The source packaging script accepts the recipe in either its staged `ci/`
location or the active `.github/workflows/` location.
The Mac app is built for Apple Silicon only; do not describe it as supporting
Intel-based Macs or as a universal Mac app.

GitHub may additionally display its automatically generated source archives;
the two files above are the intended **attached release artifacts**. See the
GitHub Releases page for the latest downloadable test build. These builds are
unsigned, not notarized, and not a substitute for an interactive Mac test.

## Point-and-click Testnet4 practice or mainnet viewing on a Mac

This is **one application and one wallet/PSBT engine**, with a selected
network configuration for BIP48 coin type, address prefix and the public
Esplora backend. Switching networks changes that routing and the visible
theme, not the wallet or fee-safety rules. Each network requires its own
matching BSMS definition; the switch never converts keys or balances.
Mainnet BTC/USD and sat/vB quotes remain explicitly labelled *references*
in both modes, as chosen for this app; Testnet4 confirmation conditions may
differ.

1. For the **current source preview**, unpack the `.tar.gz` and double-click
   **Start Easy Multisig.command** on a Mac. That older launcher needs Python 3,
   prepares a local environment on first launch, and shows Terminal. The
   future tested/signed DMG will instead open a self-contained app window.
   macOS may warn about unsigned downloaded software; do not bypass a warning
   for software whose origin you cannot independently verify.
2. A browser window opens on **127.0.0.1** on your Mac (not a hosted website).
   Start with **TESTNET4** and choose a nonproduction BSMS 1.0 definition
   with the file picker. To use **LIVE MAINNET**, switch networks and choose a
   *different*, matching mainnet BSMS definition: a Testnet4 definition cannot
   become a mainnet wallet by flipping the switch. The app shows public
   cosigners/xpubs, origin fingerprints,
   the reference address, and the first receiving and change addresses.
   The file remains in process memory; it is not stored by the app.
3. The balance check derives public addresses and sends **those addresses**
   to the selected explorer (mempool.space by default). Neither BSMS
   nor xpubs are sent. Before importing either network, you must explicitly
   acknowledge disclosure to the selected explorer operator. On mainnet those
   addresses can reveal real wallet activity.
   The wallet definition and last scan stay only in process memory until
   you quit the local app; reloading the browser restores them. Use the
   prominent **Refresh wallet balance** button after new deposits—no file
   re-selection is needed. It checks supported receive and change branches
   up to 100 indices apiece,
   stopping after a gap of 20 unused addresses. **A displayed amount is an
   explorer observation, not a proof of a complete wallet balance.** The
   interface shows when it last scanned and warns on incomplete coverage or
   inferred descriptor branches. If the explorer fails, it does *not* claim
   the wallet is empty. An undeclared change branch is **never inferred on
   either network**, so a receive-only balance is partial. Each address with
   activity shows its own confirmed,
   pending and observed net balance; the wallet total sums scanned addresses.
   For a size reference, the interface also fetches a public mainnet BTC/USD spot
   rate from mempool.space and displays approximate USD equivalents beside
   the wallet balance, individual addresses and entered send amount.
   **Testnet4 coins have no real USD value**: these are mainnet BTC price
   comparisons, not a quote to redeem test coins. It also fetches mainnet
   fee-rate recommendations even while practicing on Testnet4; Testnet4
   confirmation conditions may differ. Rates can be delayed or
   unavailable; satoshi amounts still display without a rate. No wallet
   information is included in the price request.
4. Enter a destination on the **selected network**, a whole-sat amount and fee
   rate to prepare a PSBT from confirmed outputs. PSBT preparation on either
   network requires a 2-of-3 multisig descriptor with explicit receive/change branches
   matching its reference address; inferred change or incomplete scans are
   view-only. Public explorer UTXOs must agree with the confirmed balance.
   The fee rate is limited to 1–25 sat/vB; preparation on either network
   requires a fresh mainnet fee reference, refuses rates below its economy
   estimate, and
   warns with extra acknowledgement below its standard estimate. An estimated
   fee above 10,000 sats is refused, and unusually high estimates require an
   extra acknowledgement before download. Review destination, selected
   sat/vB rate, **amount + estimated fee**, change,
   and every signer display independently; then download the unsigned `.psbt`.
   **Nothing signs or broadcasts.** A fee quote is an estimate, not a promise
   of confirmation or a substitute for checking a final signed transaction.
   The "connect signers" step is not implemented in this version.

**Optional server selection:** Open **Advanced network settings** to select
an Esplora HTTP API base for each network's explorer and a separate Esplora
broadcast server URL. Defaults for both are mempool.space; you can restore them
with one button. Mainnet can use, for example,
`https://explorer.btc21.cc/api` as an optional explorer. A custom URL is
checked against the selected network's genesis hash when saved and before
wallet data is requested. That check prevents an accidental wrong-network
selection, **not** inaccurate or malicious explorer results. The chosen URLs
are saved locally in your user configuration directory; wallet files, xpubs,
addresses, scans and PSBTs are not saved there. If a chosen server is offline,
the app does **not** silently fall back to a public explorer. Only HTTPS
servers or loopback HTTP are accepted. Electrum TLS servers (including port
50002) speak a different protocol and are **not** supported by these Esplora
fields. **The broadcaster URL is a future-use setting only:** this version
cannot sign or broadcast, and no transaction is sent to that endpoint.

The Testnet4 sample export described below uses `/*` in the descriptor, but its
reference address matches `/0/0`. The GUI uses that address to identify
the receive branch, but does **not** infer a `/1/*` change branch.
The same rule applies on mainnet. Both files are view-only until an explicit,
reference-matched receive/change definition is available. If the reference
address cannot be matched, the GUI stops
rather than inventing a wallet balance. There is no hidden hosted server
upload, wallet creation or seed entry.

## Run the older command-line hardware proof on a Mac

1. Install Python 3 and, in a Terminal opened in this repository, run:

   ```sh
   python3 -m venv .venv
   source .venv/bin/activate
   python -m pip install -r requirements.txt
   ```

2. For the device check on an Apple Silicon Mac, get the official **HWI 3.2.0**
   macOS arm64 binary from the
   [HWI releases][releases]. Follow its release verification instructions;
   do not download a wallet tool from an untrusted mirror. You may instead
   use an existing `hwi` command on your PATH. HWI is separate from this
   Python environment. HWI 3.2.0 adds an explicit `testnet4` chain option.
3. Use a **nonproduction Testnet4 BSMS file** made with the test signers.
   Its origins must use BIP48 coin type `1'`, and its reference address
   must match the descriptor's first address. Run:

   ```sh
   python probe.py inspect /path/to/test-wallet.bsms
   python probe.py devices /path/to/test-wallet.bsms --chain testnet4 --hwi /path/to/hwi
   ```

   Use `--chain signet` only if your wallet and faucet are actually on
   Signet. **A `tb1` address cannot distinguish Testnet4, legacy testnet,
   and Signet.** The device command requires an explicit chain and refuses
   mainnet. The offline `inspect` command may still inspect a `bc1` file
   without contacting devices or a network. If a device is locked, unlock
   it using its normal procedure. This app never requests a PIN or seed.

The device command displays only a policy summary and *public identity*
matching status—not proof that a device can sign. It never displays extended
public keys or fingerprints. Do **not** commit any actual BSMS file or PSBT:
wallet exports contain privacy-sensitive public keys and addresses.

## Get a few Testnet4 sats for testing

First get a BSMS export from your **test** signers. With an export whose
reference address validates against its literal descriptor, run:

```sh
python probe.py funding-address /path/to/test-wallet.bsms --chain testnet4
```

This deliberately prints the first test-wallet `tb1` address so you can
paste it into a faucet. **Before funding it, verify the same address in
an independent test wallet or on your test signers, and confirm the
emulators can eventually sign for that wallet.** This probe cannot prove
signing or check a balance; an emulator that only returns an xpub may leave
test sats unspendable. If the reference address differs from the literal
descriptor, the command stops rather than guessing a receive path.

- [Testnet4.dev faucet](https://faucet.testnet4.dev/) accepts a Testnet4
  address without a login, subject to availability and limits.
- [Mempool.space Testnet4 faucet](https://mempool.space/testnet4/faucet)
  is another option; it may require an account.
- [Mempool.space Testnet4 explorer](https://mempool.space/testnet4)
  can show whether a faucet payment arrived on **Testnet4**, not Signet.

Use only a test address. Testnet coins are for testing, not real Bitcoin;
do not buy test sats or submit seeds, private keys, or production wallet
files to a faucet. Faucet availability and limits can change.

## Emulator handoff

`--hwi` can point to an executable adapter for your fake hardware signers,
not just the real HWI binary. The adapter must accept these two HWI-style
read-only calls and return JSON on stdout:

```text
--chain testnet4 enumerate
  -> [{"type":"emulator","model":"Test signer","path":"emulator-1",
       "fingerprint":"8hexchars"}]

--chain testnet4 --device-type emulator --device-path emulator-1
  getxpub m/48h/1h/0h/2h
  -> {"xpub":"the public extended key at exactly that origin path"}
```

The adapter must exit successfully on valid responses; never output private
keys, seed words, or passphrases. The `fingerprint` and xpub must belong
to the same test signer that contributed a key to the BSMS file. A program
can imitate these **public** responses without holding any private keys,
so a match is not proof it can sign. Later PSBT signing tests must establish
that separately. No vendor USB drivers or cryptography are implemented here.

The uploaded example that motivated this proof has a reference address
that matches a common `/0/0` receive-branch convention but **not** the
literal first address of its `/*` descriptor. The probe will warn about
that difference; it will never treat a guessed branch as validation.
Resolve the wallet-export convention before any future signing feature.

Run offline tests with:

```sh
python -m unittest discover -s tests -v
```

## What has been tested—and what has not

- A strict BSMS 1.0 format and descriptor checksum check.
- A local reference-address comparison for native-SegWit multisig.
- HWI device enumeration and full public-key matching at the key-origin
  path, not a vendor-name-only or fingerprint-only match.
- Explicit Testnet4 selection and a guarded test-wallet funding address;
  no assumption that `tb1` identifies a blockchain.
- A local GUI can parse synthetic BSMS data, derive addresses, display the
  three public cosigners, scan a mocked Testnet4 explorer, and build an
  unsigned PSBT with verified previous outputs in offline tests.
- No real Testnet4 wallet balance has been checked with this GUI yet; no Mac
  launch or physical hardware has been tested. No signing or broadcasting
  exists. Do not use the PSBT preview to move production funds.

[hwi]: https://github.com/bitcoin-core/HWI
[releases]: https://github.com/bitcoin-core/HWI/releases/tag/3.2.0
[embit]: https://github.com/diybitcoinhardware/embit