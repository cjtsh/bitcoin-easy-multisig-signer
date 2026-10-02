# 0.4.6 — signature checklist

Owner feedback on the installed 0.4.5 signing panel: after the first hardware
signature the next action was easy to miss. The progress line said “1 of 2
collected,” and the remaining control was labelled **Look for more devices**,
which does not read as “sign with the second device.”

## Change

The signing panel now shows one slot per required signature.

- A filled slot names the signer that already signed.
- The next empty slot is marked **next** and tells the operator to connect a
  different device, find it, and tap Sign.
- After the first signature, remaining device buttons read
  `Sign with {model} — signature 2 of 2`.
- The secondary search control is **Find the next device**.

No change to PSBT construction, signature verification, practice-network
broadcast, or the mainnet refusal. This is an interface correction only.

## Checks

- `id="sign-slots"` is required by `tests/test_gui.py`.
- `tests/ui_state_reuse.cjs` clears the slots and `collectedSigners` when a new
  payment is prepared.
- Device-error copy in `probe.py` still mentions “Look for more devices”; that
  is recovery advice, not the button label.

## Owner test

Install the 0.4.6 DMG. Prepare a Mutinynet payment, sign with one device, and
confirm the second slot is empty and labelled next before finding and signing
with the second device. Then broadcast. Do not use Clear unless the signed
bytes should be discarded.
