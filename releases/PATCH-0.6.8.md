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
(`-I -S -P`, passed as argv rather than written into the command line). No new payment
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
| CT-73 | Med | The publish-path sweep now recognizes every publisher the audit used to evade it — `gh api`, direct REST uploads (`uploads.github.com`), `api.github.com`, third-party release actions (`action-gh-release`, `release-action`, `upload-release-asset`, `create-release`, `gh-release`), `permissions: write-all` — and requires every non-main branch that carries a workflow to *show* a read-only token (`permissions: read-all`, `{}`, or `contents: read`). Silence is an offender: an omitted block inherits a repository default no ref can disclose. | `tests/test_workflow_config.py::PublishPathSweepTests` — the six publisher/token refusal tests and the read-all accept test added with this fix (the class held 18 cases at `bd0c0e8`, 44 at `f79203c`, 53 at `c6df346` (the wave-3 tree), 63 at the cycle-9 tree and 66 in the cycle-10 round, 104 on the round-14 tree, 118 on the round-19 tree and 121 on the round-20 tree, and holds 131 on this revision; its later growth is recorded in the CT-73 + CT-102 row, the cycle-11, cycle-12 and cycle-13 sections, the R2- rows and the W3- rows); sweep run clean against the live remote |
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
| CT-90 | Med **the blocker** | The payload check no longer executes the package it inspects. It locates the package by scanning `sys.path` for `hwilib/__init__.py` (`_hwi_package_roots()`; deliberately **not** `PathFinder.find_spec`, which an earlier draft of this row wrongly named), hands those roots to the check child as argv, and the child opens and hashes every file without importing anything; the child no longer runs library code at all. The check child runs `-I -S -P` and the source-mode helper now does too, each with an explicit search path — the check child as argv, the helper as a `-c` bootstrap that appends the verified roots after the interpreter's own entries — so no site hook can execute in either while the pinned package still imports. The manifest pins all 115 `.py` source files of the tree by digest; every other loadable file (`.so`, `.pyd`, `.dll`, `.dylib`, an extra `.py`, a `.pyc`/`.pyo`) is refused by a rule over its file suffix rather than by a digest, and a `.pyc` is accepted only when it recompiles to a manifest-verified source, so a planted `__pycache__` payload whose header matches the recorded source is refused (the cycle-5 adversarial pass planted one and the first version of this check passed it). The false comment claiming poisoned site-packages was refused is gone. | `tests/test_hardening_pins.py::HwiIdentityPins::test_a_hwilib_that_lies_about_its_files_is_refused_without_running_it` (the attack, over a real subprocess: old script wrote its marker and the pin *passed*; the new one executes nothing and refuses), `::test_the_check_child_runs_without_site_support`, `::test_the_check_child_does_not_start_a_site_hook`, `::test_the_roots_come_from_the_caller_not_the_environment`, `::test_a_planted_bytecode_file_is_refused`, `::test_the_interpreters_own_bytecode_is_accepted`, `::test_a_file_added_between_the_walks_is_refused`, `::test_the_payload_check_accepts_a_package_whose_bytes_are_recorded`, `::test_a_substituted_hwilib_payload_is_refused`; plus a genuine `hwi==3.2.0` install from the hash-locked file whose published digests match the pins (audit transcript, not a committed test — the repo venv stays hwilib-free, CT-96) |
| CT-91 | Low | The identity cache no longer outlives the file. Each verified path records the `(path, digest)` pairs it verified; a cache hit re-hashes them and only then returns. A helper swapped inside one signing session is refused. | `tests/test_hardening_pins.py::HwiIdentityPins::test_a_helper_swapped_inside_one_session_does_not_inherit_the_verdict`, `::test_an_unchanged_helper_is_still_checked_only_once`, `::test_begin_signing_session_clears_every_cached_identity` (break-and-watch: old plain-path cache → `ProbeError` not raised) |
| CT-92 | Low | The frozen helper refuses a **linked** — or otherwise non-regular — bundled USB library: the extraction directory is writable by this user and `Path.resolve()` follows links, so a planted symlink satisfied every path comparison while loading other bytes. The check now decides from the directory entry (`os.lstat`, before opening anything), keeps the `O_NOFOLLOW` open plus `fstat` (`st_nlink == 1`), and compares a `(st_dev, st_ino, st_size, st_mtime_ns)` identity **after** the load, so a library swapped in the check-then-load window is refused as well. | `tests/test_hwi_entry.py::test_frozen_helper_refuses_a_hardlinked_bundled_library`, `::test_frozen_helper_refuses_a_symlinked_bundled_library`, `::test_the_libusb_preflight_refuses_a_hardlinked_library`, `::test_a_library_swapped_between_the_check_and_the_load_is_refused`, `::test_the_libusb_preflight_refuses_a_fifo_without_blocking` (break-and-watch: the old path-identity code printed `Bundled libusb: /private/var/…/libusb-1.0.dylib` and accepted the linked path; removing the descriptor's `st_nlink == 1` condition reddens **both** hardlink tests while the symlink test stays green; removing the post-load identity comparison reddens the swap test; removing the `lstat` guard makes the FIFO case hang until the five-second thread join fails) |
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
check passed. The app now locates the package by scanning `sys.path` for
`hwilib/__init__.py` (`_hwi_package_roots()`, deliberately not `find_spec`) and hands those
roots to a check child that runs `-I -S -P` — no site hook, no import — so nothing in the
library executes inside the check, and since the second cycle-6 round the source-mode helper runs under the same `-I -S -P` isolation with the verified roots appended after the interpreter's own entries. Anything whose bytes
do not match is refused, and the audit's own attack now executes nothing and is refused.

## Cycle-5 remediation: the classes, not the demonstrations

Cycle 5 (`bitcoin-easy-multisig-signer-colorteam-audit-report-v0.6.8.md`) graded this
revision **⛔ BLOCKED** on three independent failure states — Red (CT-72), Orange (CT-73)
and Copper (CT-90) — with CT-72 open as a High. The process post-mortem in that report is
the reason this section exists: the cycle-4 fixes each closed the *demonstration* the audit
had used, and a green test then meant "the old proof of concept fails", never "the class is
closed". The rounds since have repaired the classes the audit demonstrated, and an
independent adversarial round has defeated the repair each time on a new shape, so
this section records what the reader now refuses and states in the open what a
repository-side rule cannot reach.

| ID | Sev | The class | Fix and evidence |
| --- | --- | --- | --- |
| CT-72 | High | Identity of a signer key | The duplicate gate compares **key material** — `(public point, chain code)` — instead of a base58 string, and `parse_multisig_script` independently refuses a compiled witness script naming one public key twice. Evidence: the four rows of `tests/test_probe.py` and the two `tests/test_signing.py` cases listed in the CT-72 row above, each demonstrated red against the previous source. |
| CT-90 | Med | Whole-payload identity, interpreter isolation, verify-at-execution | `HWI_PAYLOAD_MANIFEST` records all 115 `.py` files of the pinned hwilib tree as literals in `probe.py` — not a digest read from `RECORD`, which the same writer who replaced the tree could rewrite. The check child runs `-I -S -P`, so a `.pth` in site-packages cannot execute inside it — `-I -P` alone does not stop site hooks — and since the second cycle-6 round the source-mode helper runs under the same `-I -S -P` isolation with the verified roots appended after the interpreter's own entries. Because `-S` removes site-packages from the child's path, the child cannot resolve `hwilib` by name at all; the parent passes the package roots as argv, and the child prints the manifest files it found and validated as `name path recorded-digest` triplets — not a list of every file it walked, which the whole-tree comparison then judges. The whole name set is compared in both directions, the CT-91 cache re-reads all of it, and `_require_unchanged()` reads every file the child reported a second time immediately before the spawn, so a deterministic swap written between the check and the exec is refused instead of inheriting a verdict about bytes that no longer exist. Every prepared build environment runs `scripts/check-hwi-payload.py` against the real hash-locked install before any signing material enters the job. Evidence: `tests/test_hardening_pins.py::HwiIdentityPins::test_the_ci_payload_check_runs_the_app_check_and_fails_closed`, `::test_the_check_child_cannot_run_a_pth_hook_planted_in_site_packages`, `::test_a_swapped_sibling_module_does_not_inherit_a_cached_verdict`, `::test_a_payload_swapped_between_the_check_and_the_spawn_is_refused`; `tests/test_workflow_config.py::test_each_prepared_build_environment_proves_its_hwilib_matches_the_pin`. Break-and-watch used a **genuine** `hwi==3.2.0` install: the previous source accepted a `commands.py` with one injected line (and an added `zz_extra.py`) while reporting two files verified; the current source refuses it. |
| CT-73 + CT-102 | Med + Info | The sweep's decision procedure | `scripts/check-publish-paths.sh` now strips comments before **any** decision and decides the token grant from a parsed `permissions:` mapping: a spaced key (`contents : write`), a quoted flow mapping, a duplicate key, `write-all`, and a bare nested `write` are all read as the grants they are, while a comment naming a write grant is no longer an offender. The read-only proof comes from the mapping, never from body text. The rule is **fail-closed**: a `permissions:` construct the parser cannot read — a YAML alias (`permissions: *w`), a merge key (`<<: *w`), a quoted key (`"contents": write`), a nested mapping, a value outside the recognized vocabulary — is reported as `unreadable-token-permissions` and refused, rather than silently read as no grant. That repaired the three spellings a pre-audit adversarial pass demonstrated walking past the first version; the rounds after it each defeated the reader again on a new shape, so it is a bounded decision procedure, not a closed class. Command continuations are joined before the publisher vocabulary runs, so a `gh \` split across a line break is read as `gh release`. The publisher vocabulary gained `gh api graphql`, `$GITHUB_API_URL`, `${{ github.api_url }}`, `actions/github-script`, camelCase REST release calls, and — in place of only callees whose path names a release — **any `uses:` into another repository**, because a remote workflow's text cannot be read from this checkout whichever name it carries; a first-party action (`actions/checkout@v4`), a local `./.github/workflows/…` callee and an action vendored under a path (`github/codeql-action/init@v3`) are not offenders — the rule keys on the GitHub-documented callee shape `{owner}/{repo}/.github/workflows/{file}@{ref}`, because a first revision keyed on "two or more slashes before an `@`" wrongly refused the subdirectory action and would have blocked a legitimate dispatch. Shell spellings of one command are normalized before matching (`gh  release`, `gh "release"`, `gh 'rel'"ease"`). Evidence: `PublishPathSweepTests`, to which the cycle-5 round added sixteen cases (the class held 18 at `bd0c0e8`, 28 at `fea859c`, 34 at `1ff0175`, 44 at `f79203c`, 53 at `c6df346` (the wave-3 tree), 63 at the cycle-9 tree and 66 in the cycle-10 round, 104 on the round-14 tree, 118 on the round-19 tree, 121 on the round-20 tree, and 131 on this revision) — its tests include `test_the_sweep_refuses_a_permission_it_cannot_read`, a `subTest` over the alias, the merge key and the quoted key, `test_the_sweep_refuses_a_publisher_split_across_a_continuation`, `test_the_sweep_normalizes_shell_spellings_of_one_command`, `test_the_sweep_refuses_a_remote_reusable_workflow_under_any_name`, `test_the_sweep_does_not_mistake_an_action_or_a_local_callee`, `test_the_sweep_does_not_mistake_a_subdirectory_action_for_a_callee` and `test_the_sweep_refuses_the_rest_api_through_the_api_url_context`. Seven breaks of the original matchers were watched; each reddens the test named for it (an independent referee measured eight of the ten tests then present red against the previous script), and two of them also redden an older test that covers the same code path — removing the reusable-workflow call turns four red, including the pre-existing `test_the_sweep_refuses_a_reusable_release_workflow`, and loosening the `./*`/remote-callee boundary turns three red, including `test_a_uses_line_that_only_mentions_release_is_not_a_callee` — so "each reddens exactly its own named test" overstated it. The fail-closed arm was separately watched red, and the live `origin` sweep is still clean. **Scope, stated in the same open:** the sweep fetches branches only (`+refs/heads/*`), so a tag-only publish path is outside its reach; a tag's control is CT-97's environment scope, and the default-token residual is recorded under `## Documented residuals`. The sweep stays bash + git: `PublishPathSweepTests` deliberately does not gate it on PyYAML. **The third adversarial round.** An independent referee defeated the version above, and a second attacker then defeated the first rewrite, by hiding a grant or a callee inside YAML *presentation*: `permissions: {contents: !!str write}`, `{contents: &a write}`, `{contents: !<tag:yaml.org,2002:str> write}`, `{issues: read, contents: !!str write}`, `{issues: read, contents: &a write}`, an inline job "permissions": {issues: read, "contents" : write}` (and the top-level form), `{issues: read, "contents" : "write"}`, `'contents' : 'write'`, and the callee spellings `uses: &a o/r/.github/workflows/w.yml@main`, `uses: !!str o/r/…` and `uses: !<tag:yaml.org,2002:str> o/r/…` — every one printed the ok line while PyYAML resolves it to a real grant or a real callee. The rewrite makes the sweep a parser, not a word list, and a construct it cannot classify is **refused — never silently read as read-only** (`scripts/check-publish-paths.sh:60-132`). A flow `permissions:` mapping is taken apart member by member and each value has its YAML presentation — tags (`!!str`), anchors (`&a`), quotes, the space before the colon — stripped before the decision (`normalize_flow_value()` `scripts/check-publish-paths.sh:644`, `decide_flow_permissions()` `scripts/check-publish-paths.sh:699`); any value that does not resolve to `read`/`read-all`/`none`/`write`/`write-all` makes the mapping `unreadable-token-permissions`, and the old "some `key:` token ⇒ read-only" fallback is deleted. A `uses:` value starting with `&`, `*` or `!` is refused, with a leading tag or anchor stripped and the remainder re-tested as the callee (`calls_a_remote_reusable_workflow()` `scripts/check-publish-paths.sh:2321`). Both the permissions reader and the callee reader now require **key position**, and the value and block body of `run|with|if|env|name|shell|working-directory` are stripped (`strip_scalar_bodies()` `scripts/check-publish-paths.sh:1434`) before those two decisions only — the publisher vocabulary still reads literal bodies, so `gh release` inside `run: |` still refuses `runs-gh-release`. The same fix closed four over-refusals, which must stay `ok`: `- run: echo { permissions: write }`, `with: {note: 'permissions: write'}`, a `run: |` body holding a `permissions:`-shaped line, and a `uses:`-shaped value under `with:`/`if:`/`env:`. The nine flow spellings all refuse — seven as `grants-contents-write` and the two `!<tag:…>` URI spellings as `unreadable-token-permissions` — and the three callee spellings as `calls-a-release-workflow`. **Stated in the open:** this is a bash YAML reader that fails closed, so an unusual but honest workflow can also be refused. **The cycle-10 round** narrowed the job-id hole in the KEY-POSITION rule (round 19 later repaired the node-property blind spot recorded below): a job id may legally be spelled `env`, `run`, `with`, `if`, `name`, `shell` or `working-directory`, and `strip_scalar_bodies()` had deleted a line whose first key was one of those spellings plus every deeper line, so a job declared `jobs: env:` lost its whole body before the permissions and callee readers ran. The header doctrine gained the bullet `a job id is recognised by its POSITION under the workflow jobs: key, never by its spelling` (`scripts/check-publish-paths.sh:96-107`); `strip_scalar_bodies()` (`scripts/check-publish-paths.sh:1434`) now computes the `jobs:` line, its block end and the job-id indent once and prints a job declaration verbatim, with a flow job's continuation protected by `_strip_flow_close_line()` (`scripts/check-publish-paths.sh:780`) and a `jobs: {…}` flow mapping protected whole (`scripts/check-publish-paths.sh:1462-1466`). The publisher pipeline is untouched, so `gh release` inside `run: |` still refuses. **The cycle-11 and cycle-12 rounds** (the cycle-10 fix defeated and repaired, then the cycle-11 fix defeated and repaired) are recorded in full in the two sections below, with the referee's fixture names, the surviving mutations and the kept over-refusals. **The cycle-13 round (the identity arm).** The sweep now refuses any non-main branch that adds or modifies a path under `.github/workflows/` or `.github/actions/` relative to its merge base with `main` (`scripts/check-publish-paths.sh:2923-2961`) unless the branch, path and blob oid are named exactly in `.github/publish-sweep-allowlist.txt` read from the allowed ref (`scripts/check-publish-paths.sh:2582-2608`, `scripts/check-publish-paths.sh:2613`), never from the branch under test; deletions add no publish capability and are clean; the allowlist suppresses the identity arm's refusal for exactly the branch, path and blob it names, while the parser arm is independent of it and decides only the shapes it can read — a branch whose PyYAML resolves to `contents: write` printed the ok line whenever the parser lost the job body, which is why the round-19 reader repair below exists instead of a claim that the allowlist is harmless. The fail-closed reasons are `branch-changes-workflow-file` (`scripts/check-publish-paths.sh:2961-2962`), `unreadable-merge-base` (`scripts/check-publish-paths.sh:2925`), `unreadable-allowlist` (`scripts/check-publish-paths.sh:2955`) and `unreadable-branch-tree` (`scripts/check-publish-paths.sh:2965`), with a shallow clone (`scripts/check-publish-paths.sh:2657-2659`) and an unlistable allowed tree (`scripts/check-publish-paths.sh:2661-2663`) stated as global preconditions that name the remedy and end the run. The exact ok line is `ok: no non-main branch carries a publish-capable workflow differing from main's` (`scripts/check-publish-paths.sh:3020`). The tripwires are the 11 identity cases, the 5 tip-blob/fork cases and the 3 banner-class cases in `tests/test_workflow_config.py::PublishPathSweepTests` (`tests/test_workflow_config.py:4569`–`tests/test_workflow_config.py:4981`) plus `SweepFailClosedPins` (5 cases, `tests/test_workflow_config.py:5369`), each mutation-proven; named at least: `test_the_sweep_leaves_a_fork_of_main_carrying_the_publisher_clean` (`tests/test_workflow_config.py:4833`), `test_the_sweep_still_refuses_a_stale_inherited_publisher` (`tests/test_workflow_config.py:4846`), `test_the_sweep_leaves_a_stale_inherited_read_only_workflow_clean` (`tests/test_workflow_config.py:4865`), `test_the_sweep_leaves_a_change_equal_to_mains_tip_clean` (`tests/test_workflow_config.py:4885`), `test_the_sweep_refuses_a_change_that_matches_neither_baseline` (`tests/test_workflow_config.py:4903`) and `test_the_sweep_allowlist_cannot_smuggle_a_publish_path` (`tests/test_workflow_config.py:4708`). |
| CT-97 | Med | The watched credential name set | `scripts/check-release-credentials.sh` derives its watched names from the workflow text — every `secrets.NAME` reference, partitioned by the environment each referencing job declares — instead of a hand-typed list of five. The sixth name, `MAC_NOTARY_KEY_P8_BASE64`, is covered the day it appears. The rule is one-directional exactness plus non-vacuity: an extra name is refused, an environment holding none of its own names is refused, and a referenced-but-absent name is reported as a `note:` rather than a refusal, because the workflow reads the notary key only on the optional notarize path while every required credential is guarded by `: "${NAME:?}"`. `--print-scope` prints the derived table so the next reader can see what the check believes. The cycle-5 adversarial pass then found the derivation **attributable-only**: it built its watched set from the structured `jobs()` walk, so a release credential named in a workflow-level `env:` block, under a quoted job key, or under a `jobs:` block indented past the literal `jobs:` line was never read, and the check reported the environment scope clean while a repository-level credential of that name existed. `live_references()` now scans the whole comment-stripped file and anything it cannot attribute to a job is refused as `<file> names the release credential <NAME> somewhere this check cannot attribute to a job`, so an unreadable spelling fails closed instead of disappearing. Evidence: `tests/support.py::workflow_credential_scope`, `tests/test_release_credentials.py` (29 tests when this row was written, 36 at `f79203c`, 47 on this revision — see the cycle-6 section — including a workflow-level `env:`, a quoted job key, a four-space `jobs:` block, a bracket-spelled `secrets['NAME']`, a missing branch policy, a non-`main` branch policy and an unreadable policy endpoint), `ReleaseCredentialScopePins`, and each refusal arm broken and watched red. |
| CT-105 | Med | The Windows helper's trust model | The claim that a frozen build's sidecar "sits inside the signed bundle it authenticates" is true on macOS only. On Windows `hwi.exe` and `hwi.sha256` sit in the same user-writable directory and neither is signed, so the app's sidecar check there is a corruption check, not an identity check. That is now stated in `probe.py`, `scripts/build-sbom.py`, `HWI-DEPENDENCY.md` and a new `SIGNING.md` section, and pinned by `tests/test_hardening_pins.py::HwiIdentityPins::test_the_identity_docstring_does_not_claim_a_windows_signature`. Signing the Windows helper or moving the sidecar out of the writable directory was put to the owner as a business choice rather than an agent call; **the owner's decision, taken 2026-10-08, is to keep Windows unsigned (Option A)** — ship with the SmartScreen instructions, the GPG-signed `SHA256SUMS` and the Sigstore attestation that already exist — and to leave the sidecar beside `hwi.exe` with the identity limit stated in the open. A Windows code-signing certificate stays a future business option, not a gap this round leaves unfinished. |
| CT-92 | Low | Link, not only symlink, and check-then-load | `scripts/hwi_entry.py` decides from the directory entry (`os.lstat`) before opening anything, then opens with `O_NOFOLLOW` and requires `fstat` to report a regular file with `st_nlink == 1`, and compares a `(st_dev, st_ino, st_size, st_mtime_ns)` identity after the load and before usb1 receives the handle. A hard link has no distinct path to resolve, so `is_symlink()` alone never saw it; the `lstat` arm is also what refuses a FIFO without blocking on `os.open` and what makes the link refusal work on Windows, where `O_NOFOLLOW` is `0`. Evidence: `tests/test_hwi_entry.py` plants **real** `os.link`/`os.symlink` links instead of monkeypatching `Path.is_symlink`; removing the descriptor's `st_nlink == 1` condition reddens **both** hardlink tests (an earlier draft of this row said "the hardlink test" singular) while the symlink test stays green; removing the post-load identity comparison reddens `test_a_library_swapped_between_the_check_and_the_load_is_refused`; removing the `lstat` guard makes `test_the_libusb_preflight_refuses_a_fifo_without_blocking` hang until its five-second thread join fails. |
| CT-98 · CT-107 · CT-108 · CT-109 · CT-110 · CT-113 · CT-114 | Low–Info | Small pins and honest wording | `candidate_run_id` expressions are pinned out of **every** run block that consumes the input, not just the version job's guard (CT-98). The provisioning script's header no longer claims argv never carries a value; it names the two windows that do (`security export -P`, `notarytool store-credentials --password`) and pins them (CT-107). The broadcast identity clause has a test that actually drives the swap window (CT-108, `tests/test_send_flow.py::test_broadcast_refuses_when_the_prepared_payment_is_swapped_mid_flight`). `_clean_token` and `_device_class` have direct drop tests (CT-109). The three unquoted version interpolations are quoted and pinned (CT-110). `do_GET` records why it has no Origin check and a test pins that the token is the whole control there (CT-113). The BOM strip removes exactly one BOM instead of a character set (CT-114). |
| CT-100 · CT-106 · CT-111 · CT-115 · CT-116 | Info | Disclosure, not silence | `ToolchainDisclosurePins` asserts a literal expected probe-name set instead of iterating the table it is testing (CT-100). The release-environment comment says the gate protects the secret, not the environment, and a test refuses a job-level `if:` that would make the claim true by accident (CT-106). The explorer limitation is documented in `README.md` and `USER-MANUAL.md`: a self-consistent liar can drive preparation over phantom funds, preparation moves nothing, broadcast refuses a mismatched transaction ID rather than claiming success, and a mainnet lie must survive the signers' screens (CT-111). The two false statements in this ledger were corrected in place (CT-115, CT-116). |
| CT-112 | Info | The CI accept path | `scripts/check-hwi-payload.py` — the script the three build jobs run against the locked environment — reports success only through the app's own whole-tree check (`probe._hwi_package_roots()` plus `probe._verify_hwi_payload()`) and exits non-zero on an environment with no hwilib, on a moved tree, and on any `ProbeError`, so a build cannot pass the step vacuously. This row exists because the cycle-4 ledger closed CT-112 **by silence**, with no row and no residual, which is the one thing `RELEASE-PROCESS.md` §5 forbids. | `tests/test_hardening_pins.py::HwiIdentityPins::test_the_ci_payload_check_runs_the_app_check_and_fails_closed` |

**What this round does not claim.** No new payment capability; the money path still holds
and every change here can only refuse. The vendored-decoder residual (CT-89), the
explicit-helper operator choice (CT-93), the bridge-URL fallback (CT-95) and the
practice-network scan limits stand as documented. The two items that were put to the owner
as **business choices rather than agent calls** are settled as of 2026-10-08: Windows stays
unsigned (CT-105, Option A — the SmartScreen instructions, the GPG-signed `SHA256SUMS` and
the Sigstore attestation already exist), and the release pipeline stays **structurally
automated with no human approval step**, which is what the repository already enforces —
`scripts/check-release-credentials.sh` refuses a `required_reviewers` or `wait_timer`
protection rule on a signing environment
(`tests/test_release_credentials.py::test_a_required_reviewer_is_refused`,
`::test_a_wait_timer_is_refused`). Neither item asks the owner to click or sign anything by
hand.


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
with today's secrets, gated only by release-existence; the sweep never scans tags.* All 58
tags from `v0.1.0` on carry a dispatchable `build-candidate.yml` (the other 7 of the
repository's 65 tags predate `v0.1.0`), and the pre-0.6.4 ones lack the default-branch
guard, so dispatching one runs that tag's own frozen workflow text with whatever
credentials the repository holds **today**.

**Owner decision, 2026-10-07: option B — scope the credentials to protected environments.**
The owner directed the permanent form of the fix rather than a dated acceptance, on the
grounds that the project will cut many more releases.

Why a settings change is the permanent fix: the control is a rule about *which ref a run is
on*, not a list of tags. A repository secret is handed to a job on **any** ref; an
environment secret is handed only to a job that declares that environment *and* only when
the environment's deployment rule admits the ref. An old tag never declares the environment,
so it gets nothing even though its frozen workflow names the secret. A tag created in the
future carries a workflow that does declare it and is still refused, because the deployment
rule admits `main` only. Enumerating and cleaning every historical tag (58 from `v0.1.0` on,
of 65 in total) would have to be repeated forever; this does not.

Implemented in this revision:

- `.github/workflows/build-candidate.yml` declares `environment: apple-signing` on the
  `macos` job and `environment: release-signing` on the `checksums` job. The Apple steps run
  only under `if: ${{ inputs.notarize }}` and the GPG step only under
  `if: ${{ inputs.publish }}`. A `publish=false` run therefore skips the steps that read the
  secrets — but it still **enters** the environment, because `environment:` is a job key and
  neither job carries a job-level `if:` (CT-106). What denies a non-`main` ref is the
  environment's own `main`-only deployment rule, not the step gate.
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
published digest, desktop lock job and a genuine-install transcript), CT-105 (on Windows
`hwi.sha256` sits beside `hwi.exe` in the same user-writable directory and neither file is
signed, so there the sidecar proves the build is complete and uncorrupted, not that a local
writer did not replace both files together), CT-54/CT-59
(dated deferrals, hard expiry 2027-10-07).

Added by the cycle-5 adversarial pass, so none of these is mistaken for a closed item:

- **The publish-path sweep reads branches, not tags.** It fetches `+refs/heads/*` only. A tag
  whose frozen workflow text grants `contents: write` is outside its reach, and the audit's own
  `AGENTS.md` records that a tag's workflow text does run (`gh workflow run … --ref v9`). The
  sweep's scope line says so. The controls that remain for a tag are CT-97's environment scope
  (a tag run cannot deploy into `release-signing` or `apple-signing`, so it has no signing key —
  live repository state, verified against GitHub on 2026-10-08, not a fact the tree proves;
  `scripts/check-release-credentials.sh` re-verifies it and refuses a policy that admits a tag)
  and the fact that every historical tag carries the publisher text that shipped with it — a
  sweep that fetched tags would refuse this repository's own published v0.6.x tags, which is why
  tags are deliberately out of scope rather than overlooked.
- **A tag run keeps the default `GITHUB_TOKEN`.** Its `contents: write` comes from repository
  settings, not from a workflow file the sweep can read; the workflow's own `permissions:` block
  narrows it where declared. This is a repository-settings fact, not a code fact, and it is
  stated here rather than assumed away.
- **`ctypes.CDLL` runs a shared library's constructors at load.** The post-load identity
  comparison in `scripts/hwi_entry.py` discards a swapped handle before `usb1` receives it, so
  the library is never *used*, but a constructor in the swapped bytes has already run. Closing
  that would need the digest compared from an un-swappable source; not claimed here.
- **A `0x04`-prefixed 33-byte push was accepted until cycle 5's second round** and is now
  refused at parse. Signature verification refused it downstream in every build examined, so the
  window was fail-closed, but the parse gate is the layer that exists to catch it.

Added by the cycle-6 review, same rule — disclosed rather than claimed closed:

- **The helper's own site processing is gone on this revision; the residual is the reverse.** In
  the first cycle-6 round the helper itself ran `-I -P`, so a `.pth`/meta-path hook planted in
  site-packages was not blocked in the helper process; `-S` was used only in the payload check
  child, and that child cannot resolve `hwilib` by name at all, so it was never a substitute for
  the helper's own import. The second cycle-6 round spawns the source-mode helper under `-I -S -P`
  too, with a fixed `-c` bootstrap that appends the verified package roots after this
  interpreter's own entries (its `sysconfig` `purelib`/`platlib` among them), so no site hook runs
  and the pinned `hwilib` still imports. They are appended, not prepended, since the third audit
  round: a verified root's parent IS the site directory, so prepending let a planted
  `<site-packages>/ctypes.py` shadow a standard-library module inside the helper that had just
  passed the identity check. The cost is disclosed with the fix: a directory that reached the
  helper only through a `.pth` file (an editable install) no longer does. The frozen bundle path
  is unchanged — it still runs the bundled executable directly.
- **The publish sweep is a text matcher and does not follow shell-variable indirection.** It
  joins command continuations and normalizes shell spellings of the verb, but a publisher
  written `CMD=gh; $CMD release create …` names no token the matcher can see. No static reader
  of a workflow can resolve that; it is disclosed rather than claimed closed.
- **The sweep deletes every ref under `refs/remotes/publish-audit/*` before and after it runs.**
  That namespace is its own private audit area, but a caller whose repository already had a
  remote of that name would have those remote-tracking refs deleted. A known hygiene defect,
  disclosed rather than fixed here.

Added by the cycle-6 second round, same rule:

- **The publisher word list is a belt; the read-only-token requirement is the guarantee.** These
  spellings genuinely execute on the runner while naming no token a lexical scan can see: a YAML
  tab escape (`"gh\t release create v9"`), a command substitution (`$(which gh) release create
  v9`), a quoted variable (`Z=gh; "$Z" release create v9`), a backslash-escaped space
  (`gh release\ create v9`), and an `IFS` substitution (`gh${IFS}release${IFS}create v9`). None
  is fixed here. What holds is that a workflow which cannot show a read-only token is refused
  before any publisher word is considered; the word list is a second line, not the first.
- **A `jobs:` alias or merge key is over-refused; a flow `jobs:` map is now read.** `jobs: *j`
  leaves the jobs walk without a literal `jobs:` line, so every reference in the file is
  unattributed and the check refuses it rather than passing it — over-refusal in the safe
  direction. A flow-style `jobs: {…}` mapping was over-refused the same way until the third wave
  taught the walk to read a flow job's own read-only token (W3-4); a flow map it cannot resolve
  still fails closed.
- **The widened callee reader can read a `uses:` that is not a call.** The any-position `uses:`
  match added in R2-7 also fires on text inside a literal `|` run body, so that file is refused
  as `calls-a-release-workflow` rather than passed. Over-refusal in the safe direction.
- **The sweep reads branches, not tags, so a tag-only publish path is out of its scope.** It
  fetches `+refs/heads/*` with `--no-tags`; a released tag's tree legitimately contains the
  release workflow, and the tag-side control is not the absence of such a workflow from the text
  but the credential check's API walk, which enforces the branch policy on every environment that
  holds a watched credential (W3-7). The live repository has exactly three environments —
  `apple-signing` and `release-signing`, both main-only and holding the release/signing
  credentials, and `github-pages`, holding none — and no repository-level secrets, with the live
  check exiting 0.
- **The explicit-helper-path branch anchors only on a sidecar it reads beside the binary.**
  `_verify_hwi_bytes` (`probe.py:905`) compares an explicitly named helper against `hwi.sha256`
  in the same directory or in the bundle's `Resources`, so a local writer who replaces both files
  together is not detected there; on macOS that sidecar sits inside the codesign seal, on Windows
  it does not (CT-105). No independent anchor exists on this branch — a known limitation, not a
  fixed one.
- **A `.pyc` compiled into the pinned package after a warm verdict was executable** until the
  third wave made `_cached_identity_holds(path, payload=True)` re-run the whole payload walk, so a
  warm verdict re-establishes the whole-tree facts instead of re-hashing only the recorded pairs
  (`probe.py:433`, `probe.py:935`). Closed in this round. The child's freshness rule is now a by-value
  comparison of code objects (`fingerprint()`, `probe.py:722`, `probe.py:788`), not `marshal.dumps` bytes
  — a genuine `compileall`-written `.pyc` had been refused because `marshal` encodes
  string-interning state — and a `.pyc` whose body is not the recorded source is still refused.
- **`scripts/hwi_entry.py` is run with `runpy.run_path` and is in neither the manifest nor the
  spawn-time re-read.** Rewriting it needs write access to the app tree, which is the same access
  the pinned package itself needs; there is no independent anchor for the entry file on the
  source-mode path. A known limitation, not a fixed one.
- **Added by the cycle-6 third round: the pin covers `hwilib`'s own 115 `.py` files, not its
  dependencies.** `-S` removes site-packages from the helper, so the parent appends its own
  entries — site-packages among them — and a module beside the package still executes inside
  the helper: `hwilib/_serialize.py` imports `typing_extensions`, and with the frozen bootstrap
  that shim runs (`dependency shim ran: YES`). Closing it would mean pinning every dependency's
  bytes, and a writer to site-packages can replace the package itself before the check runs.
  Not fixed; disclosed, as the helper's own docstring at `probe.py:603-617` records.

## Verification on this revision

The audited revision is the round-23 commit on top of `f4ca17b2688f3024ba2a78a1c68dcb95ae642663`
(the round-22 commit); the rounds this revision sits on are 16, 17, 19, 20, 21, 22 and 23. Those artifacts are identified by content rather than by a commit sha, because the
commit that carries this ledger is not part of what the referees audited:

| Artifact | md5 | Lines |
| --- | --- | --- |
| `scripts/check-publish-paths.sh` | `caaffccc3fac47f90bf6e1125aa35f65` | 3226 |
| `tests/test_workflow_config.py` | `681797b88fd9306d5d7efe5b54918387` | 6240 |
| `tests/test_hardening_pins.py` | `fe88d3112fcb56351138e6ce65d45960` | 2110 |
| `probe.py` | `5d69c05e2d67f9ee2609359a14b07800` | 1498 |

- The full Python suite on the frozen tree: `Ran 777 tests in 360.053s` — **OK**, zero skips,
  zero failures (580 when the roll was first measured; the adversarial rounds since added the sweep,
  payload and credential classes — see the counts table in the cycle-6 section). Run it from the repository root, as `README.md`
  documents
  (`.venv/bin/python -m unittest discover -s tests -q`): one test spawns
  `python -c "import safe_http"`, which cannot resolve from inside `tests/` and fails
  there for that reason alone. A `ValueError: the WebView2 runtime is missing` line can appear in the
  log: it is the traceback a passing test prints through `desktop.report_startup_failure()`
  (`desktop.py:379`) on unbuffered stderr, so read the `Ran N tests` and `OK` lines rather than the
  last line of output.
- The UI DOM suites: all ten `tests/ui_*.cjs` files exit 0 under `node`.
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
  `/tmp/archive-check/bitcoin-easy-multisig-signer-v0.6.8`: `Ran 580 tests` — **OK** — the count on the tree the archive was cut from (`1a5e9bf`, the first fully green candidate run; this revision's own tree is re-measured in the counts table). On a
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
  `test_every_value_sent_to_github_arrives_on_stdin` red (re-run in cycle 6); any tool call before the
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
  tag`** (exit 0) as of 2026-10-08: the repository secret list is empty, and each
  environment holds the credential names its workflow references (the optional
  `MAC_NOTARY_KEY_P8_BASE64` is not stored, reported as a `note:`), allows only `main`,
  and declares no human gate.
- No wallet material, secret, or credential appears in this file or in the tests added
  by it; every fixture is synthetic.

## Verification of the cycle-5 remediation

- The full Python suite on this tree: `Ran 644 tests in 165.7s` — **OK**, zero failures, zero
  skips (580 at the cycle-4 roll; 42 are the WO-1…WO-8 pins and 22 more came from the cycle-5
  adversarial pass — the payload bytecode pins, the sweep spellings, the credential
  attribution, the helper swap/FIFO pins and the witness-script key-encoding pin).
- `bash -n` clean on every shell script in `scripts/`; every `.github/workflows/*.yml`
  parses under `yaml.safe_load`; all ten `tests/ui_*.cjs` suites exit 0 under `node`.
- `bash scripts/check-publish-paths.sh origin` against the live remote: exit 0,
  `ok: no non-main ref carries a publish-capable workflow` (the wording at the cycle-5 roll; the
  third wave has since narrowed it to `…non-main branch…`, because the sweep fetches heads only).
- `scripts/check-release-credentials.sh` against the live account (real `gh`, authenticated
  as the maintainer): exit 0, `ok: the release credentials are environment-scoped,
  main-only, and unreachable from any tag`, plus the expected `note:` for the unstored
  notary key. Since the third wave the check enumerates every API environment and enforces
  main-only, no human gate and no wait timer on any environment that holds a watched name, so
  that ok line rests on the environment branch policies read from the API, not on the absence of
  a tag-triggered workflow in the audited text.
- Break-and-watch, each on a disposable `git worktree` with the working files copied in,
  the named regression introduced, the named test watched red, the file restored
  byte-identical (`cmp`) and the control green again:
  - **CT-72** — the previous `probe.py`/`signing.py` on a detached `HEAD` worktree with the
    current test files: 4 tests red, 7 reports.
    `::test_the_same_key_respelled_under_another_version_is_still_refused` reports four times
    (the `subTest` version spellings),
    `::test_a_respelled_duplicate_is_refused_even_when_the_fingerprints_differ` reports once,
    `::test_a_compiled_script_with_a_duplicated_pubkey_is_refused` once, and
    `::test_a_duplicate_key_input_cannot_reach_complete_with_one_signature` once, with
    `"same public key more than once" does not match "Input 1 does not match its verified
    previous transaction."`. The other two probe tests stay **green** under that same break:
    the pre-existing fingerprint gate already refuses the same-origin duplicate and the old
    base58 gate still refuses the same-spelling duplicate, so neither is a tripwire for the
    key-material gate. (An earlier draft of this paragraph claimed all four probe tests
    failed. An independent referee falsified that during the pre-audit adversarial pass, and
    the record is corrected here rather than left as a claim the evidence does not support.)
  - **CT-73/CT-102** — seven breaks: comment stripping disabled, the spaced-key regex
    narrowed, the flow-mapping arm disabled, `github-script` removed, the camelCase REST
    names removed, the `$GITHUB_API_URL` arm dropped, and the reusable-workflow match
    narrowed. Against the previous sweep exactly eight of the ten new sweep tests are red;
    each break reddens the test named for it, and two of them also redden a pre-existing
    test that covers the same code path (removing the reusable-workflow call turns four red,
    loosening the `./*`/remote-callee boundary turns three).
  - **CT-90** — a genuine `hwi==3.2.0` install with one line injected into `commands.py`
    (and later an added `zz_extra.py`): the previous source reports `accepted: 2 files` and
    passes; the current source refuses with
    `The hardware-wallet tool does not match its recorded digest. Refusing to run it.`
    Removing `-S` turns four named tests red
    (`::test_a_substituted_hwilib_payload_is_refused`,
    `::test_the_check_child_runs_without_site_support`,
    `::test_the_check_child_does_not_start_a_site_hook`,
    `::test_the_check_child_cannot_run_a_pth_hook_planted_in_site_packages`). Removing the
    generated child's whole-tree comparison **alone leaves every pin green**: measured on a
    disposable copy as `Ran 72 tests … OK` (`tests/test_hardening_pins.py` holds 72 tests on
    this revision). An added file is refused first by the loadable-suffix rule in the same
    child, and a removed or substituted manifest file is caught by the per-file digest loop
    and by the parent's own completeness loop, so the set comparison is defence in depth
    rather than the layer any named test drives — it is still what catches a manifest file
    absent from one package root when another root supplies it. No break-and-watch is claimed
    for it; the referee's phrase "turns named tests red" overstated it and this line replaces
    it. Dropping the spawn-time re-read
    (`_require_unchanged`) turns
    `::test_a_payload_swapped_between_the_check_and_the_spawn_is_refused` red with
    `AssertionError: ProbeError not raised`, and nothing else.
  - **CT-97** — the extra-name, empty-environment, stray-gate and repository-level-copy breaks
    each redden their named test. The missing-policy and wrong-policy cases did **not**:
    against the previous script all three of those cases drove one shared branch-policy guard,
    so an independent referee measured two breaks that turned nothing red — the cycle-4 line
    "seven breaks … each red" was stronger than the evidence. This round added
    `test_a_missing_branch_policy_is_refused`,
    `test_a_non_main_branch_policy_is_refused` and
    `test_an_unreadable_policy_endpoint_is_refused`; re-run in cycle 6, neutering that guard
    reddens **three** tests — the two new policy tests and the pre-existing
    `test_a_tag_that_could_deploy_into_an_environment_is_refused`, which shares the same
    guard, so those three are not independent of one another. The derivation's unattributed
    class found by the adversarial pass is pinned by `test_a_workflow_level_env_is_refused`,
    `test_a_quoted_job_key_is_read_as_its_own_job` and
    `test_a_four_space_indented_job_is_read`; all three read the one whole-file `Counter`
    net in `scripts/check-release-credentials.sh`, so deleting that net reddens all three
    together.
  - **CT-92** — the previous `is_symlink()` guard: **both** hardlink tests are red
    (`::test_frozen_helper_refuses_a_hardlinked_bundled_library` and
    `::test_the_libusb_preflight_refuses_a_hardlinked_library`, `RuntimeError not raised`)
    and the frozen preflight accepts a hardlinked library; removing the `st_nlink` arm
    reproduces exactly those two reds while the symlink test stays green (not skipped). The
    fixtures plant real `os.link`/`os.symlink` links and never patch `Path.is_symlink`.
  - **CT-105** — the old "inside the signed bundle" sentence restored in `probe.py`, the
    SBOM sentence replaced, and the `SIGNING.md` heading renamed: three separate reds.
  - **CT-108** — the broadcast identity clause replaced with `if False:` in `_broadcast`
    only: the new send-flow test fails with
    `Expected 'broadcast_transaction' to not have been called. Called 1 times.`
- **Independent adversarial review of commit `1ff0175`** (performed in a read-only worktree by
  reviewers forbidden from modifying this repository): referees re-ran the tripwire claims
  above, an attacker tried to defeat the new gates, and an auditor checked every absolute
  claim in
  these documents against the code. They falsified three claims — CT-72's "four probe tests",
  CT-90's child-tree-gate breadth, and CT-97's "seven breaks, each red" — and the record above
  carries the corrections rather than the original claims. The attacker found five defects the
  cycle-5 audit had not filed; each is fixed and pinned:
  - **The payload pin covered only `.py` files.** A planted
    `hwilib/__pycache__/_cli.cpython-312.pyc`, its header mtime and size matching the unmodified
    source and its body attacker bytecode, passed both the payload check and the spawn-time
    re-read, and importing it ran the attacker's code. `_hwi_payload_check_script()` now
    refuses every non-manifest file whose suffix is loadable and accepts bytecode only when it
    recompiles to the recorded source under this interpreter's magic number (a stale header
    whose mtime and size no longer match is inert, so it is tolerated).
  - **The credential derivation read only what its `jobs()` walk could attribute** — a
    workflow-level `env:` naming a release secret was invisible and the check reported the
    scope clean while a repository-level credential of that name existed. See the CT-97 row.
  - **The sweep missed four spellings**: a REST release call through `${{ github.api_url }}`
    with the job's own token, a whitespace run (`gh  release`), shell quoting
    (`gh "release"`), and any reusable workflow whose path did not contain the word "release".
    All four now refuse (`talks-to-the-rest-api`, `runs-gh-release`,
    `calls-a-release-workflow`), with `actions/checkout@v4` and a local callee still accepted.
  - **`scripts/hwi_entry.py` had a check-then-load window** — the verified descriptor was
    closed before `ctypes.CDLL()` re-resolved the path, so a file swapped in between loaded
    attacker bytes — and a FIFO planted at the bundled name made the preflight block forever
    in `os.open`. Both are closed (see the CT-92 rows).
  - **`signing.py::parse_multisig_script` accepted a 33-byte push with a `0x04` prefix**,
    which changed the bytes for the same point and so walked past the byte-for-byte duplicate
    gate; it failed closed later, but not at the gate that exists to catch it.
- No wallet material, secret or credential appears in the tests added by this round; every
  fixture is synthetic, and the one genuine hwilib tree used for the CT-90 demonstration
  lived in `/tmp`, never in this repository.


## Cycle-6 remediation: the class holes a second adversarial review opened

Cycle 6 answers an independent adversarial review of commit `1ff0175`, performed in a read-only
worktree by reviewers forbidden from modifying this repository. It did not re-run the cycle-5
demonstrations; it attacked the *classes* those demonstrations were taken to close, and it found
holes the first round had not filed. Every change below is on the working tree and each is held
by a test demonstrated able to fail.

A second, independent re-audit — again in fresh worktrees, forbidden from modifying the
repository and given none of the first round's reasoning — then attacked commit `f79203c`,
which is cycle 6's own answer to the first review. It filed eight bypasses; all eight are fixed
in the rows below, the round reports each guard broken on a disposable copy, its own test watched
red, and the file restored before the next was touched. Attacking the first of those fixes then
found five more flow-style spellings of a write token, and the two reader gates were widened to
read them (R2-2, R2-3). A separate pass closed a `.pth` hole in the helper spawn (R2-15). The R2-
rows are those fixes; they are one row per reader hole, not a one-to-one restatement of the
reviewers' eight filings.

A third wave closed the holes the next attack left, in three lanes landing together: a genuine
`compileall`-written `.pyc` was refused while a `.pyc` added after a warm verdict executed
(W3-1, W3-2); a local `./` action the sweep could not read could publish, and the ok/refusal text
overclaimed the sweep's scope (W3-3, W3-6); two flow spellings were over-refused (W3-4, W3-5);
and the credential check never queried an API environment it had not seen named (W3-7, W3-8). The
W3- rows are those fixes.

| # | Finding | What was wrong | Fix on this revision | Evidence |
| --- | --- | --- | --- | --- |
| E1a | The `permissions:` key had to be unquoted | `"permissions": write-all` on a job was read as no grant, so a publishing job passed as read-only | `permissions_verdict()` matches the key with `local pat_perm='^([[:space:]]*)[^[:alnum:]_]*permissions[^[:alnum:]_]*[[:space:]]*:(.*)$'` (`scripts/check-publish-paths.sh:1743`) and reports `grants-write-all` (`scripts/check-publish-paths.sh:2757`). The pattern is held in a variable because `/bin/bash` 3.2.57 rejects an inline `["\']?` class inside `[[ =~ ]]`, and `bash -n` does not catch it | `PublishPathSweepTests::test_the_sweep_refuses_a_quoted_permission_key` |
| E1b | The publisher vocabulary was incomplete | `gh --repo owner/repo release create v1` and `gh -R owner/repo release create v1` named no token; the REST release calls were matched only in camelCase | `scripts/check-publish-paths.sh:2829-2831` refuses both `gh --repo … release` and `gh -R … release` as `runs-gh-release`; the loop at `scripts/check-publish-paths.sh:2863-2865` adds `create_release`, `update_release` and `upload_release_asset` to `calls-the-rest-release-api` | `test_the_sweep_refuses_a_publisher_written_with_the_repo_flag` |
| E2 | A `uses:` the reader could not resolve fell through | `uses: *w` (alias/merge) and a folded `uses: >-` callee were read as no callee | `calls_a_remote_reusable_workflow()` refuses an alias/merge value and strips a leading `>`/`\|` indicator (plus an optional `-`/`+`) before taking the value, because YAML folding joins a folded scalar onto its indicator line | `test_the_sweep_refuses_a_uses_the_reader_cannot_resolve`, `test_the_sweep_refuses_a_folded_uses_callee` |
| E4/E3 | The credential check read only page 1 | On a repository with more than one page of secrets a release credential could sit on page 2 unseen | `scripts/check-release-credentials.sh` passes `--paginate` at `scripts/check-release-credentials.sh:529` (repository secrets), `scripts/check-release-credentials.sh:567` (branch policies) and `scripts/check-release-credentials.sh:574` (environment secrets); each of the three readers drains back-to-back documents with `json.JSONDecoder().raw_decode` (`scripts/check-release-credentials.sh:385`/`scripts/check-release-credentials.sh:425`/`scripts/check-release-credentials.sh:455`) | `test_the_repository_read_asks_for_every_page`, `test_a_repository_secret_on_a_later_page_is_refused` |
| CT-97b | A quoted job key was not a job | `  "leak":` merged its body into the previous job, so a credential it declared looked scoped when it was not | `JOB` (`scripts/check-release-credentials.sh:126`) accepts an optionally quoted job name | `test_a_quoted_job_key_is_read_as_its_own_job` (replacing cycle-5's case for a quoted job key) |
| CT-97c | The whole-file net compared names, not occurrences | A workflow-level `env:` repeating a name already seen inside a scoped job was reported as attributed | `live = Counter(live_references(text))` (`scripts/check-release-credentials.sh:330`) compares occurrences | `test_a_workflow_level_env_cannot_hide_behind_a_scoped_job`, `test_a_workflow_level_env_is_refused`, the over-refusing four-space-indent case (since replaced by `test_a_four_space_indented_job_is_read`; see R2-10) — one net, three reds |
| CT-97d | Derived names and hostile answers | `secrets[format('{0}','NAME')]` was not derived; a list-shaped answer from a reader raised `AttributeError`; `name: Don't build # see ${{ secrets.X }}` was read as a reference | `format(...)` derives to `NAME`; a non-dict answer is a refusal with a reason; `strip_comment()` treats a quote as opening a scalar only where a token can begin | the cycle-5 bracket-expression case (since replaced by `test_a_bracket_expression_secret_is_refused_as_unreadable`; see R2-14), `test_a_list_shaped_secret_answer_is_a_refusal_with_a_reason`, `test_a_list_shaped_environment_answer_is_a_refusal_with_a_reason`, `test_an_apostrophe_does_not_turn_a_comment_into_a_reference` |
| B-A | The payload walk could step past a symlinked directory | `pathlib.rglob('*')` does not descend a symlinked directory, so a symlinked `__pycache__` was never opened | `_hwi_payload_check_script()` walks with `os.scandir` and `follow_symlinks=False` and refuses anything that is neither a regular file nor a directory | `test_a_symlinked_bytecode_directory_is_refused` (its attack body is real code, `MARKER = 'attacker'`, not a comment) |
| B-C | Only the last package root was re-read | The check child printed only the last root's files, so `_require_unchanged` re-read only that root | Every root's files are printed and every `(path, digest)` pair returned, so an earlier root is re-read too | `test_every_root_is_reverified_before_the_spawn` |
| E6 | `co_filename` was part of the bytecode identity | A genuine tree compiled by `pip install --target` from a staging directory was refused | The rule unmarshals (never executes) and compares `marshal.dumps(scrub(code))`, where `scrub` blanks `co_filename` recursively | `test_bytecode_compiled_at_another_path_is_accepted`, `test_a_bytecode_file_with_a_wrong_magic_is_refused`; the cycle-5 nonzero-flags case was replaced by W4-3's `test_an_unknown_bytecode_invalidation_flag_is_refused` when the third round stopped refusing legitimate hash flags |
| — | The remote-callee rule over-refused | Cycle-5's matcher refused any `uses:` with two or more slashes before an `@`, which also refused ordinary subdirectory actions and container references | The rule is narrowed to the callee shapes GitHub documents — `*/.github/workflows/*` and a two-or-more-slash path ending `.yml`/`.yaml`, minus the local `./` form — so `github/codeql-action/analyze@v3` and `docker://ghcr.io/o/i@sha256:d` pass **by design** | `tests/test_workflow_config.py:1951` (`test_the_sweep_does_not_mistake_a_subdirectory_action_for_a_callee`); the comment at `scripts/check-publish-paths.sh:2297-2303` |
| R2-1 | A flow `permissions:` mapping split across lines | `permissions: {issues: read,` with `contents: write}` on the next line was folded as a mapping that never closed; the first scope read read-only and `contents: write` vanished | `permissions_verdict()` refuses a `{`-valued token with no `}` — `decide_flow_permissions()` reports `unrecognized` (`scripts/check-publish-paths.sh:699-744`) — and the branch reports `unreadable-token-permissions` (`scripts/check-publish-paths.sh:2777`) | `PublishPathSweepTests::test_the_sweep_refuses_a_flow_permission_mapping_split_across_lines` |
| R2-2 | A flow-style job put its token mid-line | `publish: {runs-on: …, permissions: {contents: write}, …}` kept the key off line start, so the anchored pattern saw no grant while a separate job's `contents: read` covered the file | After the anchored miss, an opening brace at line start or after space/comma arms a mid-line read (`scripts/check-publish-paths.sh:1920-1921`); `contents: write` reports `grants-contents-write` (`scripts/check-publish-paths.sh:2753`) | `::test_the_sweep_refuses_a_flow_style_job_that_grants_write` |
| R2-3 | Five more flow spellings of a write token | Attacking the fix above found a quoted job key, a flow mapping on the line after the key, a tagged `!!map {…}`, an escaped key (`"permiss\u0069ons"`), and the explicit-key `? permissions` / `: write-all` form each carrying a grant | The widened gate refuses the first three as `grants-contents-write` and the two key spellings it cannot resolve as `unreadable-token-permissions` (`scripts/check-publish-paths.sh:1920-1921`) | `::test_the_sweep_refuses_every_flow_spelling_of_a_write_token` |
| R2-4 | The widened flow gate could over-refuse prose | A `run:` string echoing `"{permissions: write}"`, or the repository's own build step holding a `b"\x7fELF"` literal, sits on a brace-bearing line and could be read as a token | The gate keys on an opening brace where a flow mapping can begin, and the escaped-key rule keys on the quote being in a key position (`scripts/check-publish-paths.sh:1771`, `scripts/check-publish-paths.sh:1920-1921`); both files are accepted | `::test_prose_that_names_a_permission_is_not_a_grant` (the over-refusal control) |
| R2-5 | A deeper `permissions:` covered a job that declared none | The coverage proof counted any deeper `permissions:` line — e.g. a variable `permissions: read` under `env:` — as the job's own token, so a file with an undeclared job read read-only | `_jobs_all_declare_permissions()` counts only a `permissions:` at the job's direct-child indent (`scripts/check-publish-paths.sh:2167`); an undeclared job leaves the file `partial` → `partial-token-permissions` (`scripts/check-publish-paths.sh:2786`) | `::test_a_deeper_permissions_key_does_not_cover_a_job` |
| R2-6 | A block-indicator `uses:` hid its callee | `uses: \|`, `uses: \|2-` and `uses: >2-` put the callee on the next line; the indicator was read as the value, so the call passed | The indicator strip removes the whole run of signs and digits (`scripts/check-publish-paths.sh:2413-2415`) and an empty value is a refusal (`scripts/check-publish-paths.sh:2425`), so the callee is refused as `calls-a-release-workflow` | `::test_the_sweep_refuses_a_block_scalar_uses_that_hides_its_callee` |
| R2-7 | A `uses:` the reader could not place | `call: {uses: …}`, `call: {"uses": …}`, `steps: [{uses: …}]` and the explicit-key `? uses` / `: …` form kept the key off line start, so a remote callee passed | `pat_uses` matches `uses:` anywhere a key can begin (`scripts/check-publish-paths.sh:2329`) and `pat_explicit_uses` refuses the split key (`scripts/check-publish-paths.sh:2334`); a local `./` callee and a subdirectory action still pass (`scripts/check-publish-paths.sh:2459-2463`, `scripts/check-publish-paths.sh:2473`) | `::test_the_sweep_refuses_a_callee_inside_a_flow_mapping` |
| R2-8 | A `#` inside a word ended the line | `echo x#${{ secrets.NAME }}` is live in the shell GitHub runs, and stripping from any `#` hid the reference from the walk | `strip_comment()` treats `#` as a comment only at line start or after whitespace (`scripts/check-release-credentials.sh:142-149`) | `tests/test_release_credentials.py::test_a_hash_inside_a_word_does_not_hide_a_reference` |
| R2-9 | A job key with whitespace before its colon was not a job | `  leak :` merged into the previous job's body, so its environment and its credential were attributed to the wrong job | `JOB` accepts whitespace around the colon (`scripts/check-release-credentials.sh:126`) | `::test_a_whitespace_before_a_job_colon_is_read` |
| R2-10 | The job indent was hard-coded to two spaces | A four-space file was read as no jobs, so every live reference in it was unattributed and an honest file was refused | `jobs()` measures the job indent as the smallest indent in the `jobs:` block (`scripts/check-release-credentials.sh:157-197`) | `::test_a_four_space_indented_job_is_read` (REPLACED the over-refusing four-space-indent case) |
| R2-11 | A YAML anchor made a job or an environment unreadable | `build: &b` and `environment: &env release-signing` kept the anchor text as the name, so the job or environment did not resolve | `JOB` allows a trailing anchor (`scripts/check-release-credentials.sh:126`) and `environment()` strips a leading anchor (`scripts/check-release-credentials.sh:251`) | `::test_a_yaml_anchor_does_not_hide_a_job_or_an_environment` |
| R2-12 | A lowercase or single-bracket spelling escaped the watched name | `secrets.gpg_private_key` resolves the same API name (`GPG_PRIVATE_KEY`) but was compared literally, and a single quoted bracket name was not derived | `references()` uppercases every derived name (`scripts/check-release-credentials.sh:265`); a whole-literal bracket index is still a name (`scripts/check-release-credentials.sh:284-288`) | `::test_a_lowercase_secret_reference_is_matched_to_its_name`, `::test_a_single_literal_bracket_secret_is_still_derived` |
| R2-13 | A reference split across lines was read as neither half | `secrets` newline `.NAME` / `["NAME"]` is one reference; the per-line walk saw neither half | `live_references()` strips comments per line, then joins the text before matching (`scripts/check-release-credentials.sh:296-306`) | `::test_a_reference_split_across_lines_is_still_live` |
| R2-14 | An expression bracket index or an escaped dot form was read as a harmless name | `secrets[format('{0}_KEY','GPG_PRIVATE')]` was derived as the harmless `GPG_PRIVATE`, and `secrets.GP\u0047_PRIVATE_KEY` stopped at `GP`, so the real name was watched by nobody | `references()` returns `?unreadable` for a non-literal bracket index or an escaped/interpolated dot form (`scripts/check-release-credentials.sh:265`), and the caller refuses it (`scripts/check-release-credentials.sh:511`) | `::test_a_bracket_expression_secret_is_refused_as_unreadable` (which replaced the cycle-5 case that derived a bracket-expression secret) |
| R2-15 | A `.pth` in site-packages could redirect the helper after the pin passed | The source-mode helper ran `-I -P`, which does not stop `site`, so a `.pth` could insert a tree ahead of the pinned one while the identity check still said PASS | The helper now runs `-I -S -P` under a fixed `-c` bootstrap that appends the verified package roots (`probe.py:593`, `sys.path.extend` at `probe.py:597`) after the interpreter's own entries, including its `purelib`/`platlib` (`probe.py:603`, `probe.py:631`, `probe.py:650`; flags at `probe.py:542`, `probe.py:548`) | `HwiIdentityPins::test_a_pth_in_site_packages_cannot_redirect_the_helper` (`tests/test_hardening_pins.py:1265`), `::test_the_helper_search_path_never_precedes_the_interpreter` (`tests/test_hardening_pins.py:1324`), `::test_a_search_directory_module_cannot_shadow_the_stdlib` (`tests/test_hardening_pins.py:1363`). An earlier draft of this row said the bootstrap inserted the roots first; the third audit round showed that ordering was itself the bug: the root's parent is site-packages, so the inserted directory led the standard library inside the helper |
| W3-1 | A genuine `compileall` `.pyc` was refused | The child compared `marshal.dumps(scrub(code))`; `marshal` encodes string-interning/`FLAG_REF` state, so a real `pip`/`compileall`-written `__pycache__/client.cpython-312.pyc` compared unequal and the pinned tree was refused | The child's freshness test compares code objects by value through a recursive `fingerprint()` (`probe.py:722`), ending `return fingerprint(recorded) == fingerprint(code)` (`probe.py:788`); `co_filename` is normalised away and the format covers every code field plus `co_consts` recursively (code objects, tuples and frozensets recursed, everything else by value AND by type — see W3-9). A `.pyc` whose body is not the recorded source is still refused, proved in the same test | `HwiIdentityPins::test_a_genuine_compileall_bytecode_file_is_accepted` (`tests/test_hardening_pins.py:855`), `::test_a_missing_package_is_refused_as_not_installed` (`tests/test_hardening_pins.py:1012`) |
| W3-2 | A `.pyc` added after a warm verdict executed | `_cached_identity_holds` re-hashed only the recorded `(path, digest)` pairs, so a new compiled file inside the pinned package inherited a standing PASS | `_cached_identity_holds(path, payload=False)` re-runs the whole payload walk when `payload` is true, and `_verify_hwi_identity` (`probe.py:935`) passes it for the source-mode case (`probe.py:433`) | `::test_a_bytecode_file_added_after_a_warm_verdict_is_refused` (`tests/test_hardening_pins.py:1088`), `::test_a_module_added_after_a_warm_verdict_is_not_believed` (`tests/test_hardening_pins.py:1154`) |
| W3-3 | A local action the sweep could not read could publish | A `./`-prefixed target was passed without reading it, so an unread local action could carry a publisher | `calls_a_remote_reusable_workflow()` passes a local `./` target only when it is `.github/workflows/*.yml\|*.yaml` (after stripping `@ref` and flow punctuation); any other local target fails closed with the new reason `calls-a-local-action`, reported through the caller (`scripts/check-publish-paths.sh:2321`, `scripts/check-publish-paths.sh:2443-2462`, `scripts/check-publish-paths.sh:2462`) | `test_the_sweep_refuses_a_local_action_it_does_not_read` (`tests/test_workflow_config.py:1973`) |
| W3-4 | A flow `jobs:` map was over-refused | A flow-style `jobs: {…}` mapping that declared its own read-only token was read as no jobs and refused | `_flow_members` (`scripts/check-publish-paths.sh:1983`), `_flow_key_value` (`scripts/check-publish-paths.sh:2040`), `_flow_job_declares_permissions` (`scripts/check-publish-paths.sh:2079`), `_flow_jobs_mapping_covers` (`scripts/check-publish-paths.sh:2098`) and `_collect_flow` (`scripts/check-publish-paths.sh:2118`) read it; `_jobs_all_declare_permissions` (`scripts/check-publish-paths.sh:2167`, delegating `scripts/check-publish-paths.sh:2204`, per-job `scripts/check-publish-paths.sh:2241`) keeps the cycle-6 depth guard, so a `permissions:` nested under `env:`/`strategy:` still does not cover a job | `test_the_sweep_accepts_a_read_only_token_in_a_flow_style_job` (`tests/test_workflow_config.py:1683`) |
| W3-5 | `with: {x-permissions: …}` was over-refused | The mid-line flow pattern matched `x-permissions` as a grant | `pat_perm` keeps the key in key position — `^([[:space:]]*)[^[:alnum:]_]*permissions[^[:alnum:]_]*[[:space:]]*:(.*)$` (`scripts/check-publish-paths.sh:1743`), capture group 2 — so the `x-permissions` spelling is not a grant | subTest in `test_prose_that_names_a_permission_is_not_a_grant` (`tests/test_workflow_config.py:1778`) |
| W3-6 | The ok/refusal text overclaimed the sweep's scope | It said "non-main ref" while the sweep fetches heads only (`git fetch --no-tags … +refs/heads/*`, `scripts/check-publish-paths.sh:2508`), and the header did not say tags are out of scope by design | The header scope comment (`scripts/check-publish-paths.sh:4-18`), the refusal banner (`scripts/check-publish-paths.sh:2998-3015`) and the ok line (`scripts/check-publish-paths.sh:3020`) name a non-main **branch** (the sweep fetches heads only) and state that tags are out of scope by design, with tag-triggered credential use controlled by the environment branch policy; the ok line was tightened once more in the cycle-13 identity round, because a fork of `main` carries `main`'s own publish-capable file — the exact current string is quoted in the CT-73 + CT-102 row | the ok-line assertions across `tests/test_workflow_config.py` (`tests/test_workflow_config.py:1276`, `tests/test_workflow_config.py:2059`, `tests/test_workflow_config.py:2079`, `tests/test_workflow_config.py:2311`, `tests/test_workflow_config.py:2345`, `tests/test_workflow_config.py:2710`, `tests/test_workflow_config.py:2758`, `tests/test_workflow_config.py:2787`, `tests/test_workflow_config.py:2995`, `tests/test_workflow_config.py:3818`, `tests/test_workflow_config.py:3892`, `tests/test_workflow_config.py:3944`, `tests/test_workflow_config.py:4115`, `tests/test_workflow_config.py:4300`, `tests/test_workflow_config.py:4843`, `tests/test_workflow_config.py:5115`, `tests/test_workflow_config.py:5216`) |
| W3-7 | An environment holding a watched credential but never named was never queried | The check audited only environments the workflow text named, so an undeclared `*` environment with an empty branch policy could deploy from a tag | A new section 3 (`scripts/check-release-credentials.sh:599`, API walk `scripts/check-release-credentials.sh:609`) pages `repos/$REPO/environments` and enforces main-only, no human gate and no wait timer on any environment that holds a watched name, named or not; one holding none (e.g. `github-pages`) is skipped before its policy is read, with its secrets still listed. `names_from` decode mode (`scripts/check-release-credentials.sh:399`), `encoded_env()` (`scripts/check-release-credentials.sh:409`), whitespace-safe declared stream (`scripts/check-release-credentials.sh:556-558`) requesting percent-encoded names (`*` → `%2A`). Refusal wording: "the <env> environment is not named by any workflow in $WORKFLOWS_DIR and holds the watched credential name(s) [<names>], but it <does not allow deployments from the main branch alone (found: none)>[ and declares a human gate (wait_timer(5))]; a tag dispatch could still name it, so it is refused rather than left unaudited" | `tests/test_release_credentials.py:421` (`test_an_undeclared_environment_holding_a_credential_is_refused`), `tests/test_release_credentials.py:450` (`test_an_undeclared_environment_holding_no_credential_is_ignored`, the `github-pages` control, must stay exit 0), `tests/test_release_credentials.py:471` (`test_an_undeclared_environment_with_a_human_gate_is_refused`) |
| W3-8 | `environment: {name: x}` was mis-parsed | A flow mapping was read as its raw text, so the environment name did not resolve | `flow_name()` (`scripts/check-release-credentials.sh:199`), called from `environment()` (`scripts/check-release-credentials.sh:252`), reads `{name: x}` and `{name: x, url: …}`; a mapping with no name key falls back to its raw text as one environment, so no phantom names | `tests/test_release_credentials.py:870` (`test_a_flow_mapping_environment_is_read_as_its_name`), `tests/test_release_credentials.py:914` (`test_an_unnameable_flow_mapping_stays_one_environment`) |

| W3-9 | A hand-built `.pyc` retyped a constant and passed the fingerprint | `code.replace(co_consts=…)` rebuilds a code object with `co_code` and the line table untouched while swapping `1` for `1.0` (or `True`); `1.0 == True == 1`, so a by-value comparison accepted a pyc that is not the compiled source. Found by a self-attack on W3-1 before the commit | `fingerprint()` now reduces every non-code constant to `(type(item).__name__, item)`, so a constant is compared by value AND type (`probe.py:748`); the genuine `compileall` tree still passes (W3-1) and a different value is still refused | `HwiIdentityPins::test_a_bytecode_file_with_a_retyped_constant_is_refused` (`tests/test_hardening_pins.py:920`) |
| W4-1 | The verified helper could be made to run a substituted standard-library module | The bootstrap prepended the verified roots; each root's parent is site-packages, and `scripts/hwi_entry.py:3` imports `ctypes`, so a planted `<site-packages>/ctypes.py` ran first inside the helper while the identity check still reported PASS | `_HWI_HELPER_BOOTSTRAP` appends (`sys.path.extend`, `probe.py:593-600`) | `HwiIdentityPins::test_the_helper_search_path_never_precedes_the_interpreter` (`tests/test_hardening_pins.py:1324`), `::test_a_search_directory_module_cannot_shadow_the_stdlib` (`tests/test_hardening_pins.py:1363`) — reproduced end-to-end against a real `hwi==3.2.0` install: the fixed bootstrap prints `IDENTITY CHECK: ACCEPTED` and `marker written: False`; the old prepending bootstrap prints the same verdict with `marker written: True`. Break-and-watch: restoring `sys.path[:0]` reddens both (`AssertionError: True is not false : a file in the search directory shadowed a standard-library module inside the verified helper`; `'sys.path.extend(' not found`) |
| W4-2 | `0.0` and `-0.0` compared equal in the bytecode pin | `fingerprint()` returned `(type(item).__name__, item)`, so a `.pyc` whose constant was `-0.0` where the source has `0.0` was accepted and the interpreter imported it | `fingerprint()` compares `float`/`complex` by `repr` (`probe.py:746`) | `::test_a_bytecode_file_with_a_signed_zero_is_refused` (`tests/test_hardening_pins.py:968`) — break-and-watch: removing the arm reddens it (`AssertionError: ProbeError not raised`). Latent for the shipped tree: none of the 115 pinned sources contains a float or complex zero constant |
| W4-3 | A legitimate hash-based (PEP 552) `.pyc` tree was refused | The child refused any pyc whose header flags were nonzero, which is every `compileall --invalidation-mode checked-hash`/`unchecked-hash` tree | the child reads the flag: `0` keeps the mtime/size stale shortcut, `1` and `3` are accepted only when the body equals the compiled source, anything else is refused (`probe.py:761-772`) | `::test_a_hash_flagged_bytecode_file_is_accepted_when_its_code_matches` (`tests/test_hardening_pins.py:698`), `::test_a_hash_flagged_bytecode_file_with_a_foreign_body_is_refused` (`tests/test_hardening_pins.py:727`), `::test_an_unknown_bytecode_invalidation_flag_is_refused` (`tests/test_hardening_pins.py:747`) — break-and-watch: refusing flags 1/3 again reddens the first, letting a hash pyc take the stale shortcut reddens the second |

The `—` row above the second-round rows corrects a claim about this rule: the refusal of `docker://…@sha256:…` and
`github/codeql-action/analyze@v3` was true of commit `1ff0175` and is false of the working tree.
That finding was measured against `1ff0175`, not this revision; the narrowing is deliberate and
pinned, not an oversight.

Cycle 6 added nine cases to `PublishPathSweepTests`, eight to `tests/test_release_credentials.py`
(and replaced one), and five to `HwiIdentityPins`. The cycle-6 sweep tests are
`test_the_sweep_refuses_a_quoted_permission_key`,
`test_the_sweep_refuses_a_publisher_written_with_the_repo_flag`,
`test_the_sweep_refuses_a_uses_the_reader_cannot_resolve`,
`test_the_sweep_refuses_a_folded_uses_callee`,
`test_the_sweep_refuses_a_publisher_folded_across_yaml_lines`,
`test_the_sweep_does_not_mistake_a_subdirectory_action_for_a_callee`,
`test_the_sweep_does_not_fold_a_literal_block`,
`test_the_sweep_refuses_a_read_only_token_on_only_some_jobs` and
`test_the_sweep_accepts_a_read_only_token_declared_on_every_job`.

The second round added seven cases to `PublishPathSweepTests`, eight to
`tests/test_release_credentials.py` (two of them replacing older cases), and two to
`HwiIdentityPins`. Its sweep tests are
`test_the_sweep_refuses_a_flow_permission_mapping_split_across_lines`,
`test_the_sweep_refuses_a_flow_style_job_that_grants_write`,
`test_the_sweep_refuses_every_flow_spelling_of_a_write_token`,
`test_the_sweep_refuses_a_block_scalar_uses_that_hides_its_callee`,
`test_the_sweep_refuses_a_callee_inside_a_flow_mapping`,
`test_a_deeper_permissions_key_does_not_cover_a_job` and
`test_prose_that_names_a_permission_is_not_a_grant` (the over-refusal control). Its credential
tests are `test_a_hash_inside_a_word_does_not_hide_a_reference`,
`test_a_whitespace_before_a_job_colon_is_read`, `test_a_four_space_indented_job_is_read`
(replacing the over-refusing four-space-indent case),
`test_a_yaml_anchor_does_not_hide_a_job_or_an_environment`,
`test_a_lowercase_secret_reference_is_matched_to_its_name`,
`test_a_single_literal_bracket_secret_is_still_derived`,
`test_a_reference_split_across_lines_is_still_live` and
`test_a_bracket_expression_secret_is_refused_as_unreadable` (replacing the
cycle-5 case that derived it). Its `HwiIdentityPins` tests are
`test_a_pth_in_site_packages_cannot_redirect_the_helper` and
`test_the_helper_search_path_never_precedes_the_interpreter`.

The third wave added two sweep cases —
`test_the_sweep_accepts_a_read_only_token_in_a_flow_style_job` and
`test_the_sweep_refuses_a_local_action_it_does_not_read` — and folded the `x-permissions` case
into `test_prose_that_names_a_permission_is_not_a_grant`; five credential cases —
`test_an_undeclared_environment_holding_a_credential_is_refused`,
`test_an_undeclared_environment_holding_no_credential_is_ignored`,
`test_an_undeclared_environment_with_a_human_gate_is_refused`,
`test_a_flow_mapping_environment_is_read_as_its_name` and
`test_an_unnameable_flow_mapping_stays_one_environment` — with no existing credential case
rewritten; and five `HwiIdentityPins` cases —
`test_a_genuine_compileall_bytecode_file_is_accepted`,
`test_a_missing_package_is_refused_as_not_installed`,
`test_a_bytecode_file_added_after_a_warm_verdict_is_refused`,
`test_a_module_added_after_a_warm_verdict_is_not_believed` and
`test_a_bytecode_file_with_a_retyped_constant_is_refused` — with
`test_the_helper_search_path_never_precedes_the_interpreter` and
`test_a_file_removed_from_the_package_is_refused` hardened.

### Verification of the cycle-6 remediation

Re-measured on the frozen tree from the repository root with
`python -m unittest discover -s tests` (Python 3.12.14) — the same command `README.md` documents as
`.venv/bin/python -m unittest discover -s tests`. The counts below were measured on the revision named above, after the round-16, round-17, round-19, round-20, round-21, round-22 and round-23 patches.

| Suite | Tests on this revision | Earlier |
| --- | --- | --- |
| `tests/test_workflow_config.py::PublishPathSweepTests` | 131 | 127 on the round-22 tree, 121 on the round-20 tree, 118 on the round-19 tree, 104 on the round-14 tree, 94 on the round-10 tree, 66 in the cycle-10 round, 63 at cycle 9, 53 at `c6df346` (wave 3), 51 at wave 2, 44 at `f79203c`, 34 at `1ff0175`, 28 at `fea859c`, 18 at `bd0c0e8` |
| `tests/test_workflow_config.py::SweepFailClosedPins` | 5 | 4 on the cycle-10 tree |
| `tests/test_workflow_config.py` (whole file) | 190 | 186 on the round-22 tree, 180 on the round-20 tree, 177 on the round-19 tree, 163 on the round-14 tree, 152 on the round-10 tree, 129 at the cycle-11 tree |
| `tests/test_release_credentials.py` | 47 | 42 at wave 2, 36 at `f79203c`, 29 at `1ff0175` |
| `tests/test_release_credentials.py::ReleaseCredentialCheckTests` | 41 | — |
| `tests/test_hardening_pins.py::HwiIdentityPins` | 60 | 59 on the round-14 tree, 55 at wave 3, 50 at wave 2, 48 at `f79203c`, 43 at `1ff0175` |
| `tests/test_hardening_pins.py` (whole file) | 84 | 83 on the round-14 tree, 79 at wave 3, 74 at wave 2 |
| full suite | `Ran 777 tests in 360.053s` — **OK** | `Ran 773 tests in 335.106s` on the round-22 tree; `Ran 767 tests in 331.443s` on the round-20 tree; `Ran 764 tests in 308.429s` on the round-19 tree; `Ran 749 tests in 277.295s` on the round-14 tree; `Ran 738 tests in 261.085s` on the round-10 tree; `Ran 710 tests` on the frozen cycle-10 tree; `Ran 707 tests` on the cycle-9 tree; `Ran 693 tests in 184.818s` on the third-wave tree; `Ran 681 tests` on the wave-2 tree; `Ran 666 tests` at `f79203c`; `Ran 644 tests in 165.7s` in the cycle-5 record |

Every row's `measured at` is this pass on the frozen tree with the audit interpreter
(Python 3.12.14), run from the repository root: `PublishPathSweepTests` `Ran 131 tests` — **OK**,
`tests/test_release_credentials.py` `Ran 47 tests` — **OK** (of which
`ReleaseCredentialCheckTests` `Ran 41 tests`), `HwiIdentityPins` `Ran 60 tests` — **OK**,
`tests/test_hardening_pins.py` `Ran 84 tests` — **OK**. The credential file went 42 → 47 across the
third wave with no existing case rewritten; its second-round two replacements
(the over-refusing four-space-indent case → `test_a_four_space_indented_job_is_read` and
the bracket-expression case →
`test_a_bracket_expression_secret_is_refused_as_unreadable`) stand. The sweep class went 53 → 63 in
the cycle-9 round, 63 → 66 in the cycle-10 round, and 66 → 94 across the cycle-11, cycle-12 and
cycle-13 rounds (five rewrite cases, four more, then eleven identity, five tip-blob and three
banner-class cases), and 94 → 104 across the round-12 and round-14 rounds (four inherited-action
cases and a symlinked-allowlist case, then five `permissions`-key node-property cases and the
column-zero pin), and 104 → 113 across the round-16 and round-17 rounds (the three parser classes
referee E filed plus the continuation, split-key and allowlist-field cases), 113 → 118 in round 19
and 118 → 121 in round 20 (the node-property and explicit-key cases), 121 → 127 across rounds 21
and 22 (the pinned continuation-indent cases), and 127 → 131 in round 23 (the sequence-entry
block-scalar cases); `HwiIdentityPins` went
55 → 60, and the hardening file 79 → 84.
`SweepFailClosedPins` gained its shallow-clone case in round 12, so it holds 5 cases.

On the same frozen tree, `bash -n` is clean on every shell script, every
`.github/workflows/*.yml` parses under `yaml.safe_load`, and all ten `tests/ui_*.cjs` scripts
exit 0 under `node` (each asserts with `node:assert/strict` and signals pass by exit code —
only some print a trailing `…: ok` line, so the exit code is the evidence, not a stdout match).
Both live checks were re-run after the last wave-3 fix landed and each exits 0:
`bash scripts/check-publish-paths.sh origin` prints its ok line (the exact current text is quoted once, in the CT-73 + CT-102 row), and
`bash scripts/check-release-credentials.sh` prints the `apple-signing` /
`MAC_NOTARY_KEY_P8_BASE64` note and
`ok: the release credentials are environment-scoped, main-only, and unreachable from any tag`.
The repository has exactly three environments (`apple-signing` and `release-signing`, main-only
and holding the release and signing credentials; `github-pages`, holding none) and no
repository-level secrets.

Every cycle-6 change above was broken and watched red when it was made; four of them were
re-broken here, on a disposable copy of the tree, and the red recorded (the file was restored
byte-identical afterwards):

- The provisioning script's `set_secret()` was changed from `gh secret set … < "$3"` to
  `--body "$(cat "$3")"`: `Ran 2 tests … FAILED (failures=2)`, both stdin tests
  (`test_every_value_sent_to_github_arrives_on_stdin` and
  `test_the_owner_path_carries_the_value_on_stdin_only`), the second quoting the value out of
  `argv`.
- The branch-policy guard in `scripts/check-release-credentials.sh` was neutered: three reds —
  `test_a_missing_branch_policy_is_refused`, `test_a_non_main_branch_policy_is_refused` and the
  pre-existing `test_a_tag_that_could_deploy_into_an_environment_is_refused`.
- The whole-file unattributed net was deleted: three reds, all on the shared `Counter` arm.
- The reusable-workflow call guard was replaced with `if false`: eight failures across four test
  methods, including the pre-existing `test_the_sweep_refuses_a_reusable_release_workflow`.
- **Not** watched red: deleting the generated child's `set(found) != set(manifest)` comparison
  leaves every pin green (`Ran 72 tests … OK`). A file added to the package is refused first by
  the loadable-suffix rule in the same child, and a removed or substituted one by the per-file
  digest loop and the parent's completeness loop, so that comparison is defence in depth and no
  break-and-watch is claimed for it.

The second and third rounds report the same discipline for their own fixes: each guard was broken
on a disposable copy and its named test watched red before the file was restored. Those transcripts
are not reproduced here; the tests are named in the R2- and W3- rows, and the suite run above is
what this pass measured on the frozen tree.

What remains open after this round is unchanged from `## Documented residuals`, with one
substitution: the sweep reads branches only, a tag run keeps the default token, `ctypes.CDLL`
constructors run at load, shell-variable indirection is not followed, and a pre-existing
`refs/publish-audit/*` would be clobbered (the sweep's own namespace; it no longer touches
`refs/remotes/publish-audit/*`, which a real remote named `publish-audit` owns). The helper no longer keeps site-packages: both
children run `-I -S -P`, and the residual is now on the other side — a path that reached the
helper only through a `.pth` file (an editable install) no longer does.

### Verification of the third adversarial round (W4)

The third audit round re-attacked the helper spawn and the bytecode reader. Each break below
was applied on a disposable copy, its named test watched red, and `probe.py` restored
byte-identical (`cmp` confirmed):

- **Prepend the verified roots again** (`sys.path[:0] = …` in `_HWI_HELPER_BOOTSTRAP`):
  `test_the_helper_search_path_never_precedes_the_interpreter` and
  `test_a_search_directory_module_cannot_shadow_the_stdlib` fail (`AssertionError: True is not
  false : a file in the search directory shadowed a standard-library module inside the verified
  helper`; `'sys.path.extend(' not found`).
- **Drop the `float`/`complex` `repr` arm** in `fingerprint()`:
  `test_a_bytecode_file_with_a_signed_zero_is_refused` fails (`AssertionError: ProbeError not
  raised`).
- **Refuse PEP 552 hash flags again** (flags `1` and `3`):
  `test_a_hash_flagged_bytecode_file_is_accepted_when_its_code_matches` fails.
- **Let a hash-flagged `.pyc` take the mtime/size stale shortcut**:
  `test_a_hash_flagged_bytecode_file_with_a_foreign_body_is_refused` fails.
- **Admit an unknown invalidation flag** (fall through for a flag outside `0`, `1`, `3`):
  `test_an_unknown_bytecode_invalidation_flag_is_refused` fails.

The reproduction is end-to-end, not a unit pin: against a real `hwi==3.2.0` install the frozen
bootstrap prints `IDENTITY CHECK: ACCEPTED` and `marker written: False`, while the previous
prepending bootstrap prints the same verdict with `marker written: True`.

Measured on the frozen probe side from the repository root with the audit interpreter
(Python 3.12.14): `HwiIdentityPins` `Ran 60 tests` — **OK** and `tests/test_hardening_pins.py`
`Ran 84 tests` — **OK**. The counts table above now carries these alongside the sweep lane
(`PublishPathSweepTests` `Ran 131 tests` — **OK**) and the full suite (`Ran 777 tests` — **OK**).

### Verification of the third adversarial round (sweep)

The cycle-9 sweep round replaced the lexical word list with the doctrine recorded in the
CT-73 + CT-102 row. Four new `PublishPathSweepTests` cases pin it; each break below was applied on
a disposable copy, the named test watched red, and `scripts/check-publish-paths.sh` restored
byte-identical (`cmp` confirmed):

- **Drop the tag/anchor/quote normalization** in `normalize_flow_value()`:
  `test_the_sweep_refuses_a_write_grant_hidden_by_a_tag_anchor_or_quote` fails (4 of its cases).
- **Disable the leading-token guard** on a `uses:` value:
  `test_the_sweep_refuses_a_callee_hidden_behind_a_tag_or_anchor` fails (3 cases).
- **Drop the scalar-body strip from the callee pipeline**:
  `test_the_sweep_reads_uses_only_in_key_position` fails (4 cases).
- **Drop the scalar-body strip from the permissions pipeline**:
  `test_the_sweep_does_not_read_key_shaped_text_in_a_scalar_value` fails (5 cases); **add it to the
  publisher pipeline** and the same test's positive half fails (1 case), because `gh release`
  inside `run: |` must still be an offender.

The live `origin` sweep is still clean (exit 0, its ok line), and the live credential check still prints the `apple-signing` optional-notary `note:`
before its ok line.

**Stated in the open:** this is a bash YAML reader that fails closed, so an unusual but honest
workflow can also be refused. The whole-file `!<tag:yaml.org,2002:str>` flow spellings report
`unreadable-token-permissions` rather than a grant because the tag URI carries the comma and colon
the flow splitter uses; a nested mapping value (`{contents: {write: true}}`) is refused
`unreadable-token-permissions`; and where a file carries no top-level `permissions:` the callee
refusal `calls-a-release-workflow` is reported before `no-read-only-token-permissions` because the
callee check runs first — still a refusal.

### Verification of the cycle-10 adversarial round (job ids)

The cycle-10 sweep round narrowed the job-id hole in the KEY-POSITION rule (round 19 later repaired the node-property blind spot recorded below). A GitHub job id may legally
be spelled `env`, `run`, `with`, `if`, `name`, `shell` or `working-directory`, and
`strip_scalar_bodies()` deleted any line whose first key was one of those spellings plus every
deeper line. A workflow whose job was declared `jobs: env:` therefore had its whole body removed
before the permissions reader (`perm_text`) and the callee reader (`callee_text`) ran, so a grant
or a remote callee inside that job read as nothing. An independent referee's fixtures
`jobid_{env,run,with,if,name,shell,working-directory}.yml` printed
the bare ok line (exit 0) while PyYAML resolved
`jobs.env.permissions` to `{'contents': 'write'}`; a 210-case differential fuzz found 98
ok-while-YAML-says-write cases, every one this class. The same hole hid
`jobs.env.uses: other-org/…/publish-package.yml@main` and a step-level remote `uses:` inside a job
named `env`.

The fix is positional and fail-closed: `strip_scalar_bodies()`
(`scripts/check-publish-paths.sh:1434`) computes the workflow `jobs:` line, its block end (the first
later non-blank line at indent ≤ the `jobs:` indent) and the job-id indent (the least indent
between them) once, and prints a non-blank line at that indent verbatim; a flow job's continuation
is protected by the new `_strip_flow_close_line()` (`scripts/check-publish-paths.sh:780`) and a `jobs: {…}` flow mapping protects
its whole region (`scripts/check-publish-paths.sh:1462-1466`). Workflow-level `env:`, a job-level `env:` at indent 4 and step-level
`run:`/`with:` are still stripped, and the publisher pipeline still reads literal bodies, so
`gh release` in `run: |` still refuses. The header doctrine gained the bullet "a job id is
recognised by its POSITION under the workflow `jobs:` key, never by its spelling"
(`scripts/check-publish-paths.sh:96-107`).

Three new `PublishPathSweepTests` cases pin it:

- `test_the_sweep_finds_a_write_grant_in_a_job_named_for_a_scalar_key`
  (`tests/test_workflow_config.py:3976`) — seven ids × {block `permissions: {contents: write}`,
  one-line flow job}, plus a two-job hidden case and a `write-all` job named `name`.
- `test_the_sweep_finds_a_remote_callee_in_a_job_named_for_a_scalar_key` (`tests/test_workflow_config.py:4040`) — a job-level
  and a step-level remote `uses:` inside a job named `env`.
- `test_a_job_named_for_a_scalar_key_keeps_the_scalar_controls_honest` (`tests/test_workflow_config.py:4066`) — honest controls
  in jobs named `env`/`run`/`if` stay `ok`, and `gh release` in a `run: |` body is still an
  offender.

**Mutation evidence.** Disabling the job-id exemption (the position test `-ge 0` → `-ge 999999`)
reds `test_the_sweep_finds_a_write_grant_in_a_job_named_for_a_scalar_key` (15 cases) and
`test_the_sweep_finds_a_remote_callee_in_a_job_named_for_a_scalar_key` (one case). The
honest-controls test is the non-regression control and stays green; the five cycle-9 mutations
still red their named tests. Every break was applied on a disposable copy and the restored
`scripts/check-publish-paths.sh` compared byte-identical (`cmp`).

### Verification of the cycle-11 sweep rewrite (the cycle-10 fix defeated and repaired)

The cycle-10 positional fix above was itself attacked by an independent round-6 referee and defeated
three ways, plus one over-refusal regression; a 734-workflow differential fuzz reported `DEFECTS=279`
(209 + 49 + 21) and 10 over-refusals. Each defeat printed the ok line while PyYAML resolved a real
grant or a real remote callee:

- **M7 — the escaped quote (21 cases).** `_strip_flow_close_line` had no backslash-escape handling, so
  `\"` closed a double-quoted flow scalar early and the `}}` that followed was read as flow depth zero;
  the continuation line was then stripped before the permissions reader ran. Fixtures
  `M7_flow_jobs_escaped_quote_grant.yml`, `M7_flow_jobs_escaped_quote_callee.yml`.
- **M1 — the `jobs:` decoy inside a block scalar (209 cases).** The locator broke on the first
  `jobs:`-shaped line, so a decoy inside a `name: |` body won, the job-id indent stayed `-1`, and the
  scalar-key rule deleted the real job id with its body. Fixtures `M1_decoy_block_env_grant.yml`,
  `M1_decoy_callee.yml`, `M1_decoy_flow_writeall.yml`.
- **M2 — the quoted `"jobs":` key (49 cases).** A quoted key did not match the locator's regex, so the
  file's real `jobs:` was never located. Fixture `M2_quoted_jobs_key_grant.yml`.
- **O1 — the over-refusal regression it introduced.** An exempted job-declaration line was printed
  verbatim, so a quoted `"permissions: write"` note inside it was read as a grant
  (`grants-write-all`, `scripts/check-publish-paths.sh:2757`) where the previous revision printed ok.
  Fixture `O1_flow_note_on_jobdecl.yml`.
- **Three mutations survived all 66 tests then present** — MT3 (`_strip_flow_close_line` always
  returning its start offset), MT4b (dropping `shell` from the scalar-key list) and MT6 (the block-end
  comparison `-le` → `-lt`) — so the multi-line-flow grant, the `shell`-body control and the block-end
  bound had no coverage.

The cycle-11 repair is positional and fail-closed. The header doctrine now states the rule outright
(`scripts/check-publish-paths.sh:60-132`): a construct the parser cannot classify is refused. A job id
is recognised by its POSITION under the one unambiguous top-level `jobs:` key (`_jobs_key_kind()`
`scripts/check-publish-paths.sh:835`, `_locate_jobs_key()` `scripts/check-publish-paths.sh:1275`); block-scalar bodies are skipped while locating it
(`strip_scalar_bodies()` `scripts/check-publish-paths.sh:1434`), quoted spellings are stripped, and a `\`-escaped spelling or two
candidates is unreadable. When the locator cannot find a `jobs:` key it emits the sentinel
`permissions: *sweep-cannot-locate-the-jobs-key` and hands both readers the UNSTRIPPED text, so a real
grant is still reported as a grant and a job-less or ambiguous file refuses rather than reading as
read-only. `_strip_flow_close_line()` (`scripts/check-publish-paths.sh:780`) now skips the character after a backslash inside a
double-quoted scalar and returns a sentinel on an unbalanced flow, and `_flow_find_permissions()`
(`scripts/check-publish-paths.sh:1564`) finds an inline `permissions` only in KEY position, so a quoted scalar in value position is
data while a quoted key or value is still read.

Five new `PublishPathSweepTests` cases pin the repair, each red under its own mutation:
`test_the_sweep_ignores_a_decoy_jobs_line_inside_a_block_scalar`
(`tests/test_workflow_config.py:4144`), `test_the_sweep_reads_a_quoted_top_level_jobs_key` (`tests/test_workflow_config.py:4199`),
`test_the_sweep_walks_a_flow_jobs_mapping_with_an_escaped_quote` (`tests/test_workflow_config.py:4245`),
`test_the_sweep_does_not_read_a_quoted_scalar_as_a_permissions_key` (`tests/test_workflow_config.py:4282`) and
`test_the_sweep_scopes_a_scalar_body_and_the_jobs_block` (`tests/test_workflow_config.py:4313`). The three previously surviving
mutations now redden named tests, the referee's fuzzer re-run gives `DEFECTS=0 OVER-REFUSALS=0`, and
the 28-case job-id corpus, the 25-fixture audit-I corpus (byte-identical) and ten further fixtures all
pass.

**Behaviour change this round, documented not hidden:** a workflow file with no `jobs:` key, or an
empty `jobs:` value, is now refused `unreadable-token-permissions` (`scripts/check-publish-paths.sh:2777`) where the previous revision
printed ok. Both are invalid GitHub workflow syntax that can publish nothing, so the refusal is the
fail-closed doctrine. **Residuals carried forward:** a flow member whose URI tag contains the flow
splitter's comma or colon reports `unreadable-token-permissions` rather than a named grant (fail-closed);
`permissions: {contents: {write: true}}` (a nested mapping) is unreadable; a job id written as a
sequence item is not exempt (invalid GitHub syntax).

### Verification of the cycle-12 sweep rewrite (the cycle-11 fix defeated and repaired)

The round-8 referee defeated the cycle-11 repair twice.

1. **Defeat: `uses:` escapes.** A single-document workflow with
   `uses: "other-org/ci\x2f.github\x2fworkflows\x2fpublish-package.yml@main"` is a real remote
   reusable-workflow call after YAML decoding, but the sweep printed the ok line. Cause:
   `normalize_command_text()` (`scripts/check-publish-paths.sh:497`) stripped quote characters without
   decoding YAML escape sequences, and the callee test required two literal slashes. Variants:
   `\u002f`, a tagged `!!str "…"`, a job-level `uses:`. Control: `\/` was refused.
2. **Defeat: multiple documents.** A file whose first document is a one-line flow root with
   `jobs.build.permissions: {id-token: write}` and whose second document supplies a column-0 `jobs: {}`
   and a top-level `permissions: read-all` slipped through, because the second document cleared the
   fail-closed sentinel and only its read-only token was matched. All six fuzz defects the referee
   found were this family.

The repair, all in `scripts/check-publish-paths.sh`:

- quoted-scalar state is carried across lines (`_qs_line_open_quote()` `scripts/check-publish-paths.sh:949`, used by `_ambiguously_placed_jobs_key()` `scripts/check-publish-paths.sh:1005` and the locator `scripts/check-publish-paths.sh:1275`, with the
  branch-loop guard at `scripts/check-publish-paths.sh:2745`), so a `jobs:`-shaped line inside a multi-line quoted scalar cannot become the locator's
  candidate; an ambiguous placement refuses (`unreadable-token-permissions` `scripts/check-publish-paths.sh:2777`);
- the jobs-key reader strips a leading anchor or tag before comparing to `jobs` (`_jobs_key_kind()`
  `scripts/check-publish-paths.sh:835`), so `&j jobs:` and `!!str jobs:` are the key, not a decoy;
- more than one document refuses (`has_multiple_documents()` `scripts/check-publish-paths.sh:966`, called `scripts/check-publish-paths.sh:2736`) and is reported
  `unreadable-multiple-documents` (`scripts/check-publish-paths.sh:2737`) — GitHub runs one workflow per file, so a second document is
  unclassifiable;
- YAML double-quoted escapes (`\xHH`, `\uHHHH`, `\UHHHHHHHH`, `\/`, `\\`, `\"`, `\ ` and the short
  escapes) are decoded (the addendum comment is at `scripts/check-publish-paths.sh:459-471`) before any callee or publisher decision;
  an escape that cannot be decoded refuses `unreadable-escape-sequence` (`scripts/check-publish-paths.sh:2814`);
- a quoted `"permissions"` key is read like the bare key (the KEY-position rule at
  `_flow_find_permissions()` `scripts/check-publish-paths.sh:1564`, `pat_perm` `scripts/check-publish-paths.sh:1743`). This removed the real over-refusal the
  referee flagged: a job-level `"permissions": read-all` with no top-level token reported
  `partial-token-permissions` (`scripts/check-publish-paths.sh:2786`) while the bare spelling was clean.

Four new `PublishPathSweepTests` cases pin it: `test_the_sweep_skips_a_jobs_decoy_inside_a_quoted_scalar`
(`tests/test_workflow_config.py:4354`), `test_the_sweep_decodes_yaml_escapes_in_a_double_quoted_value`
(`tests/test_workflow_config.py:4428`), `test_the_sweep_refuses_a_file_with_more_than_one_document` (`tests/test_workflow_config.py:4490`) and
`test_the_sweep_reads_a_quoted_permissions_key` (`tests/test_workflow_config.py:4520`).

**Kept over-refusals (deliberate, disclosed, unchanged):** `uses: ./.github/actions/x` is refused as
`calls-a-local-action` (`scripts/check-publish-paths.sh:2462`) and the string `gh release` anywhere in a
`run:` value refuses as `runs-gh-release` (`scripts/check-publish-paths.sh:2831`). These are the lexical belt's cost, not bugs.
**Residuals:** code points below 32 and 127 are folded to a space inside decoded escapes (defensive; no
fixture distinguishes it); two locator fixtures (`C2`/`C5`) refuse as unclassifiable rather than with a
named reason, because they differ from an honest control only in the job body; a URI tag containing the
flow splitter is unreadable (fail-closed).

### Verification of the cycle-13 identity arm (the decidable answer to the parser's limits)

**Why.** Six independent adversarial rounds each defeated the hand-rolled bash YAML-subset parser; the
R2-, W3-, cycle-9, cycle-10, cycle-11 and cycle-12 rows above are that sequence. Classification of an
arbitrary YAML subset cannot be made sound in bash 3.2, so the certification must not rest on it. The
parser stays as the second belt — a branch byte-identical to `main` still needs a verdict on `main`'s own
shared workflows — and a decidable arm decides the branch question by comparing bytes, not by parsing.

**The invariant.** For every enumerated non-main branch B, let M be the merge base of the allowed ref
(`main`) and B. Every path under `.github/workflows/` or `.github/actions/` that B adds or modifies
relative to M is refused `branch-changes-workflow-file` (`scripts/check-publish-paths.sh:2961-2962`) unless
the allowlist on the ALLOWED ref names exactly that branch, path and blob oid. Deletions are ignored — a
deletion adds no publish capability. The allowlist is read from the allowed ref only (`scripts/check-publish-paths.sh:2582-2608`),
never from the branch under test. Code: merge base `scripts/check-publish-paths.sh:2923`, per-path comparison `scripts/check-publish-paths.sh:2925-2961`.

**Why the merge base and not `main`'s tip.** A branch based on an older `main` commit inherits reviewed
`main` content; measuring against the current tip would refuse branches that changed nothing. Measured on
the live repository on 2026-10-08, before the cleanup below, every one of the 15 non-main branches then in
existence had zero added or modified workflow/action paths against its merge base
(`paths_compared=4 changed=0`; only four CI paths existed across those branches), so the arm passed with
an empty allowlist while a tip comparison would already have needed three waivers. On 2026-10-08 the
fourteen stale non-main branches were deleted from `origin`, which now carries `main` alone, so the live
branch claim is vacuous by construction; the sweep still audits any branch that exists later.

**The fork-from-main defect found while checking that.** The live ok was accidental: no non-main branch
carries `.github/workflows/build-candidate.yml`, whose `main` copy holds `id-token: write` and
`contents: write`. A branch forked from `main` DOES carry it, and the sweep refused it
(`feature-x .github/workflows/build-candidate.yml grants-writable-token-scope`) with the harmful advice
"Delete the file on the ref above" — so every fork of `main` failed the check. Repaired by keying both
belts on the allowed ref's tip blob (`git rev-parse -q --verify "$ALLOWED_REF:$path"`, `scripts/check-publish-paths.sh:2702`): the
parser SKIPS a path whose branch blob oid equals the allowed ref's blob for that path (`scripts/check-publish-paths.sh:2703-2705`), and
the identity arm calls a path the branch's own change only when its blob differs from BOTH the
merge-base blob AND the allowed tip blob AND is not exactly allowlisted (`scripts/check-publish-paths.sh:2947-2961`). Consequences: a
STALE inherited publish-capable file is refused on its own bytes (its blob differs from the tip); a
stale inherited READ-ONLY file is clean (the live shape); a branch that adopts `main`'s tip content is
clean; an allowlisted publish-capable change is refused only while the parser arm actually sees the
grant — that arm does not read the allowlist, but it decides only the shapes it understands, and round 19
repaired the reader after a node-property/column-zero payload hid a job body from it. Because a fork of `main` does
carry a publish-capable file, the old ok text overclaimed; the current ok line is the one quoted in the
CT-73 + CT-102 row (`scripts/check-publish-paths.sh:3020`), and the old string must not appear anywhere in this repository's markdown.

**Fail-closed.** A shallow clone is a global precondition: it states the remedy and ends the run
(`refusing: the repository is a shallow clone, … Fetch the full history (checkout with fetch-depth: 0, or
\`git fetch --unshallow\`) and re-run. (1)`, `scripts/check-publish-paths.sh:2657-2659`), as does an unlistable allowed tree
(`scripts/check-publish-paths.sh:2661-2663`). Per branch, a missing merge base refuses `unreadable-merge-base` (`scripts/check-publish-paths.sh:2925`), an
unreadable allowlist refuses `unreadable-allowlist` (`scripts/check-publish-paths.sh:2955`) and an unlistable branch tree refuses
`unreadable-branch-tree` (`scripts/check-publish-paths.sh:2965`). A refusal with no single path at fault names `-` in the path column
(`scripts/check-publish-paths.sh:2653-2657`, `scripts/check-publish-paths.sh:2925`, `scripts/check-publish-paths.sh:2965`) rather than a placeholder that looks like a file. The `version` job's
first checkout step sets `fetch-depth: 0` in `.github/workflows/build-candidate.yml:54`, with a comment
saying why.

**The allowlist.** `.github/publish-sweep-allowlist.txt` on `main`; blank lines and `#` comments are
ignored; otherwise exactly `<branch> <path> <blob-oid>`; exact match only; a missing file means an empty
list, not an error. It is empty today. The refusal text names the two remedies — merge or rebase the
change onto `main` once reviewed, or commit an allowlist line on `main` (the banner at `scripts/check-publish-paths.sh:2998-3015`).
`_allowlisted_change()` is `scripts/check-publish-paths.sh:2613`; a two-field, four-field, glob or stale-oid line is not a match because
`[ -z "$allow_extra" ] || continue` (`scripts/check-publish-paths.sh:2620`). The parser never reads the file.

**What the sweep is, and what contains the token it cannot see.** `build-candidate.yml` is `on: workflow_dispatch`. Its `version` job runs
`bash scripts/check-publish-paths.sh origin` from the ref that was dispatched
(`.github/workflows/build-candidate.yml:55-61`, checkout with `fetch-depth: 0` at `.github/workflows/build-candidate.yml:49-54`); on a
branch dispatch that is necessarily the branch's own copy of the script, so a branch's verdict is
only as trustworthy as the branch, and the authoritative run is a dispatch from `main`.

When a run is dispatched from a ref, GitHub executes that ref's own copy of the workflow file. The default-branch refusal and the sweep call are part of that file, so a branch that rewrites `.github/workflows/build-candidate.yml` removes both, and the `release` job — which declares no `environment:` — can then create a release with the built-in `contents: write` token. Nothing inside the repository can prevent this, because the file under attack is the file doing the policing. The signing credentials remain unreachable: `apple-signing` and `release-signing` allow deployments from `main` only and a branch's workflow text never declares them, so a branch can publish an unsigned release page but cannot sign or notarize anything. The binding controls are platform-side — a tag ruleset on `v*` and keeping write access tight — not code. As shipped: one collaborator (`cjtsh`, admin), no repository-level Actions secrets, main-only environment deployment policies, no non-main branches, and a tag dispatch can only attempt its own already-published version.

`linux-inputs.yml`/`windows-inputs.yml` are push-triggered. The secret-backed publish arms are contained
by the main-only `apple-signing`/`release-signing` environment policies; the sweep exists for the token
arms and is a **release-time tripwire, not runtime enforcement**. Plainly: a repository collaborator who
can push a branch can push a workflow GitHub will run, so the runtime containment is the repository's
access control and environment policies. **The security boundary is the identity arm plus the
allowlist read from `main`** — any non-main branch that adds or modifies `.github/workflows/` or
`.github/actions/` is refused unless the branch, path and blob are named in an allowlist read only
from `main`, so no unallowlisted workflow change reaches a release. The `permissions:`/callee reader
is **defense in depth for allowlisted changes**, a bounded lexical approximation whose exactness is
not claimed: an independent referee's fuzz measured 214 false oks on the pushed round-19 reader and
24 on the round-20 reader, and the parent measured 9 more on the round-21 reader out of 300 generated
write-granting documents. Platform controls (a tag ruleset on `v*`, environment protection) are the
recommendation recorded under `## Documented residuals`; they are not implemented in this revision,
and the certification must not rest on the reader. **What makes the weaker ok line safe** —
a fork of `main` does carry a publish-capable file: the only write grant on `main` is `contents: write` in
the `release` job (`.github/workflows/build-candidate.yml:891-892`), which carries no `environment:` key
but `needs: [version, source, macos, windows, linux, checksums]` (`.github/workflows/build-candidate.yml:889`); `macos` deploys to
`apple-signing` (`.github/workflows/build-candidate.yml:167`) and `checksums` to `release-signing` (`.github/workflows/build-candidate.yml:747`), and the `id-token: write` /
`attestations: write` bearer (`.github/workflows/build-candidate.yml:753-754`) sits inside the environment-gated `checksums` job. Both
environments allow only `main`, so on any other branch those jobs fail the branch policy and the `release`
job never runs. A branch that removes an `environment:` key is itself a modification of that file and is
caught by the identity arm (`branch-changes-workflow-file`) and re-judged by the parser.

**Three defects the independent corpora found in the final round, and the lesson.**

1. The closing banner counted identity offenders as publish-capable. Once the arm could refuse a
   read-only CI change, the summary line `refusing: a non-main branch carries a publish-capable workflow (N)`
   counted those too, and the trailer still said `Only main may carry a publish-capable workflow. Delete
   the file on the ref above, then re-run.` For a branch that only renamed a read-only workflow
   (`r_rename_readonly .github/workflows/ci-renamed.yml branch-changes-workflow-file`) both statements
   were false. Corrected by tracking the parser and identity offender counts separately
   (`PARSER_OFFENDERS=$((offenders - IDENTITY_OFFENDERS))` `scripts/check-publish-paths.sh:2999`), printing a class-specific summary
   (`_publish_capable_clause()` `scripts/check-publish-paths.sh:2983`, `_ci_definition_clause()` `scripts/check-publish-paths.sh:2990`, assembled `scripts/check-publish-paths.sh:3000-3007`) and
   attaching each remedy to its class (`scripts/check-publish-paths.sh:3012`, `scripts/check-publish-paths.sh:3015`), with the delete-the-file advice dropped. After
   the split, a mixed corpus prints exactly `refusing: 1 non-main branch carries a publish-capable
   workflow; 1 non-main branch changed its CI definition relative to the merge base with main (2)`, one
   remedy per class, and no delete-the-file sentence; the identity-only case prints only the CI-change
   clause plus the merge/rebase-or-allowlist remedy.
2. Fail-closed refusals printed `.` as the path for a global precondition (a shallow clone, an unlistable
   allowed tree, a missing merge base, an unlistable branch tree), once per branch. Corrected: a global
   precondition is stated once with the remedy (`fetch the full history`, i.e. the checkout's
   `fetch-depth: 0`, `scripts/check-publish-paths.sh:2657-2659`, `scripts/check-publish-paths.sh:2661-2663`), and a branch-level refusal with no single path uses `-`
   in the path column (`scripts/check-publish-paths.sh:2653-2657`, `scripts/check-publish-paths.sh:2925`, `scripts/check-publish-paths.sh:2965`).
3. The fork-from-main false positive above was found the same way — by building a corpus rather than by
   reading the code. The lesson: each of these was found by an independent corpus, which is why the
   evidence below lists the corpora and their pre-fix baselines.

**Evidence (all independent of the author's tests).**

- `identity`: 5 changes refused + 3 clean controls.
- `identity2`: 6 refused + 3 clean controls.
- `identity3`: an orphan history with no merge base fails closed (`d_unrelated`), a symlink at a workflow
  path is refused (`d_symlink`), a mode-only change with the same blob oid is clean (`d_mode`).
- `identity4`: 9 assertions — an exactly-allowlisted read-only change is clean (`e_good`), a branch that
  predates the allowlist commit and touches no CI is clean (`e_older`), a branch that edits
  `.github/publish-sweep-allowlist.txt` itself is inert (`e_allowlist_edit`, the file is read from the
  allowed ref), while a zero-oid entry (`e_stale`), a glob path (`e_glob`), a fourth-field line
  (`e_extra`) and an added action (`e_action`) are refused; and an allowlisted `write-all` change is
  refused on the parser's own reading (`e_parser_wins` — the allowlist cannot make a readable grant
  clean).
- `identity5`: 9 assertions — a fork identical to `main` (`g_fork`), a stale inherited read-only file
  (`g_oldreadonly`), a branch carrying `main`'s tip content (`g_copy_tip`) and an exactly-allowlisted
  read-only edit (`g_mod_allowlisted`) are clean; an un-allowlisted read-only edit (`g_mod_readonly`)
  and an un-allowlisted `write-all` edit (`g_stale_pub`, `g_mod_allowlisted_pub`) are refused, the last
  two by the parser with reason `grants-write-all`, never `branch-changes-workflow-file`.
- `fork`: `feature-x` identical to `main` prints the exact ok line and exits 0.
- `rename/delete`: a read-only rename refuses as a CI change, a publish-capable rename refuses as a write
  grant, a deletion is clean.
- `shallow`: a `--depth 1` clone fails closed and never prints ok.

Baselines against the round-9 script (each discriminates): `identity5` 6/9, `identity4` 4/9, and the
fork check fails. Live result: `bash scripts/check-publish-paths.sh origin` exits 0 with the ok line.
The referee fuzzer `fuzz3.py` (734 generated workflows, run alone) reports
`fixtures=734 parse_errors=1 gt_offenders=667 sweep_offenders=668`, `DEFECTS=0`, `OVER-REFUSALS=0`; the
single extra sweep offender is the tab-indented fixture (invalid YAML) — the sweep refuses it and PyYAML
cannot parse it, which is the correct direction, not a defect. `round7-check` reports
`ROUND7-CHECK: ALL GATES PASS`: the audit-I corpus matches its frozen baseline after canonicalizing
banner/remedy/ok text on BOTH sides (117 lines), with the single accepted reason delta
(`unreadable-multiple-documents` ↔ `grants-contents-write` for `wf2/M4_multidoc_write.yml`).

The new unit tests and their mutation proofs: the five cycle-11 cases and four cycle-12 cases named
above; the identity arm's 11 identity cases
(`test_the_sweep_refuses_a_branch_that_changes_a_workflow_or_action` `tests/test_workflow_config.py:4569`,
`test_the_sweep_needs_no_allowlist_file` `tests/test_workflow_config.py:4599`, `test_the_sweep_leaves_an_unchanged_branch_clean`
`tests/test_workflow_config.py:4615`, `test_the_sweep_measures_against_the_merge_base_not_the_tip` `tests/test_workflow_config.py:4624`,
`test_the_sweep_permits_an_exactly_allowlisted_change` `tests/test_workflow_config.py:4644`,
`test_the_sweep_refuses_an_allowlist_line_with_the_wrong_oid` `tests/test_workflow_config.py:4661`,
`test_the_sweep_ignores_an_allowlist_written_on_the_branch` `tests/test_workflow_config.py:4679`,
`test_the_sweep_ignores_a_deleted_workflow` `tests/test_workflow_config.py:4696`,
`test_the_sweep_allowlist_cannot_smuggle_a_publish_path` `tests/test_workflow_config.py:4708`,
`test_the_sweep_handles_a_symlink_and_a_mode_only_change` `tests/test_workflow_config.py:4742`,
`test_the_sweep_identity_arm_end_to_end` `tests/test_workflow_config.py:4766`); the 5 tip-blob/fork cases
(`test_the_sweep_leaves_a_fork_of_main_carrying_the_publisher_clean` `tests/test_workflow_config.py:4833`,
`test_the_sweep_still_refuses_a_stale_inherited_publisher` `tests/test_workflow_config.py:4846`,
`test_the_sweep_leaves_a_stale_inherited_read_only_workflow_clean` `tests/test_workflow_config.py:4865`,
`test_the_sweep_leaves_a_change_equal_to_mains_tip_clean` `tests/test_workflow_config.py:4885`,
`test_the_sweep_refuses_a_change_that_matches_neither_baseline` `tests/test_workflow_config.py:4903`); and the 3 banner-class cases
(`test_the_summary_names_only_the_publish_capable_class` `tests/test_workflow_config.py:4940`,
`test_the_summary_names_only_the_ci_change_class_for_a_rename` `tests/test_workflow_config.py:4958`,
`test_the_summary_names_both_classes_when_both_are_present` `tests/test_workflow_config.py:4981`), alongside the pre-existing
`SweepFailClosedPins` (5 cases, `tests/test_workflow_config.py:5369`). Each was broken on a disposable copy and watched red, with the
restored file compared byte-identical (`cmp`).

**The round-11 referees, and the round-14 repair that followed.**

Two further independent referees attacked this revision; neither was the author. Referee A
(`9f5949e1-7256-4366-a3aa-e8ba7834180f`) took the identity arm and filed seven findings; referee B
(`d6f42019-c03c-4218-bd20-a12555fc7f1c`) took the parser arm and defeated the `permissions`-key
reader. Each finding is recorded here as **fixed** or **disclosed**; none is called closed.

- **F1 (critical, fixed).** The merge-base skip was too broad. A branch that kept a stale inherited
  publish-capable file under `.github/actions/` printed the ok line, because its blob was identical
  to `main`'s tip. The skip now applies only to the paths the parser itself reads
  (`.github/workflows/*`): `identity_parser_reads` (`scripts/check-publish-paths.sh:2943-2946`) gates
  the merge-base baseline (`scripts/check-publish-paths.sh:2947-2948`), with the rewritten doctrine at `scripts/check-publish-paths.sh:2932-2942`. Referee A's
  own reproduction, `/tmp/refA/scratch/stale_action_check.sh`, now refuses
  `<branch> .github/actions/pub/action.yml branch-changes-workflow-file` and prints no ok line (the
  frozen script printed a false ok; the fixed corpus is 3/3). Two tests pin it —
  `test_the_sweep_refuses_an_inherited_action_that_is_not_mains_tip`
  (`tests/test_workflow_config.py:5076`) and
  `test_the_sweep_refuses_a_stale_inherited_read_only_action` (`tests/test_workflow_config.py:5118`) — and removing
  the `identity_parser_reads` guard reddens both, while
  `test_the_sweep_leaves_mains_own_action_clean` (`tests/test_workflow_config.py:5101`) and
  `test_the_sweep_still_refuses_an_added_action` (`tests/test_workflow_config.py:5152`) stay green.
- **F2 (critical, disclosed — not fixed).** The sweep step runs from the dispatched ref, so a branch
  dispatch executes the branch's own script copy and its verdict is only as trustworthy as the
  branch; the authoritative run is a dispatch from `main`. A branch that rewrites the workflow file
  removes both the call and the guard, so it can create a release page with the built-in token; the
  controls that bound that are platform-side. The corrected paragraph
  under "What the sweep is…" above records that the earlier "trusted `main` checkout" claim was
  false and has been removed.
- **F3 (disclosed).** The sweep compares `.github/**` blobs; an ordinary change under `scripts/**` is
  not a sweep finding.
- **F4 (out of scope by design).** The sweep fetches `+refs/heads/*` only. A tag dispatch cannot
  publish: `GITHUB_REF` is `refs/tags/…` so the default-branch guard refuses, there are zero
  repository-level Actions secrets, and every credential is in a main-only environment.
- **F5 (minor over-refusals, disclosed).** Referee A's generator produced 1872 presentation cases
  with `DEFECTS=0 OVER-REFUSALS=208`: `runs-release-action` 81, `calls-a-local-action` 81,
  `no-read-only-token-permissions` 17, `unreadable-multiple-documents` 15,
  `unreadable-token-permissions` 9 and `runs-gh-release` 5. Fail-closed only, and disclosed rather
  than hidden.
- **C3–C7 (minor over-refusals, disclosed — no code change).** Referee C's whole-change-set audit
  filed five cases the sweep refuses although nothing publish-capable is present: an anchored
  workflow-level `permissions` value with a read-only job override; an alias used only as an `env:`
  value; a publisher spelling inside an `if:`/`env:` value; a non-ASCII no-break space before a key;
  and `permissions::`. All five fail closed — the file is refused, never accepted — and the owner
  chose to disclose them rather than widen the gate in this round.
- **F6 (minor, fixed).** A symlinked `.github/publish-sweep-allowlist.txt` was followed as if it were
  file text. The tree entry must now be mode `100644` (`scripts/check-publish-paths.sh:2600`); any
  other mode sets `ALLOWLIST_OK=0` (`scripts/check-publish-paths.sh:2604`) and the arm refuses `unreadable-allowlist` (`scripts/check-publish-paths.sh:2955`).
  Pinned by `tests/test_workflow_config.py:5219`; the frozen script accepted the symlink (the
  referee's two-case corpus goes 0/2 to 2/2).
- **F7 (minor, fixed).** The shallow-clone precondition had no behavioural test.
  `test_the_sweep_refuses_a_shallow_clone` (`tests/test_workflow_config.py:5438`) pins it inside
  `SweepFailClosedPins`; deleting the precondition block (`scripts/check-publish-paths.sh:2657-2659`)
  is red.

**Referee B, the parser arm, and the round-14 repair.** A `permissions` KEY carrying a YAML node
property — `&p permissions:`, `? !!str permissions`, `? &p permissions`, `? &p !!str permissions` —
plus the explicit-key form hid a write-token grant, and the sweep printed the exact ok line while
PyYAML read write: eight hand-crafted cases. Round 14 peels node properties before the key is
compared, in one helper `_strip_key_props()` (`scripts/check-publish-paths.sh:1704`, doctrine at
`scripts/check-publish-paths.sh:1696-1703`) used by `permissions_verdict()` (`scripts/check-publish-paths.sh:1748`), the flow reader (`scripts/check-publish-paths.sh:1635`), the jobs locator
(`scripts/check-publish-paths.sh:2179`), the jobs exclusion (`scripts/check-publish-paths.sh:2234`) and the child-declaration reader (`scripts/check-publish-paths.sh:2273`); an explicit `?`
marker is moved to the front of the key. Referee B's differential harness (1000 fixtures, 989 valid)
went from `DEFECTS=59` against the frozen parser to
`fixtures=1000 valid=989 gt_offenders=904 sweep_offenders=938 DEFECTS=0 OVER-REFUSALS=23`, and the
round-14 gate reports `KEYPROPS: 12 pass, 0 fail` against a frozen baseline of 4 pass and 8 fail.
Five tests pin it (`tests/test_workflow_config.py:2478`, a write grant hidden by a node property
across 13 shapes; `tests/test_workflow_config.py:2642`, five read-only controls; `tests/test_workflow_config.py:2713`, a plain `write-all` control; `tests/test_workflow_config.py:2729`,
the same key inside a flow mapping; `tests/test_workflow_config.py:2761`, the column-zero `jobs:` pin). Referee B also showed that
the mutation `drop_jobs_key_position_rule` — the column-zero rule
`[ "${#ind}" -eq 0 ] || continue` (`scripts/check-publish-paths.sh:1316`) — survived the suite;
`test_the_sweep_reads_only_a_column_zero_jobs_key` (`tests/test_workflow_config.py:2761`) is the
decoy that now reddens it.

**The live posture after the 2026-10-08 cleanup.** On 2026-10-08 the fourteen stale non-main branches
were deleted from `origin`, which now carries exactly one head, `main`. Their tips are recorded in
`/tmp/stale-branch-backup.txt`; each was 51–326 commits behind `main` (50–245 by first-parent count), at most one ahead, last
touched 2026-10-06 except one on 2026-09-27, and none carried
`.github/workflows/build-candidate.yml`. The live branch claim is therefore vacuous by construction
today; the sweep still audits any branch that exists later, and this paragraph records a measurement,
not a closure. Tags and releases were deliberately **not** deleted: there are zero repository-level
Actions secrets and every credential is scoped to the main-only `apple-signing`/`release-signing`
environments, so an old tag or branch can reach no credential, while deleting release history would
cost users the provenance of builds they can still verify and would clear no finding.

### Verification of the round-16 and round-17 sweeps (the parser classes and the continuation readings)

Referee E's fresh parser fuzzer (`7eada9d5…`, revision `fea859c`) broke the parser with three
classes; the round-17 probe found a fourth. All four are repaired in the same change set, and each
names the test that reddens when the repair is broken:

1. **A job-level explicit key whose value sits on the next line.** `? 'permissions'` on its own line
   followed by `contents: write` is the permissions key to PyYAML; the explicit-key reader accepted
   the quoted spelling as a literal word. The reader now peels key properties and resolves the
   explicit-key forms before deciding (`_strip_key_props()` at `scripts/check-publish-paths.sh:1704`,
   the peel at `scripts/check-publish-paths.sh:1748`, the pattern at `scripts/check-publish-paths.sh:1743`). Pinned by
   `test_the_sweep_refuses_a_single_quoted_explicit_permissions_key` at
   `tests/test_workflow_config.py:2801`.
2. **A `permissions` key spelled with YAML escapes.** `? "permiss\u0069ons"`, the `\x`/`\U` forms
   and a key property before the quote all decode to the word. The escape pattern
   (`pat_escaped_key` at `scripts/check-publish-paths.sh:1771`) anchors the quote in key position
   rather than at line start. Pinned by
   `test_the_sweep_refuses_an_escaped_explicit_permissions_key` at
   `tests/test_workflow_config.py:2827`.
3. **A low-indent continuation inside `jobs:` that collapsed the measured job-id column.** A scalar
   (`name: "a` / ` b"`) or a flow collection (`env: {` / ` a: 1}`) whose continuation line sits at a
   lower indent used to take the minimum over the whole block, lowering `JOBS_JOBID_INDENT` (set at
   `scripts/check-publish-paths.sh:1414`, guarded at `scripts/check-publish-paths.sh:1428`, consumed at `scripts/check-publish-paths.sh:1454`) so that a job body
   and its `permissions:` fell out of the read. Pinned by
   `test_the_sweep_reads_a_job_after_a_low_indent_scalar_continuation` at
   `tests/test_workflow_config.py:2867` and
   `test_the_sweep_reads_a_job_after_a_low_indent_flow_continuation` at `tests/test_workflow_config.py:2896`.
4. **An explicit key split across lines by a double-quoted line continuation** (round 17).
   `? "permis\` split as `sions"` is one key after parsing; the same reader had read the
   fragment as a literal. Pinned by
   `test_the_sweep_refuses_an_explicit_key_split_by_a_line_continuation` at
   `tests/test_workflow_config.py:3759`.

A repair that reads more must not refuse more, so the same change set pins the read-only side: a
continuation that is genuinely a continuation is still read
(`test_the_sweep_reads_a_low_indent_continuation_but_stays_fail_closed` at
`tests/test_workflow_config.py:2971`), and a column-zero continuation of a quoted scalar is a
continuation when the reader knows a quote is open — including when a node property precedes the
opening quote, the round-19 repair — while otherwise it ends the block and the locator fails closed
(`test_the_sweep_refuses_a_write_after_a_column_zero_quote_continuation` at `tests/test_workflow_config.py:2926`,
`test_the_sweep_refuses_a_write_after_a_column_zero_flow_continuation` at `tests/test_workflow_config.py:2952`). Referee C's two
pin gaps are closed in the same round and named in the referee C paragraph below. Referee E's
corpus and its re-run are recorded in the evidence trail that follows. This is what the round
repaired; it is not a verdict that the parser has no further holes.

**Evidence trail.** The rounds recorded above were run by referees independent of the author.
Round-11 identity arm: referee `9f5949e1-7256-4366-a3aa-e8ba7834180f`, artifacts under `/tmp/refA/`
(the stale-action reproduction `scratch/stale_action_check.sh` and the 1872-case generator) — F1
**fixed**; F2, F3, F4 and F5 **disclosed**; F6 and F7 **fixed**. Round-11 parser arm: referee
`d6f42019-c03c-4218-bd20-a12555fc7f1c`, artifact the 1000-fixture differential harness and the
surviving `drop_jobs_key_position_rule` mutation — **fixed** in round 14. The round-12 fixer added the
inherited-action tests, the allowlist-mode guard and the shallow-clone pin; the round-14 fixer added
the `permissions`-key node-property peel.

Referee C's whole-change-set audit (`52bce30e…`, revision `7d271c9`) filed one critical finding, two
pin gaps and five fail-closed over-refusals. The critical finding is the C1 recorded above: a
`workflow_dispatch` run executes the dispatched ref's own copy of the workflow file, so a branch
that rewrites it removes the guard and can create an unsigned release page with the job's built-in
token — a limit no in-repository change removes. The two pin gaps are the allowlist's exact-field
rule (`[ -z "$allow_extra" ] || continue`), which a mutation deleted with the suite still green,
and `probe.py`'s `EXPECTED_HWI_VERSION`, which a mutation from `3.2.0` to `9.9.9` likewise
survived; the round-16 addendum pins both — `[ -z "$allow_extra" ] || continue` at
`scripts/check-publish-paths.sh:2620` (`test_the_sweep_refuses_an_allowlist_line_with_a_fourth_field`,
`tests/test_workflow_config.py:5170`) and `probe.py:228`'s `EXPECTED_HWI_VERSION`
(`test_the_pinned_hwi_release_is_the_one_the_manifest_records`,
`tests/test_hardening_pins.py:434`). Referee C ran ten mutations: nine were caught and only
the allowlist deletion survived, and every file was restored byte-identically to the tree it
audited (`d772cee40fe99df8fbf028ca825f9f70d5a5a81d`, `git ls-tree -r HEAD | md5` =
`45943717a7c80d527c78bc81232c1d56`). Its own baseline on that revision was
`Ran 749 tests in 279.563s` — **OK**.

Referee D's claims audit (`d7af4091…`, revision `7d271c9`) filed no critical finding and four minor
ones: a citation pointing at the wrong comment, a test-count attribution to the wrong tree, a stale
commit-distance range, and a replaced test name still cited as live. All four are corrected in this
pass. Referee D resolved 75 of its 76 citations.

Referee E's fresh parser fuzzer (`7eada9d5…`, revision `fea859c`) broke the parser with three
classes: a job-level explicit key whose value sits on the next line; a `permissions` key spelled
with YAML escapes (`? "permiss\u0069ons"` and the `\x`/`\U`/leading-escape forms); and a low-indent
continuation inside `jobs:` that lowered the measured job indent (`JOBS_JOBID_INDENT`) and deleted
a job body and its `permissions:`. Its baseline run measured
`fixtures=856 valid=760 gt_offenders=538 sweep_offenders=641 DEFECTS=56 OVER-REFUSALS=56`. The
round-16 repair answers all three classes and pins them; the same harness re-run against the
repaired script measures `fixtures=856 valid=760 gt_offenders=538 sweep_offenders=715 DEFECTS=0
OVER-REFUSALS=64`, the eight added over-refusals being fail-closed fixtures (fx343, fx344, fx345,
fx367, fx368, fx369, fx711, fx810).

The gates run on the round-17 revision were: the full Python suite
(`Ran 759 tests in 310.097s` — **OK**, earlier), `tests/test_workflow_config.py` alone (`Ran 172 tests in 147.358s` — **OK**, earlier), referee B's
differential harness (`DEFECTS=0 OVER-REFUSALS=23`), referee A's generator (`DEFECTS=0`), the
round-14 `KEYPROPS` gate (`12 pass, 0 fail`), `bash -n` over every shell script, `yaml.safe_load`
over every workflow, and the ten `tests/ui_*.cjs` scripts (exit 0). This is the state of the
evidence, not a verdict on it.

### Verification of the round-19 sweep repair (the node-property blind spot)

**The finding.** An independent referee (F) defeated the round-17 revision with a false OK, and
referee G reproduced it. The payload is 138 bytes, md5 `466ae6250d4b5d39a05201cafda06b7c`: a job
whose `name:` is `!!str "a`, continued at column zero by `b"`, followed by a second job granting
`contents: write`. The round-17 script printed the ok line and exited 0 on that workflow.

**The mechanism.** A node property in front of the opening quote left the quote untracked, so
`_locate_jobs_key()` read the column-zero continuation as the end of the `jobs:` block and
`strip_scalar_bodies()` stripped the second job's body — including its write grant — as scalar data,
leaving only the top-level `read-all` for the permissions reader to see. The class is pre-existing:
it reproduces on revisions before round 16, so no earlier round introduced it and no earlier round's
claim was about it.

**The repair.** The readers consume a node property as a single token — `!`, `!!x`, `!<uri>`, `&name`,
`*name` and combinations — with `!<…>` read through its closing `>`, and a property immediately before
the opening quote opens it, so the column-zero continuation is a continuation again. The quoted-scalar
escape and doubling branches are pinned where they bind: the two `_line_node_state` escape arms
(`scripts/check-publish-paths.sh:1122`, the backslash arm, and `scripts/check-publish-paths.sh:1123`,
the doubled `''` arm) are mutants M5 and M8, and advancing either by one character turns the tagged and
the untagged escape fixture into false oks (CAUGHT). The round-20 revision also had a second
scanner, `_qs_line_open_quote()`, with its own two escape arms; an instrumented copy of that
revision's script recorded both arms reached on every escape fixture but verdict-neutral there, so
they are recorded as unpinned: mutating both changed no false-ok verdict across 645 checked mutants.
Round 21 folded that scanner into `_line_node_state()`, so the frozen bytes carry one scanner and one
pair of escape arms (`scripts/check-publish-paths.sh:1122` and
`scripts/check-publish-paths.sh:1123`). The round-19 docstring in `tests/test_workflow_config.py` that claimed each mutant was caught by exactly one of the two was wrong on the same point and is corrected in the code (`tests/test_workflow_config.py:3127`). Mutants M4 and M7 are equivalent, because
`JOBS_JOBID_INDENT` is assigned only when `${#ind} > JOBS_INDENT`, so it is always at least 1 whenever
`saw_child` is 1.

**The RED evidence.** Against the pre-round-19 script (`scripts/check-publish-paths.sh`,
md5 `324451255af8554502a5bacf0b2f7c30`, 2781 lines — the earlier revision) with these tests in place,
`test_the_sweep_refuses_a_write_after_a_node_property_and_column_zero` FAILED (failures=10) and
`test_the_sweep_refuses_a_write_after_a_quote_escape_and_column_zero` FAILED (failures=2), while the
three controls stayed OK.

**The scope.** The reader is a bounded parser of the shapes GitHub workflows use and it fails closed
on what it cannot read; it is not a YAML implementation, and no sentence here rests on it being
unfoolable. The allowlist is independent of the parser arm and cannot make an unreadable construct
visible to it.

**Gates and corpora on the round-19 tree.** The full suite on the round-19 tree is `Ran 767 tests in
331.443s` — **OK**; `tests/test_workflow_config.py` alone on the round-19 tree is `Ran 180 tests in
149.516s` — **OK**; the hardening file is `Ran 84 tests in 4.433s` — **OK**. `PublishPathSweepTests`
held 121 cases on the round-19 tree and `SweepFailClosedPins` 5. Referee E's fresh-clone corpus (856 fixtures) measures `fixtures=856 valid=760 gt_offenders=538
sweep_offenders=715 DEFECTS=0 OVER-REFUSALS=64`, identically for the pre-round-19 and the fixed
script; referee B's 1000-fixture differential harness measures `fixtures=1000 valid=989
gt_offenders=904 sweep_offenders=938 DEFECTS=0 OVER-REFUSALS=23`. Referee F's reproducer against the
fixed script prints `VERDICT: refused (exit 1)`, F's 17-case probe prints `FALSE OK COUNT: 0`, and
F's five variants v15–v19 are all refused. The parent's own probes `/tmp/r19-check.sh` (13/13,
`R19-CHECK: PASS`) and `/tmp/r19f-check.sh` (10/10, `R19F-CHECK: PASS`) pass.

**The independent-verification trail.** Referee C (containment), referee D (style), referee E
(corpus), referee F (the false OK, the mutants and the prose), referee G (the claims audit),
referee H (the explicit-key false OK, the mutant map and the stale counts) and referee I (the
continuation-indent regression) each
closed as fixed, disclosed or out of scope. F-1, the node-property/column-zero false OK, is
**fixed**; F-2, the escape and doubling mutants M5 and M8, is **fixed** by pinning, with M4 and M7
recorded as equivalent; F-3, the prose claim that the allowlist left a publish-capable change
auto-refused, was false and is corrected in this revision; G-2, the same overstatement and the
"closed the job-id hole" wording, is **corrected**; H-1, the explicit-key/column-zero false OK, is
**fixed**; H-2, the round-19 mutant sentence that was true of only the two `_line_node_state` arms, is
**corrected** and the two `_qs_line_open_quote` arms are recorded as unpinned; H-3, the stale counts
and hashes, is re-measured and corrected; I-1, the continuation-indent regression, is **fixed**. Referee C's C1 — a branch dispatch runs the
branch's own copy of the workflow file — remains **disclosed, not fixed**, and is a platform-side
owner decision; referee D's four minor findings are corrected in this pass. This is what the rounds
repaired; it is not a verdict that the parser has no further holes.

### Verification of the round-20 sweep repair (the explicit-key indicator)

**The finding.** An independent referee (H) defeated the round-19 revision with a false OK: the sweep
printed its ok line and exited 0 on a workflow whose job permissions PyYAML's `SafeLoader` reads as
`{"contents": "write"}`. The payload is 140 bytes, md5 `cbb5a7648dbc05ff8d37f4faa0673a44`: a job whose
`name:` is `? "a`, continued at column zero by `b"`, followed by a second job granting
`contents: write`. The flow form of the same shape, md5 `cb16509f7560308ce122be44667a1393`, is
`name: {? "a}` continued by `b": 1}`. The mechanism is the YAML explicit-key indicator `?` immediately
before the opening quote: `?` was not in the node-position set, so the quote never opened, the
column-zero continuation ended the `jobs:` block, and `strip_scalar_bodies()` stripped the later job's
grant — including its `contents: write` — as scalar data, leaving only the top-level `read-all` for the
permissions reader to see. The class is pre-existing: it reproduces on the pushed round-19 revision
`91aedfaef33ea9e3762fc36b95463bca1b345678` and on `bf3ba57` before round 19, so no earlier round
introduced it; but `?` sits adjacent to the node-property spellings round 19 enumerated.

**The repair.** `?` was put in the node-position set in **both** of that revision's quote-opening
scanners — `_qs_line_open_quote()` (`scripts/check-publish-paths.sh:949`, now a wrapper) and
`_line_node_state()` (`scripts/check-publish-paths.sh:1062`) — so the measured `? "a` payloads were
refused by the rule rather than one payload spelling at a time. It did not close the class: an
independent referee's fuzz measured 24 remaining false oks on this round-20 reader, and 214 on the
pushed round-19 revision before it. Round 21 replaced the per-character rule with a plain-scalar state
machine (see the rounds-21/22 subsection below), and an undecidable position opens the quote, so the
reader fails closed.

**The RED evidence.** The systematic indicator matrix (the parent's `/tmp/r20-matrix.sh` harness) found
3 false oks on `91aedfa` — `? "a`, `?  "a` and the flow `{? "a}` — and the fixed script refuses every
write-granting shape (0 false oks) while the read-only controls stay clean; the fixer's wider 36-case
matrix (every indicator and property composition, block and flow) found 1 write-granting false ok on
`91aedfa` (`flow-question`) and 0 on the fixed script. The differential fuzz with PyYAML's `SafeLoader`
as the oracle: the fixer's run generated 1290 PyYAML-valid write-granting mutants, of which 331 were
false oks on `91aedfa` and 0 on the fixed script; the parent's own run with an independent seed
generated 1200 mutants (300 PyYAML-valid write-granting), of which 78 were false oks on `91aedfa` and
0 on the fixed script.

**The mutant map** is recorded in the round-19 subsection above (correction H-2): the two binding
escape arms are in `_line_node_state` and turn the escape fixtures into false oks when advanced by one
character, while the round-20 revision's two `_qs_line_open_quote` arms were reached but
verdict-neutral in every shape measured and changed no false-ok verdict across 645 checked mutants.

**The scope.** The reader remains a bounded parser of the shapes GitHub workflows use, and it fails
closed on what it cannot read; it is not a YAML implementation, and no sentence here rests on it being
unfoolable. The allowlist is independent of the parser arm and cannot make an unreadable construct
visible to it.

**Gates and corpora.** The round-20 repair adds three cases that take `PublishPathSweepTests` from 118
to 121; the re-measured suite counts are in the counts table in the cycle-6 section above, and the
corpora are unchanged by this round: referee E's fresh-clone corpus measures `fixtures=856 valid=760
gt_offenders=538 sweep_offenders=715 DEFECTS=0 OVER-REFUSALS=64`, referee B's 1000-fixture differential
harness measures `fixtures=1000 valid=989 gt_offenders=904 sweep_offenders=938 DEFECTS=0
OVER-REFUSALS=23`, referee F's reproducer prints `VERDICT: refused (exit 1)` and F's 17-case probe
prints `FALSE OK COUNT: 0`, and the shallow-clone refusal, the round-9 25/25, `ROUND7-CHECK ALL GATES
PASS`, the live sweep's `ok:` (rc=0) and the fuzz3 corpus (`fixtures=734 parse_errors=1
gt_offenders=667 sweep_offenders=668`, `OVER-REFUSALS 0`) all pass.

### Verification of the rounds-21/22 sweep repair (the plain-scalar state machine)

**The finding.** Referee I defeated the round-20 reader: `/tmp/refI/fuzz_mine.py` (seed `0x1A17E20`,
N=3000) measured 214 false oks on the pushed round-19 revision `91aedfaef33ea9e3762fc36b95463bca1b345678`
and 24 on the round-20 script, and classifying its 74-file corpus `/tmp/refI/fuzz_falseoks/` gives 12
REGRESSION (round 19 refused, round 20 printed the ok line), 12 BOTH-FALSE-OK, 4 FIXED, 15 refused,
29 parse-error and 2 not-a-write. The 12 regressions are one shape: `name: a?"b` is the plain scalar
`a?"b` to PyYAML — the `?` is scalar content and the `"` cannot open a scalar — but the round-20
previous-character rule saw the `?` and opened a quote, so the quote state desynced, a column-zero
continuation ended the `jobs:` block and a later job's `contents: write` was stripped as scalar data.
`/tmp/refI/docshapes/vB_flow_plus_prior.yml` (md5 `a3de0ac12eb14afce9ef5b1ada067950`, referee H's
payload B plus one preceding `name: a?"b` line) printed the ok line on both `91aedfa` and the round-20
script. The parent then defeated the round-21 repair with `/tmp/refJ-corpus/r21-minDup.yml` (150 bytes,
md5 `7f58c4341f41ff3ae1b65608f1a022a3`): a plain scalar whose run of same-indent continuation lines
resets the carry, read by PyYAML, libyaml and Ruby Psych as `jobs.run.permissions.contents == write`.

**The mechanism and the repair.** Round 21 replaced the per-character "may a quote open here?" test
with node position computed from indicator boundedness, the way PyYAML's `scan_plain`/`check_value`
do it: a quote opens only in node position; node properties (`&name`, `*name`, `!`, `!!str`,
`!<uri>`) retain node position; `-`, `?`, `:`, `,` are indicators only when bounded, so an unbounded
one is plain-scalar content and `a?"b` keeps its quote as data; and a plain scalar continues onto a
more-indented continuation line. One function serves both scanners — `_line_node_state()`
(`scripts/check-publish-paths.sh:1062`), with `_qs_line_open_quote()`
(`scripts/check-publish-paths.sh:949`) delegating to it — so the two cannot disagree about what is
data and what is structure. Round 22 then found that the carry compared the next line against the
previous line's indent, so a run of two or more same-indent continuation lines reset the plain
scalar; the repair carries the scalar's base indent `local base="$pind" carried=0`
(`scripts/check-publish-paths.sh:1077`) unchanged across its continuation lines, uses it at
`scripts/check-publish-paths.sh:1112`, and applies the base rule for `:`/`-`/`?` at
`scripts/check-publish-paths.sh:1265`. Where the position is undecidable the reader opens the quote,
so it fails closed.

**The RED and GREEN evidence.** The pinned payloads are `r21-minDup.yml` and four more parent
fixtures, pinned in `test_the_pinned_continuation_payloads_are_unchanged`. Against the round-21 tree
(`scripts/check-publish-paths.sh` md5 `24e540d526727cea8f583b49572d8d7d`, 2979 lines) the round-21
tests are `FAILED (failures=7)`; against the round-20 baseline (`scripts/check-publish-paths.sh`,
md5 `e86d6b70e62acdc656c9ee15949043aa`) `FAILED (failures=2)`; on the frozen bytes they are GREEN.
The fuzz: the parent's `/tmp/r22-fuzz-mine.py` measured 460 false oks on the round-20 tree, 70 on
the round-21 tree and 0 on the frozen bytes over 1500 documents (seed 77001); a 300-document set went
9 → 0; a fresh 600-document seed 909090 went 30 → 0; the fixer's systematic engine (4320 documents,
every indent pattern of length 2-5) went 1620 on the round-20 tree and 894 on the round-21 tree to 0;
the 1200-mutant corpus `/tmp/refJ-corpus/mf-payloads.json` went 499 on the round-20 tree and 2 on the
round-21 tree to 0.

**The scope, in the open.** The reader is a bounded lexical approximation that fails closed on what it
cannot read; it is not a YAML implementation. Each of the last four rounds was defeated on a new
quoting shape — a node property, a URI tag, the explicit-key indicator `?`, and a duplicated
continuation line — so no sentence here declares the class closed, unassailable or unfoolable. The
allowlist is independent of the parser arm and cannot make an unreadable construct visible to it.

**Gates and corpora.** `PublishPathSweepTests` grew from 121 on the round-20 tree to 127 on the
frozen bytes; the re-measured suite counts are in the counts table in the cycle-6 section above. The
corpora are unchanged by these rounds: referee E's fresh-clone corpus measures `fixtures=856
valid=760 gt_offenders=538 sweep_offenders=715 DEFECTS=0 OVER-REFUSALS=64` and referee B's
1000-fixture differential harness measures `fixtures=1000 valid=989 gt_offenders=904
sweep_offenders=938 DEFECTS=0 OVER-REFUSALS=23`.

### Verification of the round-23 sweep repair (the sequence-entry block scalar)

**The finding.** An independent referee (J) defeated the round-22 bytes with a false OK. The payload
is a job whose `name:` is a sequence entry introducing an **empty** block scalar, continued at the
entry's content column by a line that opens a quote and closes it at column zero, followed by a
second job granting `contents: write` (the parent's `t6`; referee J's 425-shape family produced 141
PyYAML-valid false oks on that revision, and J's generator `/tmp/refJ-work/fuzzJ.py <seed> 3000`
produced 3000 write documents, 1257 of them parser-passing, with 60 of 60 end-to-end false oks).
The empty scalar carries no body to PyYAML, but the round-22 reader modelled the entry's indentation
on the dash column, treated the `? "k` opener on the line after the header as block-scalar content
and ended the `jobs:` block at the column-zero closer, so the later job's `permissions: contents:
write` was stripped as scalar data and the sweep printed its ok line. The same shape defeated the
round-22 reader with a folded (`>-`) and a chomped (`|-`) header, with two jobs, and with a comment
on the closing line.

**The repair.** The reader now computes the column PyYAML uses as a block scalar's indent — the
column of the block collection that owns the scalar: the key's own column for `    key: |`, the
entry's **content** column (8) for `      - key: |` because the entry opens a mapping, and the dash
column for `- |` because there the entry *is* the scalar — in `_bs_header_col()`
(`scripts/check-publish-paths.sh:1376`), used at the three `_bs_indent_scan` call sites
(`scripts/check-publish-paths.sh:1482`, `scripts/check-publish-paths.sh:1609`,
`scripts/check-publish-paths.sh:1709`). The first version of that helper carried a `local`
declaration defect — on one `local` line, `ind="${l%%[![:space:]]*}"` expands before `l` is assigned
— so every non-dash header reported column 0 and the body of a `runs-on: |` header swallowed
structural lines; an independent 1500-document corpus caught exactly one false OK from it
(`rk01073`) and it is fixed. There is no fail-closed posture in this round: the reader models the
shape. Two independent oracles agree on the fixtures — PyYAML's `SafeLoader` and Ruby Psych 3.1.0 —
and the read-only twins stay clean.

**The RED and GREEN evidence.** Against `f4ca17b2688f3024ba2a78a1c68dcb95ae642663` (the round-22
commit, `scripts/check-publish-paths.sh` md5 `49cf7d9e29428acd6fc34d1701983430`) the four round-23
tests are `Ran 4 tests in 6.188s` — `FAILED (failures=6)`, one per shape (`e1_t6_id`,
`e2_two_jobs_sq`, `e3_comment_close`, `b1_av00000`, `b2_folded_wd`, `b3_chomp_name`); on the frozen
bytes they are GREEN, `PublishPathSweepTests` is `Ran 131 tests` — **OK**, `tests/test_workflow_config.py`
alone is `Ran 190 tests` — **OK**, and the full suite is `Ran 777 tests in 360.053s` — **OK**. The
fuzz: J's generator measures `HITS=1257` write documents with `FALSE-OK=0` on the frozen bytes
(60/60 false oks on the failed revision); the parent's 600-document fresh-seed set, the 1500-document
`rk15` set, the 300-document `rk300` set and the 1200-mutant corpus all measure 0 false oks, where
the intermediate revision whose `_bs_header_col` reported 0 measured 1 (`rk01073`); and the
empty-scalar corpora (300 documents in `av`, 800 in `av2`) measured 21 and 169 false oks against the
modelled reader before the entry-content column was computed exactly and 0 on the frozen bytes.

**The scope, in the open.** The repair adds four cases in `PublishPathSweepTests` —
`test_a_sequence_entry_write_grant_cannot_hide_behind_the_block_end`,
`test_the_read_only_twins_of_the_round_23_shapes_stay_clean`,
`test_block_scalars_with_quotes_stay_accepted` and
`test_the_pinned_round_23_payloads_are_unchanged` — and referee J's behaviour-bearing mutant M2b (a
base raise that uses the key column on a `- ` line) now reddens three of the six round-23 shapes
(`e1_t6_id`, `e2_two_jobs_sq`, `e3_comment_close`), where on the failed revision the whole sweep
class stayed green, which is why the class existed. The corpora are unchanged by
this round: referee E's fresh-clone corpus measures `fixtures=856 valid=760 gt_offenders=538
sweep_offenders=715 DEFECTS=0 OVER-REFUSALS=64` and referee B's 1000-fixture differential harness
measures `fixtures=1000 valid=989 gt_offenders=904 sweep_offenders=938 DEFECTS=0
OVER-REFUSALS=23`, so the repair adds no over-refusal. The reader remains a bounded lexical
approximation that fails closed on what it cannot read, not a YAML implementation, and no sentence
here declares the class closed, unassailable or unfoolable: each of the last five rounds was
defeated on a new shape. The allowlist is independent of the parser arm and cannot make an
unreadable construct visible to it.

## Publication

**Not yet published.** This revision is the candidate the owner reviews; the next Color
Team cycle audits this commit before any tag exists. Cycle 5 graded the previous revision
**⛔ BLOCKED** on the findings remediated above; the cycle-6 review of `f79203c` then filed the
bypasses the second cycle-6 round fixes, and this revision has not itself been audited. Promotion
to a public release requires, in order: an audit of this revision, a signed and notarized
`publish=false` candidate through the unified pipeline, and the owner hardware walkthrough.
Manual publication is prohibited.
