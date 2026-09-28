# Bitcoin Easy Signer Signer

- Keep one existing wallet/PSBT engine and one HTML UI for Testnet4 and mainnet; the switch changes network configuration and selected Esplora backend, not functionality. Never infer an undeclared change branch.
- No wallet creation, signing, or broadcasting. The broadcaster URL is only a stored future setting; do not imply transactions can be submitted.
- Package a lightweight macOS WebKit window around the existing Python app, embedding Python and dependencies. Do not rewrite the engine or replace it with Electron/Go merely for distribution.
- Attach an Apple Silicon macOS DMG and a curated source `.tar.gz` to each test release from the same version. Test DMGs are unsigned and unnotarized; signed/notarized distribution is a separate future step. The source archive remains usable on Linux with Python installed; it is not a Linux binary.
- Target Apple Silicon Macs only; Intel/universal compatibility is not a release requirement. Verify the Apple Silicon CI build before attaching its unsigned output to a public GitHub test release.
- Do not include BSMS files, wallet addresses, PSBTs, settings, or secrets in artifacts. Do not query real mainnet wallet addresses without fresh permission.
- A user-requested test release may be published after automated Mac build checks; label it experimental and unsigned, and never claim the real Mac window or native file flows were manually tested. A production-ready release requires real Mac testing and separate approval.
- Keep the app concise: place small, accessible ? pop-outs beside unfamiliar terms or consequential actions. Explain PSBT in context as an unsigned transaction file for signers; use plain English in buttons and errors, not an always-visible glossary.
- Public development and test releases are expected. Do not repeat the standard experimental/public-development disclaimers in routine updates to the user; mention only new risks or decisions that require attention.