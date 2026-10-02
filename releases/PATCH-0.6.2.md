# v0.6.2 — retiring a review also retires its network

**Status: candidate. Not published yet.** Nothing is published as 0.6.2; the
published release remains
[v0.6.1](https://github.com/cjtsh/bitcoin-easy-multisig-signer/releases/tag/v0.6.1).
This record covers what the fix is, what it does not change, and how it was
verified.

## Why this release exists

The owner chose it as the next piece of work after 0.6.1 was published
(m01412), from a short list that also held the plain-language operator guide and
the F2/F5/F6 findings. It is the defect recorded as **F3**.

`ui.html` keeps the network that the final screen was built for in
`finalChain`, and the broadcast posts that value as the backend's mainnet
opt-in:

```js
confirm: true, mainnet_opt_in: finalChain === "main",
```

`invalidateReview()` retired every other part of a finished review — the
prepared PSBT, the review id, `finalTxid`, every value on the final panel — but
not `finalChain`. Two other places that retire a review had the same gap: the
clear-signed handler, which discards the signed bytes, and the signer-step reset
that runs when a new payment is prepared.

**This was not reachable and is not a fund risk.** A broadcast also requires a
non-null `finalTxid`, and `finalTxid` is only ever set beside `finalChain` in
`showFinal()`, so a broadcast could not be sent from a retired review at all.
The stale value mattered because it was the one field feeding the mainnet opt-in
that outlived the payment it described, and the honest description of a
defence-in-depth fix is that it is one — not a vulnerability.

## Change

All three sites now clear the chain together with the rest of the review:

- `ui.html` `invalidateReview()` — `finalTxid = null; finalChain = null;`
- `ui.html` clear-signed handler — `finalTxid = null; finalChain = null;`
- `ui.html` signer-step reset — `if (reset) { … finalTxid = null; finalChain = null; }`

A comment at each site records why the network belongs to the review: the
broadcast derives its mainnet opt-in from it.

## Verification

`tests/ui_broadcast_outcome.cjs` now reads the body of the broadcast request and
pins three things:

1. after `invalidateReview()`, `finalChain` is `null`;
2. a broadcast sent with no finalized network carries `mainnet_opt_in: false`
   and still names the transaction it was given;
3. a payment genuinely finalized on mainnet still carries
   `mainnet_opt_in: true`, so the opt-in itself is untouched.

The first assertion was checked against the unfixed file, where it fails:

```
AssertionError [ERR_ASSERTION]: retiring a review must also retire the chain the mainnet opt-in is read from
  expected: null,
```

The full gate was re-run with the fix in place: 240 Python tests, all nine
`tests/ui_*.cjs`, `git diff --check`, `bash -n` on every shell script, the
workflow YAML parse, and the source-archive build.

## What did not change

- The transaction and signing engine is unchanged from 0.5.1. Nothing about how
  a payment is built, signed, finalized or submitted changed.
- No user-visible behaviour changes. The final panel, the gate, the frame and
  the badge are as 0.6.1 left them.
- The mainnet opt-in still defaults to `False` in the backend, and the
  final-screen confirmation is unchanged.

## Deliberately out of scope

- **F2** — the custom mainnet broadcaster is not genesis-verified at broadcast
  time (`gui.py:905`; the mainnet `checkpoint_height` is `None`). Low severity:
  the transaction is already signed, so it cannot be stolen, and the explorer is
  verified during the scan. Left as recorded, not fixed here.
- **F5** — the `--dsh-check-libusb` debug flag ships in production
  `scripts/hwi_entry.py`.
- **F6** — `xattr -cr "$app"` in `scripts/build-macos.sh` strips bundle extended
  attributes, including quarantine.
- The plain-language operator guide and the nontechnical walkthrough remain
  deferred to the owner.

## Owner decisions

- The owner asked for the stale-review state to be fixed as 0.6.2, choosing it
  from three offered pieces of work (m01412).
