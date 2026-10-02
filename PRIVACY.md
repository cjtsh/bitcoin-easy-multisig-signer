# Privacy notice

**Publisher:** Bitseeker LLC. This notice describes the Bitcoin Easy Signer
website and desktop app. It is general information, not a promise about the
privacy practices of independent services linked or contacted by the project.

## Website and downloads

The project website is hosted by GitHub Pages, and source code and release
downloads are hosted by GitHub. Bitseeker LLC does not operate a project user
account system, collect wallet data through the website, or use project-run
analytics on the site. GitHub may process connection and download information
under its own privacy terms. Do not submit wallet files, addresses, transaction
data, device details, or secrets in GitHub issues or discussions.

## Desktop app

The app runs locally and does not require an account with Bitseeker LLC. It does
not send seed words or private keys to the project. It reads a BSMS wallet file
locally, derives public addresses locally, and contacts the selected Esplora
server for wallet-address and transaction information. Those requests can let
that server associate your IP address with the queried public addresses and
transaction identifiers.

With the default mainnet settings, wallet lookups and broadcasts use
mempool.space; selected mainnet outpoints are also checked through
blockstream.info. Fee estimates and the approximate BTC/USD reference use
mempool.space. Testnet4 uses mempool.space's Testnet4 service; Mutinynet uses
mutinynet.com. Advanced settings let an operator choose other Esplora servers;
requests then go to the configured services. The app does not silently switch
to a different server.

When you broadcast, the selected broadcaster receives the signed transaction,
which becomes public if accepted by the Bitcoin network. A transaction ID and
public outputs can reveal financial activity. Hardware-device communication is
local over supported interfaces; device manufacturers' software and services
are outside this project's control.

The optional diagnostic report is created only when you request it, saved in
your Downloads folder, and is not automatically sent to Bitseeker LLC. It
contains the app version, selected network, timestamps, fixed event codes, and
a validated device class; review it before sharing. A saved PSBT is also stored
locally when you explicitly request one. Treat wallet files, addresses, PSBTs,
and signed transactions as sensitive information even when they do not contain
seed words.

## Third-party services

Using public explorers, GitHub, or hardware-vendor tools is subject to the
respective provider's terms and privacy practices. Check those policies before
use. This notice describes the current source. Older downloaded app versions
may differ; consult the documentation for the version you use.
