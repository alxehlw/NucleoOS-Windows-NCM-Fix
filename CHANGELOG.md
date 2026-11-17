# Changelog

All dates are the engineering dates of this project, not upstream release dates.

## [Evidence revision] — 2026-11-17

Scope: evidence and documentation only. No firmware source, patch, OTA tool or device was touched; no release, tag, upstream issue or pull request was created.

### Fixed

- `tests/descriptor-tests/results_all.txt` was the **pre-`0x0101` run**: it still showed the `bcdDevice 0x0100` device descriptor and 6 device-descriptor checks. It is now the recorded raw output of the final candidate (7 device-descriptor + 41 BOS/MS OS 2.0 + 18 configuration = **66 checks, 0 FAIL**). The superseded run is preserved as `results_all-bcddevice-0100-superseded.txt` and marked as history.
- `tests/descriptor-tests/verification_summary.txt`: `bin_size_bytes` (3,176,592) and `bin_sha256` (`05cf2658…6e6a`) were empty placeholders; both are now filled, together with the final ELF hash, image size, headroom and the symbol-to-binary offset mapping.
- `docs/BUILD-GUIDE.md` referred to `build/nucleos.elf`; the actual ESP-IDF output is `build/nucleoos.elf` (project name `nucleoos`). Both occurrences are corrected and the name is explained.
- Counts unified: `README.md`, `README.zh-CN.md`, `tests/descriptor-tests/README.md`, `docs/BUILD-GUIDE.md`, `docs/ROOT-CAUSE-AND-IMPLEMENTATION.md`, `docs/REPOSITORY-CONTENTS.md` now all state **66** (7 + 41 + 18), matching the checker.

### Evidence basis

The final linked ELF (`c27962647b03d31c52ab96164e288ed5aa52f959dcd47e748281bfc3adc0c216`) is no longer retained, so its 14:51 raw output is published verbatim rather than re-derived. It was re-established against the shipped candidate binary (`05cf2658…`, 3,176,592 B, not redistributed): device descriptor at `0x752ec` = `bcdUSB 0x0210` / `bcdDevice 0x0101` / VID:PID `303A:4006`; BOS and MS OS 2.0 blobs byte-identical to the ELF-time dumps (`check_desc.py` → 41/41 PASS); configuration descriptor byte-identical to the pre-`0x0101` build that scored 18/18; symbol addresses map to binary offsets by the constant `0x3c250000`. Nothing was inferred to reach 66.

### Known gap (unchanged)

A full clean-room rebuild was started for this revision and stopped: on the 2-core build host it projects to well over an hour, and a fresh ELF would carry a new hash that is not the candidate artifact. The numbers above therefore rest on the recorded final-build output plus the byte-level re-check of the shipped binary, not on a rebuilt ELF.

## [Unreleased] — publication of the initial public project

### Added

- `README.md` (English, default GitHub page) and `README.zh-CN.md` (Chinese) describing the observed Windows 10 failure, the Microsoft OS 2.0 approach, and the tested limits.
- `docs/ROOT-CAUSE-AND-IMPLEMENTATION.md`, `docs/ACCEPTANCE.md`, `docs/OTA-DEPLOYMENT.md`, `docs/BUILD-GUIDE.md`, `docs/RECOVERY-GUIDE.md`, `docs/REPOSITORY-CONTENTS.md`, `docs/LICENSE-AND-ATTRIBUTION.md`.
- `patches/full-diff-complete.patch` — exact diff `8a5c6be..a51c571`, 4 files, +337/−3, 19,316 B, SHA256 `bd1dff9568885aa4374e318f3a0a0a09b0c158b986894f0dc73db03dec66db61`. Exported with `git diff` from the local worktree; byte-identical to the reviewed `final-fix.patch`.
- `tools/otadata_plan.py` (15,950 B, SHA256 `e281b9135c0b3beea915aade218e9e3de4d047576d153066df1df90c10a8badb`) and `tools/check_otadata.py` (2,804 B, SHA256 `eed94eec6465fa2eed3cfadb76160b9523c8f14daf94b2a44e87b27423e9f09d`), both matching the final execution record.
- `tests/descriptor-tests/` — the 66/66 descriptor results (7 device-descriptor + 41 MS OS 2.0 + 18 configuration checks), the link-symbol summary, the raw MS OS 2.0 bytes, and the two checkers.
- `evidence/g-boot-raw3.log` (3,248 B, 43 lines) and `evidence/g-boot-meta3.txt`, sanitized.
- `SHA256SUMS` covering every published file.

### Changed

- Descriptor-check total: an earlier verbal "66" was first reconciled downward to **65** against `results_all.txt`, which turned out to be a run of a pre-`bcdDevice 0x0101` build (6 + 41 + 18). The final-candidate run is **66** (7 + 41 + 18); see the evidence-revision entry below. No individual verdict was ever changed.
- A–J summary corrected to **9 PASS / 1 FAIL / 1 NOT_RUN sub-item** (G counts as PASS because all three of its sub-items passed; H's write test is a separate NOT_RUN sub-item and is not folded into the PASS total).
- `docs/OTA-DEPLOYMENT.md`: the earlier note "tool excluded because its hash does not match" is replaced by the verified inclusion of both tools; the superseded `e5db7cde…` build is explicitly excluded.
- `tests/descriptor-tests/check_devdesc_prop.py`: the hard-coded toolchain path was made portable (`XTENSA_ESP32S3_PREFIX` or `PATH`). This is the only source edit applied for publication; it changes no assertion.

### Not included

- Candidate firmware binary (`05cf26580fc324e3c4985c27a61f876769add1d8b534b9bf42f1e71e6dbe6e6a`, 3,176,592 B). Hash published, file withheld.
- Upstream NucleoOS source tree.
- `proposal-bcddevice-0101.patch` as a standalone patch: folded into `a51c571`, does not apply to `8a5c6be`.
- Stale intermediate diff `b439e3d2…` / 18,855 B.

### Verified in this repository

- Patch hash matches the engineering record byte for byte.
- Both tool hashes match the engineering record.
- Descriptor result file parses to 66 PASS, 0 FAIL.
- No machine-local absolute paths, credentials, or device MAC remain in the published tree.

### Not verified in this repository

- A clean-room rebuild from a fresh NucleoOS v0.8.7 checkout was **not** performed during publication. The build and descriptor results come from the original engineering worktree.

## Test basis

- Hardware: M5Stack Cardputer ADV (ESP32-S3 / Stamp-S3A), one unit.
- Host: Windows 10 Pro 22H2, Build 19045.6466, one host.
- Firmware baseline: NucleoOS v0.8.7 (`8a5c6be`), candidate commit `a51c571`.
- Dependencies: ESP-IDF 5.4.4, esp_tinyusb 1.7.6~2, TinyUSB 0.19.0~3.
