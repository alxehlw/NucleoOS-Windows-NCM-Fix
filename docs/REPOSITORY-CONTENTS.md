# Repository contents

This repository publishes the documentation, the sanitized evidence, the exact reviewed source patch, and the SHA256-verified host tools for one Windows 10 CDC-NCM compatibility fix.

It is **not** a firmware distribution and **not** a copy of the NucleoOS source tree.

## What is included

| Path | Content | Provenance |
|---|---|---|
| `README.md` | English project page | Original documentation |
| `README.zh-CN.md` | Chinese project page | Original documentation |
| `CHANGELOG.md` | Publication history of this repository | Original documentation |
| `SHA256SUMS` | Integrity manifest for every file here | Generated from the files in this repository |
| `docs/ROOT-CAUSE-AND-IMPLEMENTATION.md` | Observed failure, compatibility approach, dependency baseline | Original documentation |
| `docs/ACCEPTANCE.md` | A–J acceptance report with per-item PASS / FAIL / NOT_RUN | Original documentation, evidence-backed |
| `docs/OTA-DEPLOYMENT.md` | What was actually written to flash and how OTA selection was handled | Original documentation, evidence-backed |
| `docs/BUILD-GUIDE.md` | Reproducing the build and the descriptor checks | Original documentation |
| `docs/RECOVERY-GUIDE.md` | Returning the device to the original firmware | Original documentation |
| `docs/LICENSE-AND-ATTRIBUTION.md` | Rights split for documentation, tools, patch and third-party components | Original documentation |
| `docs/REPOSITORY-CONTENTS.md` | This file | Original documentation |
| `patches/full-diff-complete.patch` | Exact diff `8a5c6be..a51c571` (4 files, +337/−3) | Exported from the local Git worktree |
| `tools/otadata_plan.py` | OTA record planner / 4 KiB sector generator | Original tool, SHA256 verified |
| `tools/check_otadata.py` | OTA record decoder and boot-selection simulator | Original tool, SHA256 verified |
| `tests/descriptor-tests/results_all.txt` | 66/66 descriptor checks of the final candidate, with per-field assertions | Recorded output of the final linked ELF; re-established against the shipped BIN |
| `tests/descriptor-tests/results_all-bcddevice-0100-superseded.txt` | 65-check run of the pre-`0x0101` build | History only; superseded |
| `tests/descriptor-tests/verification_summary.txt` | Link-symbol table plus partition budget | Produced from the linked ELF and MAP |
| `tests/descriptor-tests/check_desc.py` | Descriptor byte-level checker | Original tool |
| `tests/descriptor-tests/check_devdesc_prop.py` | Device-descriptor property checker | Original tool |
| `tests/descriptor-tests/msos20-bytes-from-elf.txt` | Raw MS OS 2.0 bytes as read from the ELF | Produced from the linked ELF |
| `evidence/g-boot-raw3.log` | Sanitized 43-line startup log capture | Captured over USB Serial/JTAG; sanitized |
| `evidence/g-boot-meta3.txt` | Capture metadata (port, baud, byte count, window) | Captured during the same test |

## What is deliberately not included

- Firmware binaries (`*.bin`). The candidate hash is published in `docs/ACCEPTANCE.md`; the file is not redistributed.
- The full NucleoOS source tree, or any copy of upstream source files.
- `proposal-bcddevice-0101.patch` as a standalone patch: it is already folded into `8a5c6be..a51c571` and does not apply to the base commit. Publishing it as an applicable patch would be misleading; its content is documented in `docs/ROOT-CAUSE-AND-IMPLEMENTATION.md`.
- The earlier `otadata_plan.py` with the wrong CRC convention (`e5db7cde…`). It is superseded and must not be reused.
- Build caches, object files, MAP/ELF artifacts, machine-local paths, credentials, and device-private identifiers.

## Stale artifacts from the earlier investigation

During the work, two files were produced that look like the final deliverables but are not:

- `full-diff-complete.patch` at 18,855 B / `b439e3d2…` — a stale intermediate diff. The authoritative patch here is 19,316 B / `bd1dff95…`, regenerated with `git diff 8a5c6be..a51c571` and byte-identical to the reviewed `final-fix.patch`.
- `proposal-bcddevice-0101.patch` (1,489 B / `4237a8ae…`) — `git apply --check` against `8a5c6be` fails because the change is already in `a51c571`.

Do not substitute either file for the patch published here.

## Verification status

Every file in this repository is listed in `SHA256SUMS`. The patch hash and both tool hashes were compared against the engineering record before upload; no file was rebuilt from prose. Items not covered by that record are documented as original material rather than as engineering-record artifacts.
