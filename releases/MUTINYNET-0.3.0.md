# Mutinynet integration and reviewer handoff

## Why this exists

The owner reported that a Testnet4 payment remained unconfirmed for a long time, then confirmed on 29 September 2026. Waiting for repeated Testnet4 blocks makes physical-device testing impractical. The owner chose Mutinynet for the published 0.3.0 test path. This is an **additional practice network**, not a replacement for the Testnet4 wallet or a route to mainnet. Testnet4 remains selectable so the existing wallet and transaction history remain accessible. Standard Signet was considered, but it does not provide Mutinynet's operator-targeted 30-second block cadence. A cadence is not a confirmation guarantee. Release evidence and the remaining owner check are in `PATCH-0.3.0.md`.

## One engine, three network profiles

`network_config.py` adds the `mutinynet` profile (testnet BIP48 coin type `1'`, `tb1` P2WSH addresses, `https://mutinynet.com/api` Esplora and web explorer). `wallet_service.py` now carries the explicitly selected chain through scan and PSBT construction; it does **not** infer a chain from `tb1`. `signing.py` is unchanged. HWI receives `test` for either practice network because the signers use testnet key paths, while the app's Esplora and broadcast endpoints remain chain-specific. Mainnet broadcast is still refused in `gui.py`.

Mutinynet and ordinary Signet have the same genesis hash. `network_settings.verify_esplora` therefore checks **both genesis and Mutinynet block 1** (`000002855893a0a9b24eaffc5efc770558a326fee4fc10c9da22fc19cd2954f9`), captured from Mutinynet's public Esplora API on 29 September 2026. The app checks this checkpoint before each Mutinynet scan/prepare and before broadcast, including the built-in endpoint. A standard Signet backend with the same genesis but a different block 1 is refused. This pins network identity; it cannot prove the server is honest about current UTXOs.

Mutinynet fees come from its Esplora `/fee-estimates`, without wallet identifiers. Mainnet and Testnet4 retain their existing mainnet reference. The same 1–25 sat/vB and 10,000-sat fee caps apply. Selected historical funding transactions must still be confirmed and the selected outpoints unspent immediately before prepare and broadcast. Mutinynet and Testnet4 currently have only a fresh same-operator check; mainnet additionally checks a separately operated Esplora. Do not describe a single public explorer as independent verification.

## Wallet and operator steps

The owner must create a **new 2-of-3 native-SegWit multisig wallet on Mutinynet** in a wallet that supports this custom Signet, fund it with practice coins from the [Mutinynet faucet](https://faucet.mutinynet.com/), and export a BSMS definition that declares its receive and change branches. The Testnet4 BSMS may use the same `tb1` format and hardware keys, but its existing coins and confirmation history stay on Testnet4. A single-signature wallet can be useful for checking the faucet, yet this app cannot prepare a payment from it. No address, BSMS, xpub, seed, PSBT or signed transaction is required for agent review.

Sparrow advertises Signet, multisig and hardware-wallet support; its compatibility with the **custom Mutinynet server and this exact BSMS export** still requires the owner's hands-on check. The owner's Nunchuk and Jade/Trezor/Ledger path on Mutinynet is likewise **unverified**. Do not claim device support from the synthetic tests.

| Component | Known evidence | 0.3.0 owner validation still needed |
| --- | --- | --- |
| Sparrow | Documents Signet, multisig, hardware and Electrum-server use | Custom Mutinynet connection; 2-of-3 wallet creation; BSMS export with change branch |
| Nunchuk | Owner used it with the original Testnet4 multisig | Custom Mutinynet connection and matching wallet definition; no current claim of support |
| Jade, Trezor Safe 3, Ledger Nano S Plus | Owner previously used all three on Testnet4 in earlier versions; 0.3.0 HWI tests are synthetic | Recognize public identity and display/sign the actual Mutinynet PSBT on two devices |
| HWI 3.2.0 | Its `--stdin` mode is exercised synthetically and in the packaged build recipe | Device-specific stdin signing on the owner's Mac |
| Mutinynet Esplora | Genesis, block-1 checkpoint and fee endpoint returned valid data on 29 September 2026 | Live wallet scan, selected-outpoint checks and broadcast of the owner's practice payment |

Ask for a diagnostic report and a description of what the device displayed only if the completed 0.3.0 walkthrough fails.

## Compatibility and release checks

- Legacy v1 settings containing only `main` and `testnet4` are accepted and receive the Mutinynet default without changing the saved URLs.
- The UI distinguishes Mutinynet from Testnet4 and clears old signing/final panels when a new payment is prepared. The installed 0.2.1 app has the stale-panel bug; **close that app before using 0.3.0 and never broadcast from a mixed screen**.
- Synthetic API tests cover Mutinynet import → scan → PSBT through the existing builder, rejection of ordinary Signet's block-1 hash, and legacy settings. The bundle's `--check-network` probes Mutinynet genesis/checkpoint through the packaged TLS path. Physical wallet/device/broadcast acceptance is pending the owner test of the completed 0.3.0 DMG.
- The [Mutinynet deployment](https://github.com/MutinyWallet/mutiny-net) describes its custom Signet, public Esplora and 30-second target. The [faucet](https://faucet.mutinynet.com/) publishes its Signet challenge and configuration. [Sparrow](https://www.sparrowwallet.com/) documents Signet and multisig support. None of these sources guarantees that every wallet, firmware or hosted service will work at test time.
