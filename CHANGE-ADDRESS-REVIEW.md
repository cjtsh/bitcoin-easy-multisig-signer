# Change-address safety review

This review responds to the owner's `multisig_change_address_notes.md`. The note was treated as an input to verify, not as an implementation authority. No owner's wallet file, addresses, xpubs, transaction or diagnostic report is stored here.

## What the standards actually establish

- [BIP 129](https://github.com/bitcoin/bips/blob/master/bip-0129.mediawiki) makes BSMS a four-line descriptor record: version, descriptor or template, path restrictions, and first address. A separate, explicit change *address* is not a standard fifth field. A `/**` template with `/0/*,/1/*` restrictions does explicitly declare both branches; `No path restrictions` does not.
- [BIP 48](https://github.com/bitcoin/bips/blob/master/bip-0048.mediawiki) specifies external `/0/index` and internal `/1/index` below the native-SegWit multisig account xpub. This is a standard derivation policy, not proof that every historical or customized wallet used it.
- Nunchuk's [BSMS writer](https://github.com/nunchuk-io/libnunchuk/blob/33f7dc36b4251cd2042ee1e796c90250b4438979/src/utils/bsms.hpp) emits `No path restrictions` for ordinary wallets. Its descriptor importer defaults an unspecified external/internal pair to `{0,1}`. A custom historical branch choice may be absent from an ordinary export. A first receive address verifies only that receive path, not the wallet's undisclosed change history.

The attached note correctly warns that a wrongly constructed change output can be hard to recover. It overstates that every BSMS export declares `/0/*,/1/*` and that an explicit change address is a standard field. Deriving a different *unhardened* branch from the same three account xpubs does not necessarily change which seeds can sign, but another wallet may not discover that output automatically. Deriving from different accounts or using a different script could create a much worse recovery problem.

## Current app boundary

`probe.py` validates the BSMS checksum when present, parses the exact descriptor, and checks the file's first address. `wallet_service.py` uses declared receive/change branches when present. For `No path restrictions`, it permits a smaller send only under the strict native-SegWit sorted 2-of-3 BIP48 policy, with three matching account origins and a first address that anchors the `/0/0` receive address. It then derives `/1/index` from the **same three xpubs**, preserving the 2-of-3 witness script. The change address, amount and signer derivations go into the reviewed PSBT. Finalization and broadcast recheck outputs and fee against that review. A wallet outside this policy cannot make a partial send; Send All remains an explicit user choice.

The owner's supplied Mutinynet Nunchuk BSMS was inspected read-only without printing its identifiers: it has `No path restrictions`, three bare `/*` signer suffixes, and a first address matching only after expansion to `/0/0`. It therefore follows the intended BIP48 fallback. The owner's earlier 0.3.2 Mutinynet payments and 0.4.1 Ledger + Jade payment are useful device evidence, but do not by themselves prove every possible mainnet wallet layout. Mainnet broadcast remains disabled.

The owner also supplied a separate Sparrow Testnet4 BSMS and Nunchuk Mutinynet BSMS for a format comparison. Both are four-line 2-of-3 records with four-level signer origins. The Sparrow record declares `/0/*,/1/*` and puts `<0;1>/*` directly in its descriptor; the app treats that change branch as declared. The Nunchuk record says `No path restrictions` and uses bare `/*` in its descriptor; its first address anchors receive `/0/0`, so the app treats change `/1/*` as standard-derived. The two records describe different wallets and cannot verify each other's change address. Neither file, nor any derived identifier, is committed to the repository.

## Additional guard from this review

A bare `/*` descriptor can itself match a first address at `xpub/0`. That is *not* evidence for `xpub/0/index` receiving and must not authorize `xpub/1/index` change. `wallet_layout` now keeps such an export receive-only for an unrestricted file, so a partial send is unavailable. If that same file claims `/0/*,/1/*` restrictions, the contradictory record is rejected. A synthetic regression test covers both cases; the ordinary Nunchuk-style `/0/0` anchor remains supported.

## Remaining mainnet gate

One BSMS file with `No path restrictions` cannot independently prove an undisclosed custom change branch. Before enabling mainnet broadcast, the owner and an independent reviewer should verify the exact live-wallet change policy against the wallet and signers, including the first *unused* change address and its full script/derivation, then perform a bounded live send and confirm the change is recognized and subsequently spendable. The recovery operator must not be asked to resolve paths or supply a second database file. If that verification cannot be automated or established during setup, the product should retain a clear limitation for partial sends from ambiguous wallet exports.
