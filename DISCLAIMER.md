# Bitcoin Easy Signer: terms of use, warranty disclaimer, and limitation of liability

**Effective date / last updated:** October 25, 2026
**Publisher / maintainer:** Bitseeker LLC (GitHub account: [`@cjtsh`](https://github.com/cjtsh))
**Canonical legal framework:** [https://github.com/cjtsh/software-disclaimer](https://github.com/cjtsh/software-disclaimer) — *Standard Software Disclaimer & Limitation of Liability*, version 1.2.2, effective October 21, 2026.

This notice is the Bitcoin Easy Signer copy of the Bitseeker LLC Standard Software
Disclaimer & Limitation of Liability (the "Framework"). It incorporates the
Framework as published at the canonical URL above and adds the Bitcoin Easy
Signer-specific facts below. Where the canonical publication changes, the
canonical text at that URL is the operative version; this file is the project's
own copy of it and should be refreshed when the Framework changes.

**Please read before using Bitcoin Easy Signer.** It is free, open-source
software offered to the Bitcoin community. The source is public for anyone to
inspect, test, audit, and validate. Public source availability is not a claim
that a particular release has received a professional or independent security
audit.

Version 0.7.4 is the current source revision. It changes how the app itself behaves in one direction: when a broadcast server answers with an error after the complete signed payment has already been sent to it, the app now treats the result as unknown rather than as a refusal, records the payment against the wallet and keeps the wallet paused, instead of clearing the pause and letting a retry leave on the strength of a status code. Only a check that runs before anything is sent — an unsupported network, a missing mainnet opt-in, an unusable size, invalid hex — is still treated as a proven non-send. The narrow behaviours added in 0.7.3 are unchanged: while a payment is being submitted the wallet refuses another and says so, the pause it keeps lasts until every recorded payment is confirmed rather than only the newest, and a connection reset while checking a network server is reported as the documented unavailability rather than as a generic failure. Nothing changes in how an honest payment is prepared, signed, checked or broadcast, in which networks are offered, or in the fee ceilings.
The app runs one engine across Testnet4, Mutinynet, and mainnet, and asks hardware
devices to sign through Bitcoin Core HWI (HWI). Mainnet submission requires an
explicit confirmation on the final review screen and a separate backend opt-in
that fails closed when it is missing. One recorded mainnet transaction proves
that the path works once; it is not a promise about any later transaction. A
version number is not a promise of anything. Signed but not yet broadcast
transaction bytes can be submitted by anyone who has them, so treat a signed
transaction as spendable by whoever obtains it.

For purposes of this notice, “Protected Parties” means Bitseeker LLC and its
sole member, managers, officers, employees, contractors, agents, affiliates, and
open-source contributors, but only to the extent the relevant claim arises from
acts or omissions performed for or on behalf of Bitseeker LLC or in connection
with the Software. This definition does not itself shield any person from
liability for that person's own conduct or create a defense where applicable law
does not provide one.

This notice accompanies the applicable open-source license (see
[§10](#10-governing-open-source-license)). It does not guarantee that every
provision forms a binding contract merely because a person visits the repository
or downloads software. Contractual provisions such as indemnification or forum
selection may require clear notice and affirmative assent, depending on the
facts and applicable law. Bitcoin Easy Signer itself presents no acceptance
gate: whoever distributes, hosts, or deploys the software is responsible for
obtaining any assent that their own distribution and jurisdiction require.

---

## 1. Conspicuous notice of warranty disclaimer and liability limitation

THIS SOFTWARE, SOURCE CODE, BINARIES, SCRIPTS, DOCUMENTATION, AND ASSOCIATED
MATERIALS (COLLECTIVELY, THE "SOFTWARE") ARE EXPERIMENTAL AND PROVIDED SOLELY
FOR EDUCATIONAL, TESTING, RESEARCH, AND PERSONAL UTILITY PURPOSES.

THE SOFTWARE IS PROVIDED **"AS IS"** AND **"AS AVAILABLE"**, WITHOUT WARRANTY OF
ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED
WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, TITLE, SECURITY,
ACCURACY, RELIABILITY, AND NON-INFRINGEMENT.

TO THE MAXIMUM EXTENT PERMITTED BY APPLICABLE LAW, THE PROTECTED PARTIES SHALL
NOT BE LIABLE FOR INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, PUNITIVE, OR
CONSEQUENTIAL DAMAGES (INCLUDING LOSS OF DATA, HARDWARE DAMAGE, SYSTEM FAILURE,
LOST PROFITS, LOSS OF DIGITAL ASSETS, OR BUSINESS INTERRUPTION) ARISING OUT OF
OR RELATED TO THE SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGES.
THIS LIMITATION APPLIES UNDER ANY THEORY OF LIABILITY. NOTHING IN THIS
DISCLAIMER EXCLUDES OR LIMITS LIABILITY THAT CANNOT LAWFULLY BE EXCLUDED OR
LIMITED.

For Bitcoin Easy Signer specifically, this means no promise that the app will
work with your wallet, your devices, or your version of the Bitcoin network, and
no promise that it prevents the loss of funds. Bitcoin transactions are
irreversible: a payment sent to the wrong address, for the wrong amount, with
the wrong fee, or with the wrong change output cannot be recalled by the
project. Nothing in this notice removes any right or liability that applicable
law does not allow to be excluded.

---

## 2. Autonomous agents, AI & automated execution

AUTONOMOUS AGENTS, LARGE LANGUAGE MODELS (LLMS), AUTOMATED COMMAND EXECUTION,
GENERATED CODE, AND AUTOMATED API QUERIES MAY PRODUCE INCORRECT, DESTRUCTIVE,
OR UNPREDICTABLE RESULTS. YOU ARE SOLELY RESPONSIBLE FOR REVIEWING,
SANDBOXING, AND SUPERVISING AUTOMATED ACTIONS AND FOR ANY EXECUTION OR FILE,
SYSTEM, NETWORK, OR ACCOUNT CHANGES THEY MAKE.

This applies to the project's own published security-review records: the Z.ai
Color Team reports are AI-generated, date-specific evidence about the revision
they name. “No finding” means none was found within that report's stated
coverage; it does not mean none exists, and a grade is not a certification.

---

## 3. Prohibited high-risk uses

THE SOFTWARE IS NOT DESIGNED, MANUFACTURED, OR INTENDED FOR USE IN HAZARDOUS
ENVIRONMENTS, FLIGHT NAVIGATION, LIFE-SUPPORT OPERATIONS, MOTOR VEHICLE
CONTROL, INDUSTRIAL CONTROL SYSTEMS, OR ANY MISSION-CRITICAL SETTING WHERE
FAILURE COULD LEAD DIRECTLY TO DEATH, PERSONAL INJURY, SEVERE PHYSICAL DAMAGE,
OR ENVIRONMENTAL DESTRUCTION. SUCH USE IS PROHIBITED.

---

## 4. No financial, legal, tax, or regulatory advice

THE SOFTWARE DOES NOT PROVIDE FINANCIAL, INVESTMENT, LEGAL, TAX, OR PROFESSIONAL
COMPLIANCE ADVICE. YOU ARE SOLELY RESPONSIBLE FOR ENSURING THAT YOUR USE OF THE
SOFTWARE COMPLIES WITH ALL APPLICABLE LAWS, REGULATIONS, SECURITIES LAWS,
SANCTIONS, AND NETWORK PROTOCOL RULES.

Fee guidance, address and transaction observations, and any other output in the
app come from public Bitcoin services and from the app's own scan. They are
informational, they can be stale, and they are not a recommendation to send a
particular amount of money.

---

## 5. Indemnification & hold harmless

TO THE MAXIMUM EXTENT PERMITTED BY LAW, IF YOU HAVE ACCEPTED THESE TERMS, YOU
AGREE TO DEFEND, INDEMNIFY, AND HOLD HARMLESS THE PROTECTED PARTIES AGAINST
THIRD-PARTY CLAIMS, LOSSES, AND REASONABLE LEGAL EXPENSES TO THE EXTENT CAUSED
BY YOUR UNLAWFUL USE OF THE SOFTWARE, YOUR MATERIAL BREACH OF THESE TERMS, OR
YOUR INFRINGEMENT OF A THIRD PARTY'S RIGHTS. THIS DOES NOT REQUIRE YOU TO
INDEMNIFY A PROTECTED PARTY FOR A CLAIM TO THE EXTENT CAUSED BY THAT PARTY'S
OWN NEGLIGENT OR WRONGFUL CONDUCT. THE PROTECTED PARTY MUST GIVE YOU PROMPT
NOTICE OF A CLAIM, REASONABLY COOPERATE AT YOUR EXPENSE, AND ALLOW YOU TO
CONTROL THE DEFENSE; NO SETTLEMENT MAY IMPOSE AN ADMISSION OR OBLIGATION ON A
PROTECTED PARTY WITHOUT ITS WRITTEN CONSENT.

---

## 6. Governing law & jurisdiction

IF THESE TERMS FORM AN ENFORCEABLE AGREEMENT BETWEEN YOU AND BITSEEKER LLC, THAT
AGREEMENT AND ANY DISPUTE, CONTROVERSY, OR CLAIM ARISING OUT OF OR RELATING TO
THE SOFTWARE OR ITS USE SHALL BE GOVERNED BY AND CONSTRUED IN ACCORDANCE WITH
THE LAWS OF THE STATE OF WYOMING, WITHOUT REGARD TO ITS CONFLICT-OF-LAW
PRINCIPLES. SUBJECT TO APPLICABLE LAW, ANY LEGAL SUIT, ACTION, OR PROCEEDING
ARISING OUT OF OR RELATED TO THE SOFTWARE SHALL BE INSTITUTED EXCLUSIVELY IN
THE STATE COURTS LOCATED IN SHERIDAN COUNTY, WYOMING, OR THE UNITED STATES
DISTRICT COURT FOR THE DISTRICT OF WYOMING. TO THE MAXIMUM EXTENT PERMITTED BY
LAW, YOU WAIVE ANY OBJECTION TO THE EXERCISE OF JURISDICTION OVER YOU BY THOSE
COURTS OR TO VENUE IN THOSE COURTS. THIS PROVISION DOES NOT MAKE A CONTRACT
WHERE NO CONTRACT WAS FORMED.

---

## 7. Assumption of risk & user responsibilities

By using the Software, you assume the practical risks described below. Whether
any provision creates a contract depends on the notice, assent, and applicable
law.

1. **You Run This Software Entirely at Your Own Risk:** You assume full and
   sole responsibility for any consequences resulting from the installation,
   configuration, or execution of the Software on your hardware, operating
   system, network, or cloud environment.
2. **No Guarantee of Maintenance or Support:** This is free, open-source
   software. There is no paid support, service-level agreement (SLA),
   maintenance commitment, security patching guarantee, or promise of
   compatibility with future operating system or hardware releases.
3. **Data & System Backups:** You are solely responsible for maintaining
   complete, verified backups of your data, system configurations, credentials,
   and cryptographic keys prior to running any experimental code, system utility,
   or automation script.
4. **Not Professional Advice:** Any telemetry, diagnostics, financial data,
   security evaluations, memory estimates, or analytical outputs produced by the
   Software are strictly informational and do not constitute professional
   engineering, legal, cybersecurity, or financial advice.
5. **System & Hardware Safety:** Tools interacting with system memory, kernel
   parameters, local AI models, network interfaces, cryptographic signing, or
   disk operations may cause high resource utilization, memory pressure, thermal
   throttling, application crashes, or unexpected system restarts. Verify that
   your hardware and environment are suitable before execution.

For Bitcoin Easy Signer, these responsibilities include the following:

- **Verify every transaction yourself.** Check the destination address, the
  amount, the network, the fee, and the change output on your own signing
  devices and in your own wallet software before you approve anything. Many
  signing devices do not display change addresses at all, so check change
  separately.
- **Stop when something is unclear.** If the app and the devices disagree, or if
  you cannot account for every output, do not sign and do not broadcast.
- **Test with an amount you can afford to lose.** A practice-network payment
  does not prove that a mainnet payment is correct.
- **Never enter seed words or private keys.** The app does not need them, does
  not accept them, and must never be asked for them. Anyone who asks for them is
  not this app.
- **Treat signed bytes as spendable.** Signed but not yet broadcast transaction
  bytes can be submitted by anyone who obtains them.
- **Never use the app as the only control over other people's money.** The
  operator of the wallet remains responsible for the wallet's security and for
  every payment the app prepares.

---

## 8. Statutory protections & severability

Where applicable law permits, all warranties are disclaimed to the extent stated
above and in the applicable license. UCC Article 2 governs sales of goods;
whether and how its rules apply to a particular software distribution depends on
the transaction and governing law. This notice does not assume that UCC rules
apply to every software download.

Some jurisdictions do not allow certain warranty disclaimers or liability
limitations. Each provision applies only to the extent permitted by applicable
law. If a provision is held invalid or unenforceable, it shall be severed or
narrowed only as necessary, and the remaining provisions shall remain in effect
to the extent permitted by law.

---

## 9. Third-party trademarks

All third-party product names, logos, brands, and trademarks (including but not
limited to Apple, macOS, Apple Silicon, Metal, Linux, Windows, Docker, and
GitHub) referenced in our repositories are the property of their respective
owners. Use of these names does not imply any affiliation with, sponsorship by,
or endorsement by the respective trademark holders.

---

## 10. Governing open-source license

The root `LICENSE` file identifies the applicable open-source license (the MIT
License, Copyright (c) 2026 Bitseeker LLC). This disclaimer supplements that
license only to the extent the terms are valid and enforceable; it does not
silently add restrictions that conflict with the license. Third-party notices
remain in `THIRD-PARTY-NOTICES.md` and in the notices shipped with each
component.

---

This notice is general information, **not legal advice or a guarantee of
enforceable liability protection**. If Bitcoin Easy Signer will be used to handle
real funds or released for others to do so, have a qualified attorney review the
legal terms and obtain independent security review.
