# Easy Bitcoin Multisig Signer

- Keep one existing wallet/PSBT engine and one HTML UI for Testnet4 and mainnet; the switch changes network configuration and selected Esplora backend, not functionality. Never infer an undeclared change branch.
- No wallet creation, signing, or broadcasting. The broadcaster URL is only a stored future setting; do not imply transactions can be submitted.
- Package a lightweight macOS WebKit window around the existing Python app, embedding Python and dependencies. Do not rewrite the engine or replace it with Electron/Go merely for distribution.
- Attach a signed/notarized macOS DMG and a curated source `.tar.gz` to each future public release from the same version. The source archive remains usable on Linux with Python installed; it is not a Linux binary.
- First Mac DMG release candidate is v0.1.0 (previous public source release v0.0.6). Do not call the unsigned CI artifact a public Mac release; Apple Silicon build and Intel/universal compatibility need explicit verification.
- Do not include BSMS files, wallet addresses, PSBTs, settings, or secrets in artifacts. Do not query real mainnet wallet addresses without fresh permission.
- Do not publish a release until the Mac build and native file flows are tested and the user approves public publication.