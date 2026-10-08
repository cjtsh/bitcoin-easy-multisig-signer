# 0.6.8: Color Team cycle-4 remediation

Version 0.6.8 answers the cycle-4 Color Team audit of the `v0.6.7` tree,
`bitcoin-easy-multisig-signer-colorteam-audit-report-v0.6.7.md` — SHA-256
`340495e93a46cface603291f88671f60b05198768c46f0c4b91ffe980f0e7ff0`, published on
`main` at commit `3f28ce2`. That cycle graded **⛔ BLOCKED**, and unlike cycle 3 it was
not set by process:

1. **Copper proved its own failure state** (rubric ruling 4) — **CT-90**: the
   source-mode hardware-helper payload pin could be made to *pass* while attacker code
   executed inside the very check that inspected it. The check imported the package it
   was inspecting, so a substituted `hwilib` that lied about `__file__` and planted a
   decoy `_cli` module was hashed as the genuine file. The frozen-bundle identity chain
   was intact, and the money path stayed guarded by the key-proof gates.
2. **Red found CT-72 (High)** — a BSMS that names the same signer xpub twice under two
   different origin fingerprints parsed as an honest 2-of-2 wallet: the app showed two
   cosigner cards while **one** device approval was enough to finalize a payment. That
   is quorum deception in the operator's own wallet file, reproduced end to end twice.

This release is an audit-ledger remediation. The wallet, transaction, signing and
broadcast policy is unchanged, and every change below can only *refuse* an input that was
previously accepted. This sentence was corrected in cycle 5 (CT-116): it is not true that
the payment engine changed "in exactly two places". The CT-72 parse gate and the CT-90
payload check were the two *grade-setting* changes; the same revision also re-hashed every
verified helper path on each cache hit (CT-91), put the session token in front of the two
GET feeds (CT-74/CT-75), and changed how the helper and its check child are invoked
(`-I -P`, passed as argv rather than written into the command line). No new payment
capability is added.

Every finding below is closed either by a test demonstrated able to fail (broken on a
disposable copy, watched red, restored) or by a documentation/residual disposition
stated in the open. **Nothing is closed by silence**, and no owner acceptance is
invented. CT-97 was the one item that needed the owner's decision; the owner
directed option B on 2026-10-07, its repository half is implemented here, and the remaining
owner step is scripted — see
[CT-97 fixed in repository settings](#ct-97-fixed-in-repository-settings).

## Finding → fix → test

The 33 findings the cycle-4 report carried, in its numbering.

| ID | Sev | Fix | Closing evidence |
| --- | --- | --- | --- |
| CT-72 | High | The BSMS parse refuses a wallet file that lists the same signer **key material** twice — the public point plus the chain code — even when the copies carry different origin fingerprints *and* are spelled under different network versions. A fingerprint is a label and a base58 string is a spelling; only the key bytes answer "how many keys must approve this payment". A second, independent gate in `signing.py::parse_multisig_script` refuses a compiled witness script that names the same public key twice, so a duplicate cannot reach finalization by any other route. **Corrected in cycle 5 (CT-115):** the closing evidence first cited here was the pre-existing *fingerprint* gate, which a respelled duplicate evades; that evasion is exactly what cycle 5 closed. | `tests/test_probe.py::test_one_key_listed_twice_under_two_origins_is_refused`, `::test_the_same_key_pasted_twice_keeps_its_fingerprint_refusal` (the fingerprint gate — green while the key gate was absent, which is why it was not evidence for CT-72), `::test_the_same_key_respelled_under_another_version_is_still_refused` (xpub/tpub/upub/ypub/zpub), `::test_a_respelled_duplicate_is_refused_even_when_the_fingerprints_differ`; `tests/test_signing.py::test_a_compiled_script_with_a_duplicated_pubkey_is_refused`, `::test_a_duplicate_key_input_cannot_reach_complete_with_one_signature`; break-and-watch: with the base58 comparison restored the hostile file parses as an honest 2-of-2 and one approval finalizes it |
| CT-73 | Med | The publish-path sweep now recognizes every publisher the audit used to evade it — `gh api`, direct REST uploads (`uploads.github.com`), `api.github.com`, third-party release actions (`action-gh-release`, `release-action`, `upload-release-asset`, `create-release`, `gh-release`), `permissions: write-all` — and requires every non-main ref that carries a workflow to *show* a read-only token (`permissions: read-all`, `{}`, or `contents: read`). Silence is an offender: an omitted block inherits a repository default no ref can disclose. | `tests/test_workflow_config.py::PublishPathSweepTests` (six new refusal tests + a read-all accept test); sweep run clean against the live remote |
| CT-74 | Low | The loopback token comparison is total. A non-ASCII `X-Local-Token` header (decoded latin-1) used to raise `TypeError` out of `hmac.compare_digest` before the 403 path, dropping the socket and printing a traceback per request. Both sides are now compared as bytes, so every header value reaches the same 403. | `tests/test_gui.py::LocalGuiTests::test_a_non_ascii_token_header_reaches_the_403_and_not_a_crash` (break-and-watch: the old inline comparison → `TypeError: comparing strings with non-ASCII characters is not supported` + `ConnectionResetError`) |
| CT-75 | Info | `GET /api/price` and `GET /api/fees` now require the session token, like every other route. The page itself stays unauthenticated (the token lives in the URL fragment); the UI's two feed fetches send the header. | `tests/test_gui.py::LocalGuiTests::test_the_feeds_refuse_a_caller_without_the_token` (patches both fetchers so a broken gate answers 200 instead of reaching the network) + the renamed token-gated cache tests |
| CT-76 | Info | The sweep empties `refs/remotes/publish-audit/*` on the way **out** as well as before it starts — `trap cleanup EXIT`, so the refusal path and any `set -e` failure clean up too. A read-only sweep may not change what the caller sees. | `tests/test_workflow_config.py::PublishPathSweepTests::test_the_sweep_leaves_no_private_refs_in_the_callers_repository` (break-and-watch on the pre-fix script: 15 refs left behind, seven tests red) |
| CT-77 | Med | The candidate-build `exit 0` is pinned to its own branch: the test slices from the message to the branch's own `fi` and requires the `exit` to be the **last** statement in it, so a statement after the exit can no longer absorb the refusal. | `tests/test_workflow_config.py::PublishGuardBranchPins::test_every_publish_guard_ends_at_its_own_exit` (four deletions, four red) |
| CT-78 | Med | Same pin for the tag-exists no-overwrite refusal (`exit 1`). | idem (`finding='CT-78'`) |
| CT-79 | Med | Same pin for the GPG fail-closed refusal (`exit 1`) in the signing step. | idem (`finding='CT-79'`) |
| CT-80 | Med | Same pin for the unsigned/unnotarized release refusal (`exit 1`). | idem (`finding='CT-80'`) |
| CT-81 | Low | The root cause CT-77…80 named — a guard pin blind to refusals that share one multi-statement `run:` block — is closed for the publish path by the new branch-level pin class. `GuardBodyPins` itself is unchanged; it still pins the single-body guard steps. | idem (`PublishGuardBranchPins`) |
| CT-82 | Info | Positive observation: the PATCH candidate-run narrative was corroborated with no discrepancy. No action. | cycle-4 report, §"New findings" |
| CT-83 | Med | The build-time fee-consistency gate is pinned: a selector whose reported total disagrees with the inputs it hands back is refused with the exact message. (A pure fee misquote genuinely cannot trip this gate — the packet's fee follows the quoted fee — so the test lies about the reported total, which is the divergence the gate exists to catch.) | `tests/test_money_path_pins.py::BuildTimeFeeConsistencyPins` (break-and-watch: gate disabled → `WalletError` not raised) |
| CT-84 | Low | The key-proof message digest is now checked against **published, external vectors** — the Bitcoin Signed Message envelope prefix and the two published `magicHash` digests from bitcoinjs-message's fixtures, plus a published signature verified against the published key. The pre-existing tests only round-tripped through the same function, so they could not see drift. | `tests/test_hardening_pins.py::MessageDigestVectorPins` (break-and-watch: the envelope prefix changed → 4 red, while the old CT-14 device tests stayed green — the blind spot the audit named) |
| CT-85 | Low | The recipient round-trip check is pinned by simulating the lenient-decoder threat the vendored parser (CT-89) makes credible: a decoder that returns a different address's script must be refused, not paid. | `tests/test_money_path_pins.py::RecipientRoundTripPins` (break-and-watch: the round trip removed → the build pays the change script) |
| CT-86 | Low | The `wallet_layout` first-receive re-derivation is pinned: a parsed record whose `reference_address` is not receive-0 is refused with its exact message. | `tests/test_wallet_service.py::WalletServiceTests::test_a_reference_address_that_is_not_receive_zero_is_refused` (break-and-watch: gate disabled → `WalletError` not raised) |
| CT-87 | Info | Documented, not changed. The 10,000,000-sat absolute floor term is subsumed by the 4,000,000-sat untrusted-quote term today, but it is deliberately retained: the gate is conservative, and the absolute floor must not be coupled to the quoted-price floor — a future price change must not be able to raise the absolute floor. | `gui.py` gate + `ui.html` mirror + `tests/test_gui.py::LargeAmountMirrorPins` |
| CT-88 | Info | Documented by design. The threshold comes from the operator's own BSMS file (an `AGENTS.md` invariant: any valid 2-or-3-key set, threshold from file), so a 1-of-N quorum in the file is honored like any other. Import-time emphasis is not a control. | `AGENTS.md`; `tests/test_probe.py` |
| CT-89 | Info | Residual documented. The vendored embit raw decoder accepts unknown-HRP bech32; the app-level address-prefix gate plus the recipient round trip is the only defense — and that round trip is now pinned (CT-85). Vendor internals are out of scope by the standing plan. | `tests/test_money_path_pins.py::RecipientRoundTripPins`; `vendor/README.md` |
| CT-90 | Med **the blocker** | The payload check no longer executes the package it inspects. It locates files with `importlib.machinery.PathFinder.find_spec` (hashing `spec.origin` / `sub.origin`) instead of importing them, the child no longer runs library code at all, and both the check and the helper run under the same scrubbed interpreter (`-I -P`), so the two sides see the same package and the environment cannot point the check elsewhere. The false comment claiming poisoned site-packages was refused is gone. | `tests/test_hardening_pins.py::HwiIdentityPins::test_a_hwilib_that_lies_about_its_files_is_refused_without_running_it` (the attack, over a real subprocess: old script wrote its marker and the pin *passed*; the new one executes nothing and refuses), `::test_the_check_and_the_helper_import_the_same_package`, `::test_the_payload_check_accepts_a_package_whose_bytes_are_recorded`, `::test_a_substituted_hwilib_payload_is_refused`; plus a genuine `hwi==3.2.0` install from the hash-locked file whose published digests match the pins (audit transcript, not a committed test — the repo venv stays hwilib-free, CT-96) |
| CT-91 | Low | The identity cache no longer outlives the file. Each verified path records the `(path, digest)` pairs it verified; a cache hit re-hashes them and only then returns. A helper swapped inside one signing session is refused. | `tests/test_hardening_pins.py::HwiIdentityPins::test_a_helper_swapped_inside_one_session_does_not_inherit_the_verdict`, `::test_an_unchanged_helper_is_still_checked_only_once`, `::test_begin_signing_session_clears_every_cached_identity` (break-and-watch: old plain-path cache → `ProbeError` not raised) |
| CT-92 | Low | The frozen helper refuses a **linked** bundled USB library before loading anything: the extraction directory is writable by this user and `Path.resolve()` follows links, so a planted symlink satisfied every path comparison while loading other bytes. Both the pre-load check and the post-load equality check now reject a link. | `tests/test_hwi_entry.py::test_frozen_helper_refuses_a_linked_bundled_library`, `::test_the_libusb_preflight_refuses_a_linked_library` (break-and-watch: old code printed `Bundled libusb: /private/var/…/libusb-1.0.dylib` and accepted the linked path) |
| CT-93 | Info | Documented: an operator who passes an explicit `--hwi` is choosing that helper, and the app still requires the helper and its sidecar to agree. Operator trust decision, unchanged. | `probe.py` explicit-path branch; `tests/test_hardening_pins.py` |
| CT-94 | Info | Documented by design: the app binds to the device by possession and key proof, not by firmware version reporting — possession-based binding is the stronger property. | `probe.py`; cycle-4 report §"New findings" |
| CT-95 | Info | Residual documented: the bridge URL pin returns true when the window's URL cannot be read, a decision its own comment records; the compensating control is the payload byte-equality check. Unchanged this cycle. | `desktop.py:69-82` |
| CT-96 | Info | Residual documented: hwilib is intentionally absent from the CI requirement set, so the payload pin's real-install accept path runs in desktop builds. The gap is narrowed by the CT-90 fixture accept test (real subprocess), the literal published-digest test, the desktop lock job that hash-verifies hwi 3.2.0, and the genuine-install transcript. | `tests/test_hardening_pins.py`; `requirements-desktop.lock:489` |
| CT-97 | Med | **Fixed (owner directed option B, 2026-10-07).** The release credentials are no longer repository secrets: they live in the `release-signing` and `apple-signing` GitHub environments, each deployable only from `main` and declaring no human gate, and the jobs that use them declare their environment. An old tag runs its own frozen workflow text but cannot deploy to either environment. All five stored values are environment-scoped as of 2026-10-08. A sixth name, `MAC_NOTARY_KEY_P8_BASE64`, is referenced by the optional notarize path and is not stored in either environment yet; since cycle 5 (WO-4) the check derives its watched set from the workflow text, so that name is covered the day it appears instead of being missed, and it is refused if it turns up at repository level or in the wrong environment. | `.github/workflows/build-candidate.yml`; `tests/test_workflow_config.py::ReleaseCredentialScopePins`; `tests/test_release_credentials.py`; `scripts/check-release-credentials.sh`; `scripts/provision-release-credentials.sh`; `SIGNING.md`; `RELEASE-PROCESS.md` |
| CT-98 | Low | The dispatch input `candidate_run_id` reaches the release-gate script through `env:`, never interpolated as `${{ }}` into the shell text, so a value like `1; something` is data the numeric test judges rather than code bash runs. The checksums job already did it this way. | `tests/test_workflow_config.py::test_publication_is_restricted_to_the_default_branch` (now asserts the env delivery and the absence of any `${{` in the run body) |
| CT-99 | Low | The container proof runs a digest-pinned image — `ubuntu:24.04@sha256:534baea6a22c03a63003dbc8dbe78fe34bc0d7e595d9a9dc9834884ff530eb55` — with the refresh command recorded in a comment. | `tests/test_linux_port.py::LinuxWorkflowTests::test_the_promise_of_no_libfuse_so_2_is_proven_where_the_library_is_absent` (asserts the full digest pin) |
| CT-100 | Low | Addressed by disclosure. Every per-platform SBOM now records the toolchain that produced it (`toolchain_platform`, `toolchain_python`, `toolchain_cc`, `toolchain_clang`, `toolchain_msbuild`, `toolchain_docker` — first banner line, or `not found`), so drift inside a pinned runner label is *visible in the attested artifact*. Bit-reproducible builds are still not claimed: runner images, apt, MSVC and Docker tags float inside GitHub's pinned labels and are trusted infrastructure not inspectable from this repository. | `tests/test_build_sbom.py::ToolchainDisclosurePins` (five tests, including a real probe on this interpreter) |
| CT-101 | Info | The source tarball now carries `signing-key.asc`, so a tarball-only verifier can run the `gpg --import signing-key.asc` step `SIGNING.md` and `RELEASE-PROCESS.md` tell them to run. | `tests/test_build_source.py::ArchiveCompletenessTests::test_the_signing_key_reaches_the_archive` |
| CT-102 | Info | The recipe comments no longer spell out the sweep's own matcher patterns (the false-positive direction only). Its own recipe lookup now goes through `support.find_build_recipe`: the inline read broke the `Source archive and tests` job on the 0.6.8 candidate run, because the archive ships the recipes under `ci/` and has no `.github` at all — the third time this repository has paid for that lookup. | `tests/test_workflow_config.py::PublishPathSweepTests::test_the_recipe_comments_do_not_spell_out_their_own_matchers` |
| CT-103 | Low | Both comment-satisfiable pins now assert the live code. The sweep's `cat-file` pin strips comment lines before asserting, and the large-amount message pin slices the actual refusal and asserts the triggers in it — each previously stayed green for its named regression because a comment carried the string. | `tests/test_workflow_config.py::SweepFailClosedPins::test_the_bodies_come_from_object_ids_not_from_rev_colon_path`; `tests/test_gui.py::LargeAmountMirrorPins::test_the_prepare_refusal_names_every_trigger` (both broken both ways and watched red) |
| CT-104 | Info | `releases/PATCH-0.6.7.md` no longer claims the acceptance note carries a per-item tripwire for every item; it says what the note says (an explicit reopening tripwire where a later change could erase the rationale, a design property otherwise), and the note itself now states that a future note should carry its own tripwires. | `releases/OWNER-ACCEPTANCE-2026-10-07.md`; this repository's own history |

## The two grade-setting fixes, in plain words

**CT-72 — "how many keys must approve this payment?"** A multisig wallet file names
each cosigner key and gives each a fingerprint label. The app used to count *labels*
when it displayed "2 of 2" and when it checked that a wallet is honest. An attacker —
or a mistake — could paste the same key twice with two different labels, and the
screen would show two cosigner cards while one device approval was enough to sign. The
app now counts **key bytes**, and refuses a wallet file that lists the same key twice.
Nothing about a legitimate wallet changes; a file that names each cosigner once parses
exactly as before.

**CT-90 — "is the helper the helper?"** Before a hardware helper may talk to a device,
the app hashes the library files it is made of and compares them to digests recorded in
this repository. That check used to `import` the library in order to ask it where its
files were — which runs the library's own code. A substituted library could therefore
execute inside the check and then lie about its path, so the digests matched and the
check passed. The app now locates the files **without running them**
(`PathFinder.find_spec`), runs the check and the helper under the same scrubbed
interpreter, and refuses anything whose bytes do not match. The audit's own attack now
executes nothing and is refused.

## Cycle-5 remediation: the classes, not the demonstrations

Cycle 5 (`bitcoin-easy-multisig-signer-colorteam-audit-report-v0.6.8.md`) graded this
revision **⛔ BLOCKED** on three independent failure states — Red (CT-72), Orange (CT-73)
and Copper (CT-90) — with CT-72 open as a High. The process post-mortem in that report is
the reason this section exists: the cycle-4 fixes each closed the *demonstration* the audit
had used, and a green test then meant "the old proof of concept fails", never "the class is
closed". This round fixes the classes and, where a class cannot be closed inside the
repository, says so in the open.

| ID | Sev | The class | Fix and evidence |
| --- | --- | --- | --- |
| CT-72 | High | Identity of a signer key | The duplicate gate compares **key material** — `(public point, chain code)` — instead of a base58 string, and `parse_multisig_script` independently refuses a compiled witness script naming one public key twice. Evidence: the four rows of `tests/test_probe.py` and the two `tests/test_signing.py` cases listed in the CT-72 row above, each demonstrated red against the previous source. |
| CT-90 | Med | Whole-payload identity, interpreter isolation, verify-at-execution | `HWI_PAYLOAD_MANIFEST` records all 115 `.py` files of the pinned hwilib tree as literals in `probe.py` — not a digest read from `RECORD`, which the same writer who replaced the tree could rewrite. The check child runs `-I -S -P`, so a `.pth` in site-packages cannot execute inside it — `-I -P` alone does not stop site hooks. Because `-S` removes site-packages from the child's path, the child cannot resolve `hwilib` by name at all; the parent passes the package roots as argv and the child reports every file it finds there. The whole name set is compared in both directions, the CT-91 cache re-reads all of it, and `_require_unchanged()` reads every file the child reported a second time immediately before the spawn, so a deterministic swap written between the check and the exec is refused instead of inheriting a verdict about bytes that no longer exist. Every prepared build environment runs `scripts/check-hwi-payload.py` against the real hash-locked install before any signing material enters the job. Evidence: `tests/test_hardening_pins.py::HwiIdentityPins::test_the_ci_payload_check_runs_the_app_check_and_fails_closed`, `::test_the_check_child_cannot_run_a_pth_hook_planted_in_site_packages`, `::test_a_swapped_sibling_module_does_not_inherit_a_cached_verdict`, `::test_a_payload_swapped_between_the_check_and_the_spawn_is_refused`; `tests/test_workflow_config.py::test_each_prepared_build_environment_proves_its_hwilib_matches_the_pin`. Break-and-watch used a **genuine** `hwi==3.2.0` install: the previous source accepted a `commands.py` with one injected line (and an added `zz_extra.py`) while reporting two files verified; the current source refuses it. |
| CT-73 + CT-102 | Med + Info | The sweep's decision procedure | `scripts/check-publish-paths.sh` now strips comments before **any** decision and decides the token grant from a parsed `permissions:` mapping: a spaced key (`contents : write`), a quoted flow mapping, a duplicate key, `write-all`, and a bare nested `write` are all read as the grants they are, while a comment naming a write grant is no longer an offender. The read-only proof comes from the mapping, never from body text. The publisher vocabulary gained `gh api graphql`, `$GITHUB_API_URL`, `actions/github-script`, camelCase REST release calls and reusable release workflows whose path names a release. Evidence: ten new `PublishPathSweepTests` cases, seven separate breaks each watched red, and the live `origin` sweep still clean. The sweep stays bash + git: `PublishPathSweepTests` deliberately does not gate it on PyYAML. |
| CT-97 | Med | The watched credential name set | `scripts/check-release-credentials.sh` derives its watched names from the workflow text — every `secrets.NAME` reference, partitioned by the environment each referencing job declares — instead of a hand-typed list of five. The sixth name, `MAC_NOTARY_KEY_P8_BASE64`, is covered the day it appears. The rule is one-directional exactness plus non-vacuity: an extra name is refused, an environment holding none of its own names is refused, and a referenced-but-absent name is reported as a `note:` rather than a refusal, because the workflow reads the notary key only on the optional notarize path while every required credential is guarded by `: "${NAME:?}"`. `--print-scope` prints the derived table so the next reader can see what the check believes. Evidence: `tests/support.py::workflow_credential_scope`, `tests/test_release_credentials.py` (21 tests), `ReleaseCredentialScopePins`, and seven breaks. |
| CT-105 | Med | The Windows helper's trust model | The claim that a frozen build's sidecar "sits inside the signed bundle it authenticates" is true on macOS only. On Windows `hwi.exe` and `hwi.sha256` sit in the same user-writable directory and neither is signed, so the app's sidecar check there is a corruption check, not an identity check. That is now stated in `probe.py`, `scripts/build-sbom.py`, `HWI-DEPENDENCY.md` and a new `SIGNING.md` section, and pinned by `tests/test_hardening_pins.py::HwiIdentityPins::test_the_identity_docstring_does_not_claim_a_windows_signature`. Signing the Windows helper or moving the sidecar out of the writable directory are **owner decisions, open as of 2026-10-08**, recorded as such rather than invented here until the owner picks one. |
| CT-92 | Low | Link, not only symlink | `scripts/hwi_entry.py` opens the bundled USB library with `O_NOFOLLOW`, then requires `fstat` to report a regular file with `st_nlink == 1`, both before the load and in the post-load equality check. A hard link has no distinct path to resolve, so `is_symlink()` alone never saw it. Evidence: `tests/test_hwi_entry.py` now plants **real** links instead of monkeypatching `Path.is_symlink`; the hardlink test is red when either the `O_NOFOLLOW` or the `st_nlink` arm is removed, and the symlink test stays green. |
| CT-98 · CT-107 · CT-108 · CT-109 · CT-110 · CT-113 · CT-114 | Low–Info | Small pins and honest wording | `candidate_run_id` expressions are pinned out of **every** run block that consumes the input, not just the version job's guard (CT-98). The provisioning script's header no longer claims argv never carries a value; it names the two windows that do (`security export -P`, `notarytool store-credentials --password`) and pins them (CT-107). The broadcast identity clause has a test that actually drives the swap window (CT-108, `tests/test_send_flow.py::test_broadcast_refuses_when_the_prepared_payment_is_swapped_mid_flight`). `_clean_token` and `_device_class` have direct drop tests (CT-109). The three unquoted version interpolations are quoted and pinned (CT-110). `do_GET` records why it has no Origin check and a test pins that the token is the whole control there (CT-113). The BOM strip removes exactly one BOM instead of a character set (CT-114). |
| CT-100 · CT-106 · CT-111 · CT-115 · CT-116 | Info | Disclosure, not silence | `ToolchainDisclosurePins` asserts a literal expected probe-name set instead of iterating the table it is testing (CT-100). The release-environment comment says the gate protects the secret, not the environment, and a test refuses a job-level `if:` that would make the claim true by accident (CT-106). The explorer limitation is documented in `README.md` and `USER-MANUAL.md`: a self-consistent liar can drive preparation over phantom funds, preparation moves nothing, broadcast refuses a mismatched transaction ID rather than claiming success, and a mainnet lie must survive the signers' screens (CT-111). The two false statements in this ledger were corrected in place (CT-115, CT-116). |

**What this round does not claim.** No new payment capability; the money path still holds
and every change here can only refuse. The vendored-decoder residual (CT-89), the
explicit-helper operator choice (CT-93), the bridge-URL fallback (CT-95) and the
practice-network scan limits stand as documented. Two items remain **owner decisions**, not
agent calls: whether the Windows helper gets an Authenticode signature or the sidecar moves
out of the writable directory (CT-105), and whether the human gate on `release-signing`,
removed in this cycle, is restored or the environment is moved onto a publish-only job
(CT-106/CT-97).


## The prior ledger, round-tripped: CT-01…CT-71

Cycle 4 enumerated the cycle-3 ledger (CT-01…CT-71, hash re-verified) and every ID was
accounted for. This cycle re-carries that enumeration in full, with the cycle-4
disposition; the cycle-4 report is the authority for each line. No prior finding is
missing, and none is closed by silence here.

| IDs | Cycle-4 disposition | This cycle |
| --- | --- | --- |
| CT-01 | Fixed (release-channel remediation: out-of-gate `v0.6.5-windows-x64` release and the manually uploaded v0.6.4 assets deleted) | carried; no code path touched |
| CT-02 · CT-03 · CT-04 · CT-05 · CT-06 · CT-07 · CT-08 · CT-09 · CT-10 · CT-11 · CT-12 | Fixed in cycles 1–3, carried verified (engine byte-identical v0.6.6→v0.6.7) | carried; pins green in the full suite |
| CT-13 | Fixed in cycle 1, re-derived in cycle 3 | carried |
| CT-14 | Fixed, re-derived | carried |
| CT-15 | Fixed | carried |
| CT-16 | Fixed; no recurrence observed | carried |
| CT-17 | Fixed; folded into CT-55 (full-patch Python pin) | carried |
| CT-18 · CT-19 | Fixed | carried |
| CT-20 | Fixed, re-derived | carried |
| CT-21 | Fixed (vsize half → CT-31c) | carried |
| CT-22 | Closed as observation | carried |
| CT-23 | Accounted via decomposition (→ CT-29 + CT-35) | carried |
| CT-24 | Fixed | carried |
| CT-25 | Positive hold (verified property) | carried |
| CT-26 | Fixed, re-derived (BIP-143 vectors) | carried |
| CT-27 | Fixed (superseded dual release removed) | carried |
| CT-28 | Fixed, re-derived (money-path pins) | carried |
| CT-29 · CT-30 | Fixed | carried |
| CT-31 (a–d) | Fixed | carried |
| CT-32 | Fixed | carried |
| CT-33 | Fixed; folded into CT-57 (lock-writer pin) | carried |
| CT-34 | Fixed, re-derived | carried |
| CT-35 · CT-36 · CT-37 · CT-38 · CT-39 · CT-40 · CT-41 · CT-42 · CT-44 · CT-47 | Closed by dated owner acceptance (2026-10-07, ruling 2) | carried closed |
| CT-43 · CT-45 · CT-46 | Fixed in cycles 1–3 | carried |
| CT-48 | The cycle-3 High, verified fixed in cycle 4 (13 deletion commits, sweep clean on the live remote, guards re-broken red) | carried; the sweep is now stronger (CT-73/76) |
| CT-49 | Fixed and pinned in frozen mode; residual became CT-90 | residual **fixed** (see CT-90 above) |
| CT-50 · CT-51 · CT-53 · CT-55 · CT-56 · CT-57 · CT-60 · CT-71 | Verified fixed with fail-capable pins | carried; suite green |
| CT-52 | Verified fixed; residual became CT-77…80 | residual **fixed** (CT-77…80 above) |
| CT-54 | **Open dated deferral** — rebuild `vendor/libusb-1.0.0.dylib` from pinned upstream source at the next dependency bump. Hard expiry 2027-10-07 | still open, unchanged |
| CT-58 | Verified fixed; residual became CT-91 | residual **fixed** (CT-91 above) |
| CT-59 | **Open dated deferral** — a stalling explorer can make one scan slow; the scan fails closed and claims nothing. Hard expiry 2027-10-07 | still open, unchanged |
| CT-61 · CT-63 · CT-64 · CT-65 · CT-66 · CT-67 · CT-68 · CT-69 · CT-70 | Closed by dated owner acceptance (2026-10-07) | carried closed |
| CT-62 | Verified fixed; pin caveat became CT-103 | pin **fixed** (CT-103 above) |

## CT-97 fixed in repository settings

Cycle 4 filed CT-97: *historical tags (`v0.1.0`…`v0.6.3`) freeze dispatchable publishers
with today's secrets, gated only by release-existence; the sweep never scans tags.* All 66
tags from `v0.1.0` on carry a dispatchable `build-candidate.yml`, and the pre-0.6.4 ones
lack the default-branch guard, so dispatching one runs that tag's own frozen workflow text
with whatever credentials the repository holds **today**.

**Owner decision, 2026-10-07: option B — scope the credentials to protected environments.**
The owner directed the permanent form of the fix rather than a dated acceptance, on the
grounds that the project will cut many more releases.

Why a settings change is the permanent fix: the control is a rule about *which ref a run is
on*, not a list of tags. A repository secret is handed to a job on **any** ref; an
environment secret is handed only to a job that declares that environment *and* only when
the environment's deployment rule admits the ref. An old tag never declares the environment,
so it gets nothing even though its frozen workflow names the secret. A tag created in the
future carries a workflow that does declare it and is still refused, because the deployment
rule admits `main` only. Enumerating and cleaning 66 tags would have to be repeated forever;
this does not.

Implemented in this revision:

- `.github/workflows/build-candidate.yml` declares `environment: apple-signing` on the
  `macos` job and `environment: release-signing` on the `checksums` job. The Apple steps run
  only under `if: ${{ inputs.notarize }}` and the GPG step only under
  `if: ${{ inputs.publish }}`, so a candidate build never enters either environment.
- `tests/test_workflow_config.py::ReleaseCredentialScopePins` fails the build if a job names
  a release credential without declaring its environment, if the job→environment map
  changes, or if any other workflow file names a credential at all.
- `tests/test_release_credentials.py` drives `scripts/check-release-credentials.sh` against
  fixtures for every refusal: a repository-level copy, a tag-scoped branch policy, a human
  gate (a required reviewer or a wait timer), a missing or misplaced environment secret, and
  a missing environment.
- `scripts/check-release-credentials.sh` is the standing read-only check of the platform
  half. Run it before every promotion and in every audit cycle.
- `scripts/provision-release-credentials.sh` is the recovery path the owner asked for. It
  re-derives every credential this machine can — the release key from the GnuPG keyring, the
  Developer ID p12 plus a fresh password from the login keychain, the app-specific password
  from a hidden prompt or a file — sets each one with `gh secret set` on standard input so no value
  sent to GitHub reaches argv, a log or a transcript, deletes the repository-level copies with
  `--prune`, and finishes by running the check. `--dry-run` names every secret it would set
  and touches nothing. Corrected in cycle 5 (CT-107): the header used to claim argv is never used at
  all. Two local tools on this path (`security export -P`, `notarytool store-credentials --password`)
  offer no other form, so those windows are named and pinned rather than denied.

**Live platform state, 2026-10-08.** Both environments exist under the owner's account
(GitHub settings, not files in this repository): `release-signing` holds `GPG_PRIVATE_KEY`
and `GPG_PASSPHRASE`, `apple-signing` holds `MAC_CERT_P12_BASE64`, `MAC_CERT_PASSWORD` and
`MAC_APP_SPECIFIC_PASSWORD`. All five values are environment-scoped and the repository
secret list is empty. The optional notarize path also names `MAC_NOTARY_KEY_P8_BASE64`, which is not
stored in either environment as of that date; `scripts/check-release-credentials.sh` reports it as a
`note:` rather than a silent omission (cycle 5, WO-4). Each environment allows only the `main` branch
and declares no required reviewer and no wait timer, so a promotion starts on its own and any agent team the
owner authorises can cut a release. The last value, `MAC_APP_SPECIFIC_PASSWORD`, was moved
**without owner action**: a temporary workflow sealed it to an RSA key that existed only on
the maintainer's machine and printed only the ciphertext, so nothing readable ever entered a
run log of this public repository; the throwaway workflow, its runs, the ciphertext and the
key material were all deleted afterwards. `scripts/check-release-credentials.sh` prints
`ok: the release credentials are environment-scoped, main-only, and unreachable from any
tag`. `SIGNING.md` carries the master-copy table and the recovery path;
`RELEASE-PROCESS.md` §5 makes the check a promotion step.

## Documented residuals

Kept deliberately, with reasons, so a later reader does not mistake them for oversights:
CT-87 (conservative dead disjunct retained), CT-88 (threshold from the owner's file by
design), CT-89 (vendored decoder leniency; the app-level round trip is pinned), CT-92
(the extracted `_MEI*` copy's bytes are path- and load-checked — now including a real link
check (`O_NOFOLLOW`, `S_ISREG`, `st_nlink == 1`) added in cycle 5 — but still not digest-compared
against a build record: the macOS digest is a source constant in
`scripts/build-macos.sh`, Windows checks the `LIBUSB_WINDOWS_SHA256` variable, Linux
builds from source), CT-93 (explicit-helper operator trust), CT-94 (possession-based
device binding by design), CT-95 (documented bridge-url fallback, compensated by payload
byte-equality), CT-96 (hwi absent from CI requirements; accept path covered by fixture,
published digest, desktop lock job and a genuine-install transcript), CT-54/CT-59
(dated deferrals, hard expiry 2027-10-07).

## Verification on this revision

- The full Python suite on the rolled 0.6.8 tree: `Ran 580 tests` — **OK**, zero skips,
  zero failures (573 before this revision's provisioning-script pins, which add a class of
  6, plus the gate-free wait-timer pin). Run it from the repository root, as `README.md`
  documents
  (`.venv/bin/python -m unittest discover -s tests -q`): one test spawns
  `python -c "import safe_http"`, which cannot resolve from inside `tests/` and fails
  there for that reason alone.
- The UI DOM suites: all ten `tests/ui_*.cjs` files pass under `node`.
- `bash -n` clean on every shell script touched (`scripts/check-publish-paths.sh`,
  `scripts/build-source.sh`, `scripts/check-release-credentials.sh`,
  `scripts/provision-release-credentials.sh`); every `.github/workflows/*.yml` parses
  under `yaml.safe_load`.
- Every fix above was break-and-watched on a disposable copy (`/tmp/besa-break` …
  `/tmp/besa-break10`): the control ran green, the named regression
  was introduced, the named test went red, the copy was restored byte-identical
  (`cmp`), and the control ran green again. The transcripts of the two grade-setting
  breaks (CT-72, CT-90) are the strongest form of this: with the old code the attack
  *succeeds*, and with the new code it executes nothing.
- The `Source archive and tests` job is green from the built archive, and the archive
  failure is reproducible. `bash scripts/build-source.sh 0.6.8`, extracted and run from
  `/tmp/archive-check/bitcoin-easy-multisig-signer-v0.6.8`: `Ran 580 tests` — **OK**. On a
  copy of that archive, reverting only the CT-102 recipe lookup to the inline read raises
  the job's own `FileNotFoundError: .github/workflows/linux-inputs.yml`, and the tightened
  pin in `tests/test_windows_portability.py` goes red on the same reverted tree with the
  message that names the 0.6.8 archive failure. Candidate run 37781832229 (the one that
  found it) failed the job at `7d43464`; run 37779757281 failed it at `2f779e2`. Run
  37783584533 at `1a5e9bf` is the first fully green candidate: all seven jobs success,
  including `Windows x64 bundle` and `Source archive and tests`, with the publish step
  taking its documented `publish=false` refusal path — no tag and no release, which the
  live release list confirms.
- CT-97's repository half was break-and-watched on a disposable copy. Deleting
  `environment: apple-signing` from the `macos` job →
  `test_every_job_that_names_a_credential_declares_an_environment` and
  `test_the_scope_map_is_exactly_the_documented_pair` red (2 failures). Removing the
  repository-level-secret loop from `scripts/check-release-credentials.sh` →
  `test_a_repository_level_copy_of_a_release_key_is_refused` red. Removing the main-only
  branch-policy check → `test_a_tag_that_could_deploy_into_an_environment_is_refused` red
  (with `bash -n` still clean in the broken copy, so the failure is the check's absence and
  not a syntax break). Each file was restored byte-identical (`cmp`) and the 15-test
  control run was green again.
- CT-97's gate-free half was break-and-watched the same way (`/tmp/besa-break9`): deleting
  the `gates=`/`if [[ -n "$gates" ]]` block from the check →
  `test_a_required_reviewer_is_refused` and `test_a_wait_timer_is_refused` red (2
  failures, `bash -n` still clean in the broken copy); making the wait-timer branch
  unreachable in `gate_lines` → `test_a_wait_timer_is_refused` red alone. Restored
  byte-identical (`cmp`), control green again.
- The provisioning script was break-and-watched on the same kind of copy (`/tmp/besa-break8`,
  6-test class). Passing the value in argv (`--body "$(cat …)"`) →
  `test_the_owner_path_carries_the_value_on_stdin_only` and
  `test_the_provision_script_never_passes_a_value_in_argv` red; any tool call before the
  dry-run `exit 0` → `test_a_dry_run_touches_nothing` red; a wrong pinned fingerprint →
  the documented-material test red; a dry run that no longer names `GPG_PRIVATE_KEY` →
  `test_a_dry_run_touches_nothing` red. Each file was restored byte-identical (`cmp`) and
  the control ran green again.
- The Windows leg of the suite was red on the first 2026-10-08 candidate (`Windows x64
  bundle`, run 37779757281): three provision tests called a bare `bash`, which on a Windows
  runner is the WSL launcher (`Windows Subsystem for Linux has no installed
  distributions`), and the check's own comparison failed because Windows Python writes
  CRLF and command substitution strips the newline but not the carriage return. Fixed by
  reaching bash through `support.bash_executable()` and by ending each Python→bash helper
  in `scripts/check-release-credentials.sh` with `tr -d '\r'`;
  `tests/test_windows_portability.py` now refuses a literal `["bash"` entry in
  `tests/test_release_credentials.py`, which is the pattern that broke that leg. Watched on
  `/tmp/besa-break10` with a `/tmp/crlf-bin/python3` shim that re-emits the real
  interpreter's output with CRLF: the fixed check passes; with all three strips commented
  out the positive test goes red under the shim and green under an honest POSIX python, so
  the break is exactly the CRLF handling; restoring the file (`cmp`) is green again, and
  reintroducing a literal `["bash", …]` makes the portability canary fail.
- `scripts/check-release-credentials.sh` run live against this repository **prints
  `ok: the release credentials are environment-scoped, main-only, and unreachable from any
  tag`** (exit 0) as of 2026-10-08: the repository secret list is empty, and both
  environments hold exactly their own names, allow only `main`, and declare no human gate.
- No wallet material, secret, or credential appears in this file or in the tests added
  by it; every fixture is synthetic.

## Verification of the cycle-5 remediation

- The full Python suite on this tree: `Ran 622 tests` — **OK**, zero failures, zero skips
  (580 at the cycle-4 roll; the 42 added here are the WO-1…WO-8 pins).
- `bash -n` clean on every shell script in `scripts/`; every `.github/workflows/*.yml`
  parses under `yaml.safe_load`; all ten `tests/ui_*.cjs` suites pass under `node`.
- `bash scripts/check-publish-paths.sh origin` against the live remote: exit 0,
  `ok: no non-main ref carries a publish-capable workflow`.
- `scripts/check-release-credentials.sh` against the live account (real `gh`, authenticated
  as the maintainer): exit 0, `ok: the release credentials are environment-scoped,
  main-only, and unreachable from any tag`, plus the expected `note:` for the unstored
  notary key.
- Break-and-watch, each on a disposable `git worktree` with the working files copied in,
  the named regression introduced, the named test watched red, the file restored
  byte-identical (`cmp`) and the control green again:
  - **CT-72** — the previous `probe.py`/`signing.py` on a detached `HEAD` worktree: the four
    new probe tests fail 7 times (the `subTest` version spellings) and the two signing tests
    fail, with the duplicate gate absent.
  - **CT-73/CT-102** — seven breaks: comment stripping disabled, the spaced-key regex
    narrowed, the flow-mapping arm disabled, `github-script` removed, the camelCase REST
    names removed, the `$GITHUB_API_URL` arm dropped, and the reusable-workflow match
    narrowed. Eight of ten new sweep tests are red against the previous sweep.
  - **CT-90** — a genuine `hwi==3.2.0` install with one line injected into `commands.py`
    (and later an added `zz_extra.py`): the previous source reports `accepted: 2 files` and
    passes; the current source refuses with
    `The hardware-wallet tool does not match its recorded digest. Refusing to run it.`
    Removing `-S`, or the child's tree gate, turns named tests red. Dropping the
    spawn-time re-read (`_require_unchanged`) turns
    `::test_a_payload_swapped_between_the_check_and_the_spawn_is_refused` red with
    `AssertionError: ProbeError not raised`, and nothing else.
  - **CT-97** — seven breaks (extra name, empty environment, missing policy, wrong policy,
    stray gate, repository-level copy, tag-scoped policy), each red.
  - **CT-92** — the previous `is_symlink()` guard: the hardlink test is red and the
    preflight accepts a hardlinked library; removing the `st_nlink` arm reproduces exactly
    that red while the symlink test stays green.
  - **CT-105** — the old "inside the signed bundle" sentence restored in `probe.py`, the
    SBOM sentence replaced, and the `SIGNING.md` heading renamed: three separate reds.
  - **CT-108** — the broadcast identity clause replaced with `if False:` in `_broadcast`
    only: the new send-flow test fails with
    `Expected 'broadcast_transaction' to not have been called. Called 1 times.`
- No wallet material, secret or credential appears in the tests added by this round; every
  fixture is synthetic, and the one genuine hwilib tree used for the CT-90 demonstration
  lived in `/tmp`, never in this repository.


## Publication

**Not yet published.** This revision is the candidate the owner reviews; the next Color
Team cycle audits this commit before any tag exists. Cycle 5 graded the previous revision
**⛔ BLOCKED** on the findings remediated above; this round is the answer to that grade and
has not itself been audited. Promotion to a public release requires, in order: the cycle-6
audit result, a signed and notarized `publish=false` candidate through the unified
pipeline, and the owner hardware walkthrough. Manual publication is prohibited.
