This release adds regression coverage for three signing refusals and the
unknown-outcome response to a mismatched broadcast txid. Its SBOM now records
the exact local embit wheel hash and its local-source status. The release
workflow promotes the successful signed candidate from the same commit after
verifying its run provenance and checksums. Wallet, signing, and broadcast
behavior are unchanged.

The source archive uses an explicit document allowlist so ignored local files
cannot enter a public archive.

The v0.6.3 audit grade remains Yellow pending the auditor's follow-up.
