# G2c desktop evidence — host-only, opt-in, experimental

This procedure belongs to issue #3 and draft PR #30. It is not a boot
certificate, a protection proof or an automatic Wanderer detector.

## Preconditions

- Read root `AGENTS.md` and the accepted ADR-0002 before changing this flow.
- Keep the tested baseline pinned until G1/G2 have been independently rerun.
- Obtain a real G1 ISO and its sibling `build-manifest.txt` from the
  reference build harness in draft PR #24. The ISO's path, SHA-256 and source
  SHA must match the manifest exactly.
- Install `qemu-system-x86_64` on the execution host.
- Use a **new** absolute result directory; the runner refuses overwrite.
- This path is manual only. Do not add a scheduled or push-triggered QEMU build.

## Bounded diagnostic observation (not G2c)

```sh
python3 scripts/nexus/baseline/run-desktop-observation.py \
  /absolute/path/to/aros-pc-x86_64.iso \
  /absolute/path/to/new-g2c-result \
  120
```

The runner uses one x86-64 TCG vCPU, 1024 MiB RAM, no guest network and a
120-second observation window by default (allowed range: 10–600 seconds).
It records the source and ISO hashes, QEMU identity, serial log and run status. The ISO is hashed again after the guest window: if the bytes changed, the runner writes `FINAL_STATUS=iso-changed-unverified`, preserves both `ISO_SHA256` and `ISO_SHA256_AFTER`, and refuses to capture desktop evidence.
If the VM is still alive and its HMP monitor is available, it attempts a
framebuffer dump into `desktop-observation.ppm` and binds its SHA-256 to
`desktop-observation.txt` and `run-manifest.txt`.

The capture validator accepts only QEMU's canonical P6 format with an exact
pixel count and a 16 MiB total limit. A blank screen, boot splash, or any other
framebuffer content can be **captured**; it cannot be called Wanderer solely
because the PPM file is valid.

If QEMU exits early, times out without a valid capture, or produces malformed
data, preserve the partial result directory and the serial log. Do not
rewrite the run status to imply a successful boot.

## Opt-in local interactive observation (still not G2c PASS)

Use a local UNIX-domain VNC socket only. This is a deliberate opt-in, not
enabled by the default diagnostic command. It does not expose TCP VNC or
guest networking. QEMU's documented `-vnc unix:<socket-path>` syntax is
used; the new result directory is created with mode 0700 and both UNIX
sockets are removed when the bounded guest exits.

```sh
python3 scripts/nexus/baseline/run-desktop-observation.py \
  /absolute/path/to/aros-pc-x86_64.iso \
  /short/absolute/new-g2c-interactive \
  300 --interactive
```

During the 300-second window, connect a UNIX-socket-capable viewer on
the same host (for example, TigerVNC):

```sh
vncviewer /short/absolute/new-g2c-interactive/vnc.sock
```

Use a short result path without spaces or shell/HMP metacharacters: UNIX
socket paths longer than 100 bytes, or paths unsafe for HMP, are rejected
before QEMU starts. Do not relay this unauthenticated socket
over the internet or add TCP forwarding. A reviewer should open and close
a Wanderer drawer and observe an actual input response *before* the
runner's timeout. The final screenshot is captured from that same guest
after the interaction window. Preserve serial log, run manifest, machine
capture and screenshot; the run manifest records
`INTERACTIVE_MODE=unix-vnc`.

A headless run records `INTERACTIVE_MODE=none` and **cannot** pass the
human G2c verifier. An early QEMU exit is also rejected. Neither the
existence of a VNC socket nor the manifest field proves that a human
connected or interacted: the subsequent human assertion remains mandatory.

## Independent human gate

**Current blocker:** no actual interactive Wanderer run and independent
human input-response confirmation have been recorded. The opt-in VNC
mode makes such a same-run observation possible but does not establish
it automatically. A screenshot cannot establish that Wanderer is usable.
Do **not** produce a positive G2c claim from a headless capture, a boot
splash, or an unreviewed VNC session.

Once that same-run interaction is possible and observed, a human may create
`desktop-evidence.txt` in the same result directory. Its required fields
are shown below; replace the placeholder hashes and timestamp with the
actual values, and use the reviewer identity of the person who interacted
with the VM:

```text
FORMAT=nexus-desktop-evidence-v1
RUN_MANIFEST_SHA256=<sha256 of run-manifest.txt>
SOURCE_SHA=<SOURCE_SHA from run-manifest.txt>
ISO_SHA256=<ISO_SHA256 from run-manifest.txt>
VISUAL_RESULT=wanderer-usable
HUMAN_VERIFIED=yes
REVIEWER=<human reviewer>
REVIEWED_UTC=<YYYY-MM-DDTHH:MM:SSZ, not before CAPTURED_UTC>
SCREENSHOT=desktop-observation.ppm
SCREENSHOT_SHA256=<sha256 of desktop-observation.ppm>
```

Then validate the package:

```sh
python3 scripts/nexus/baseline/verify-desktop-evidence.py \
  /absolute/path/to/new-g2c-result
```

The verifier requires `desktop-observation.txt` to bind the same run
manifest and screenshot, requires `INTERACTIVE_MODE=unix-vnc` with a
live-guest timeout, and requires human review after capture. It requires matching pre/post-run ISO hashes, including the post-run field, and rejects
missing, symlinked, truncated, overlong, noncanonical or rehashed-unbound
evidence. The reviewer identity is a **self-assertion**, not a cryptographic
signature. A successful verifier result means only that the supplied human
assertion is structurally consistent with the capture package.

## Evidence and gates

- **E1:** Python syntax and GitHub workflow policy checks.
- **E2:** parser/capture/verifier adversarial tests.
- **E3:** full host runner + HMP capture lifecycle exercised with a synthetic UNIX-socket QEMU substitute in CI (not AROS boot integration).
- **E4:** pending real deterministic QEMU G2b/G2c observation.
- **H0:** host evidence tooling; **human visual + interaction review**
  still mandatory before a G2c usability claim.
- **H1/H2/H3:** not exercised by this host-only change.
- **L0–L5:** no Nexus runtime isolation property is demonstrated.
- **U:** AROS boot/Exec/DOS/Wanderer. **N:** Nexus host evidence tools.
  **A:** none. **B0–B3:** not applicable. Machine privilege remains
  legacy-owned.

## Three reviews and stop conditions

1. **Construction:** parser is bounded and fail-closed; evidence is never
   overwritten; QEMU remains a diagnostic process.
2. **Integration:** compare with the current upstream head and tested
   baseline; no kernel, ABI, SMP or device authority changes; run host CI.
3. **Evidence Red Team:** attempt ISO mutation during a live synthetic guest, forged, missing, duplicate, rehashed,
   truncated and mismatched screenshot/manifest packages, and a review
   timestamp earlier than capture. Re-run tests after any parser change.

**NO TEST, EXPLAIN WHY:** this host-only PR cannot demonstrate a responsive
Wanderer without a real G1-bound ISO, a QEMU run with the interactive
viewer and a separate human observation. Strongest remaining false-positive scenario: a reviewer signs a
perfectly hash-consistent boot splash as "usable Wanderer". The required
next evidence is a real G1-bound QEMU session with interactive same-run
input, independent human observation and the preserved capture chain.

Do not merge this draft as a completed G2c milestone or advance BASELINE.md
until the missing evidence and relevant reviews exist.

## Capture-window provenance red team (2026-10-28)

**Goal:** prevent a screenshot from being retained as usable evidence if either the
G1 ISO or its build manifest changes between the first provenance check and
completion of the HMP capture. **Non-goals:** proving guest boot, proving a
human actually used Wanderer, defending against a malicious host or TOCTOU
changes after the final hash check.

**Preconditions:** successful SHA-bound G1 artifact, fixed source SHA, local
QEMU, bounded observation. **Ownership:** U = AROS boot and desktop; N = host
capture/provenance tooling; A = none. B0-B3 not applicable; hardware authority
remains legacy-owned. No L0-L5 security claim.

**Acceptance:** ISO and G1 manifest remain byte-identical across capture;
otherwise the runner returns nonzero, removes both PPM and observation manifest,
and records `POST_CAPTURE_PROVENANCE=changed` in the run manifest.

**Negative evidence:** fake QEMU changes the ISO or build manifest while
handling `screendump`; both must be rejected. Tests are host integration E3,
not a real AROS QEMU E4 run. **Human gate:** H0 for host tooling. No hardware
H2 requirement for this host-only property; G2c still requires a real QEMU
session and human desktop review.

**Review 1 — Construction:** post-capture hash check and fail-closed deletion;
no new kernel/ABI code. **Review 2 — Integration:** same opt-in runner and
existing synthetic HMP integration path, no automatic ISO retention or
baseline promotion; latest upstream remains independent. **Review 3 — Red
Team:** ISO and manifest mutation during screendump. Residual risks include
host compromise, deliberate human misrepresentation, and a change after the
final check; none of these can be excluded by the present tests.

**Stop:** no merge while required CI is failing, no G2c PASS without actual
Wanderer interaction, and no Phase 1 kernel implementation without Phase 0
exit evidence. Logical integrator: Frapo78 on `nexus/g2-desktop-evidence`.

## Shutdown-bound provenance gate (2026-10-29)

**Goal:** a QEMU process must not be able to change the ISO or G1 manifest
after the final evidence hash and before process shutdown. **Non-goals:**
host compromise resistance, automated Wanderer recognition, or any L0-L5
isolation proof. **Preconditions:** the same SHA-bound G1 ISO and bounded,
manual QEMU observation used above. **Owner:** N host tooling; U guest AROS;
A none; B0-B3 not applicable; machine authority legacy-owned. Integrator:
Frapo78, issue #3, draft PR #30.

**Acceptance:** capture while the guest is alive, stop/reap QEMU, then
re-hash both ISO and G1 manifest. A mutation during capture **or shutdown**
must return failure, delete both observation files and retain a run manifest
marked `POST_CAPTURE_PROVENANCE=changed`. The human G2c verifier must
reject that marker even if someone reconstructs and re-hashes an otherwise
internally consistent screenshot/manifest package.

**Negative tests:** a fake QEMU changes the ISO on SIGTERM; a second
synthetic attack modifies the G1 manifest during HMP capture; a forged
package rebinds all hashes despite the explicit provenance failure marker.
These are E2/E3 host-only tests, not a real AROS E4 run. Required human
evidence for G2c remains a live same-run interaction with Wanderer.
H0 applies to the tooling; no H1/H2/H3 or L0-L5 claim is advanced.

**Review 1:** check lifecycle cleanup, kill fallback and hash ordering.
**Review 2:** check Linux/macOS host portability, existing G1 manifest
compatibility, no kernel/ABI changes, and latest upstream. **Review 3:**
test mutation during capture, mutation on shutdown, and forged/rehashed
post-failure packages. **Stop conditions:** any failed CI, missing real
QEMU ISO, or absent human interaction keeps the PR draft and G2c blocked.

## G1 symlink provenance preflight (2026-10-29)

**Goal:** reject redirectable ISO and sibling G1 manifest paths before
launching QEMU. **Non-goals:** hostile-host filesystem isolation, atomic
snapshotting, boot or Wanderer verification. **Preconditions:** ordinary
SHA-bound G1 files; a new observation directory.

**Ownership:** U = AROS runtime; N = host runner and adversarial tests;
A = none; B0-B3 not applicable. All CR3/IRQ/MMIO/DMA and device authority
remain legacy-owned. No L0-L5 isolation claim.

**Acceptance:** symlinked ISO or `build-manifest.txt` raises an error before
creating an output directory or launching QEMU. **Negative tests:** replace
either G1 input with a symlink to otherwise valid bytes; both must fail.
Required automated evidence: focused runner tests in CI (E2); real QEMU E4
and a human Wanderer interaction are separate outstanding G2c gates.
Human gate H0 for this host-only tooling; H1/H2/H3 not invoked.

**Review 1 — Construction:** early input validation before hashing and process
creation; no ABI, kernel, or guest changes. **Review 2 — Integration:** existing
G1 manifest fields and QEMU invocation unchanged; upstream ownership intact.
**Review 3 — Evidence Red Team:** both symlinked input cases; the strongest
remaining attack is a malicious host swapping regular files between checks.
The host cannot be treated as a hostile security boundary; a future test would
need an atomic input snapshot or file-descriptor-based provenance protocol.

**Stop:** CI must be green before merge; no G2c acceptance without actual
QEMU/Wanderer and human observation. Integrator: Frapo78; branch:
`nexus/g2-desktop-evidence`.
