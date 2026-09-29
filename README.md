# Bitcoin Easy Signer — experimental mainnet and Testnet4 GUI

The latest published build is [v0.1.16](https://github.com/cjtsh/bitcoin-easy-multisig-signer/releases/tag/v0.1.25): an unsigned, ad-hoc-signed Apple Silicon test build. It prepares and reviews an **unsigned** transaction from an existing 2-of-3 multisig wallet — partial amount or send-all with the fee deducted, live fee suggestions, the change address in plain sight, a final transaction id and a public explorer link — saves the `.psbt` to your Downloads folder, checks that your hardware signers are present and belong to the wallet *before* you build a payment, and identifies them again at the end of the send flow. **It does not sign or broadcast.** A receive-only `/*` wallet export resolves the wallet's usual change addresses itself and shows the owner exactly what it did. Older v0.1.10-v0.1.12 releases exist; their assets were replaced several times during development, so prefer the newest.

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
Transaction) for signers to review, only where supported receive/change paths
are verified. This build adds owner-confirmed change paths, transaction amount and fee review,
high-dollar confirmation, and read-only matching of connected signers. It does
not sign or broadcast a transaction.

The Mac app, named **Bitcoin Easy Signer** in Applications, gives a family member a short flow for **sending from an existing
multisig wallet**. It will not create a wallet, generate keys, or ask for
recovery words. The [Bitcoin Core HWI][hwi] tool is bundled for read-only device
recognition; descriptor and PSBT handling use [embit][embit]. Signing and
broadcast code are not included.

## Development roadmap

See [ROADMAP.md](ROADMAP.md) for the current checkpoint, three ordered
development phases, acceptance gates, and handoff instructions for the
next coding agent.

## Mac test releases

**Mac app compatibility: Apple Silicon (M-series) only. Intel-based Macs are
not supported.** The separate Python source archive can also be used on Linux.

Each test release attaches **two matching-version files**:

- `Bitcoin-Easy-Signer-vX.Y.Z-UNSIGNED-TEST.dmg`: the Mac `.app`, containing its
  Python runtime, dependencies, bundled HWI device interface, existing wallet engine, and a small native
  WebKit window. A user opens the app without installing Python or using
  Terminal. The wallet picker uses the macOS WebKit file dialog without a file-type
  filter, so custom `.bsms` files remain selectable. Only `.bsms` or `.txt`
  wallet definitions are accepted after selection. Saving an unsigned PSBT writes
  a new file into your **Downloads** folder and names the full path on screen; an
  existing file is never replaced, so an earlier transaction cannot be mistaken
  for this one.
- `bitcoin-easy-multisig-signer-vX.Y.Z.tar.gz`: the source code, tests, older
  command launcher, and build scripts. This is also usable on Linux, but
  source users need Python 3 and `pip install -r requirements.txt`.
  It is **not** a self-contained Linux desktop binary.

Generate the source archive with `bash scripts/build-source.sh X.Y.Z`. On a
Mac, build an **unsigned test** `.app` and DMG with
`bash scripts/build-macos.sh X.Y.Z`. That build also needs `libusb`
(`brew install libusb`) and **Python 3.9–3.12** on `PATH`: the bundled
`hwi 3.2.0` declares `Requires-Python >=3.9,<3.13`, so a newer interpreter
cannot install it. The GitHub Actions workflow pins Python 3.12 for this
reason. On a Mac whose default `python3` is newer, install `python@3.12` and
put it first on `PATH`; the build script now fails immediately with that
instruction rather than partway through a dependency install.
Unsigned test DMGs can be downloaded
without Apple enrollment; signing and notarization reduce first-open macOS
security warnings later. The build script requires both
`MAC_SIGN_IDENTITY` and `MAC_NOTARY_PROFILE` (an already configured macOS
keychain profile) when run with `RELEASE=1`. Keep credentials out of this
repository. Build/test on Apple Silicon. In
particular, verify first launch, BSMS file picking, refresh, and native PSBT
saving on a real Mac. A Linux build environment cannot validate or notarize
the Mac app. The active GitHub Actions workflow builds an unsigned **Apple
Silicon** test DMG and matching source archive on the candidate branch; it
does not publish releases or make the app trusted by Gatekeeper.
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
   inferred descriptor branches. It explains why transaction preparation is
   unavailable, including an unsupported wallet path, partial scan, mismatch
   between explorer UTXOs and the balance, or no confirmed outputs. If the
   explorer fails, it does *not* claim
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
   rate to prepare a PSBT from confirmed outputs. Three live mainnet fee
   choices (slow/hour, medium/half-hour, fast/fastest) populate whole sat/vB
   values. The screen estimates transaction vbytes conservatively from every
   confirmed scanned UTXO and shows the fee in sats and its indicative USD
   equivalent; the review shows the actual selected inputs and fee estimate.
   A mainnet payment estimated at $10,000 or more requires a separate
   confirmation of the amount and dollar value. PSBT preparation on either
   network requires a 2-of-3 multisig descriptor with verified receive/change
   paths matching its reference address. This version accepts explicit
   multipath descriptors and BSMS templates with exactly `/0/*,/1/*`
   restrictions; the reference address must match the first, receive path.
   A receive-only descriptor or incomplete scan remains view-only. Public
   explorer UTXOs must agree with the confirmed balance.
   The fee rate is limited to 1–25 sat/vB; preparation on either network
   requires a fresh mainnet fee reference, refuses rates below its economy
   estimate, and
   warns with extra acknowledgement below its standard estimate. An estimated
   fee above 10,000 sats is refused, and unusually high estimates require an
   extra acknowledgement before continuing. Review destination, selected
   sat/vB rate, **amount + estimated fee**, change,
   and every signer display independently; then save the unsigned `.psbt` to your Downloads folder.
   **Nothing signs or broadcasts.** A fee quote is an estimate, not a promise
   of confirmation or a substitute for checking a final signed transaction.
   Before you prepare anything, the send step recommends **sending a small test
   amount first** — advice only, never a requirement. The review shows the final
   **transaction ID** and a link to a public explorer so you can confirm, after you
   broadcast elsewhere, that the payment arrived and is confirming. **This app does
   not broadcast**, so that link is how you verify the result yourself.

   The interface keeps technical detail out of the way: addresses, xpubs, the
   per-address activity list and scan statistics live behind a
   **See wallet details** button, so the main screen shows only the balance and the
   next step. The review screen is the exception — destination, amount, fee and
   change stay in plain sight there, because those are what must be checked.

   After reviewing the transaction, **Next: connect hardware wallets** opens a
   device-recognition screen. HWI checks whether a connected, unlocked device's
   public key matches one of the wallet signers. The app does not ask for a PIN,
   sign the PSBT, or broadcast anything. A matching public key does not prove a
   device can sign this particular transaction.

   The send flow begins with a clear **Yes, prepare a transaction** or **No**
   choice. Choosing Yes opens the destination, amount and fee fields. Review
   the complete proposal, save the unsigned PSBT if desired, then continue to
   read-only signer recognition. Choosing No prepares nothing. Signing and
   broadcast remain later work.

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

The older Testnet4 sample export described below uses `/*` in the descriptor,
but its reference address matches `/0/0`. Such a file proves a receiving path but
not a change path. The app resolves the wallet's usual change addresses itself —
the standard BIP48 `/1/*` branch, derived from the same cosigner keys — rather
than asking the owner to confirm a technical detail they have no way to check.
It then looks for evidence: if the wallet has spent before, the scan finds its
used change addresses and says so; if it has never spent, the app says plainly
that change addresses are unconfirmed and recommends a small test payment. The
resulting change address is shown in the review and must be checked on the
signing device. A BSMS descriptor template that declares both `/0/*` and `/1/*`
restrictions, or an explicit `<0;1>/*` multipath descriptor, is still used
exactly as given. The reference address must match the receive path. The same rule applies on mainnet. If the reference address cannot be matched, the GUI stops rather than
inventing a wallet balance. There is no hidden hosted server upload, wallet
creation or seed entry.

## Run the older command-line hardware proof on a Mac

1. Install Python 3 and, in a Terminal opened in this repository, run:

   ```sh
   python3 -m venv .venv
   source .venv/bin/activate
   python -m pip install -r requirements.txt
   ```

2. HWI 3.2.0 is bundled in the v0.1.25 Mac app.

**Devices behave differently, and it matters for the person using this.** The app
runs the recognition check itself and tells you what to do when a device will not
read, but the honest summary is:

| Device | What it takes |
| --- | --- |
| **Trezor** (Safe 3 tested) | Plug in, unlock on the device. |
| **Blockstream Jade** | Plug in, enter the PIN **on the Jade**. |
| **Ledger** (Nano S Plus tested) | Unlock on the device **and open the Bitcoin Testnet app** — the extra step people miss, and the reason a Ledger can look broken when it is not. |
| **Coldcard** | Unlock on the device. | The command-line proof below
   still uses an HWI 3.2.0 installation on your PATH. Use only the official
   [HWI release][releases]. It adds an explicit `testnet4` chain option.
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
