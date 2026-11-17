# NucleoOS Windows 10 USB NCM Compatibility Fix

> Independent compatibility investigation for **M5Stack Cardputer ADV** running **NucleoOS v0.8.7**.

**Status: validated on one physical Windows 10 host. The exact reviewed source patch and the SHA256-verified host tools are included; firmware binaries and upstream source are not redistributed.**

This project documents a real USB CDC-NCM enumeration problem observed on Windows 10 Pro 22H2 (Build 19045.6466), the MS OS 2.0 / `WINNCM` compatibility approach used to address it, and the resulting device-side and host-side validation.

## Result

On the tested Cardputer ADV + Windows 10 setup, the repaired firmware exposed the Microsoft OS 2.0 compatible ID `USB\MS_COMP_WINNCM`. Windows automatically bound its inbox `UsbNcm` driver, obtained an address through DHCP, routed the USB subnet through the NCM interface, and opened the NucleoOS web interface over the USB cable.

No third-party Windows driver was installed. No Windows INF, registry, driver-signing policy, or network-stack settings were modified during the recorded acceptance.

### Verified host/device path

1. USB enumeration exposed `USB\MS_COMP_WINNCM`.
2. Windows bound Microsoft `usbncm.inf` (`UsbNcm` service).
3. Windows obtained `192.168.7.2/24` by DHCP.
4. The `192.168.7.0/24` route used the NCM interface, not the Meta Tunnel interface.
5. `http://192.168.7.1` returned HTTP 200 over the NCM interface.
6. PIN pairing opened the NucleoOS web desktop.

See [the acceptance report](docs/ACCEPTANCE.md) for the full evidence and limitations.

## Scope

This repository is intentionally limited to the Windows 10 CDC-NCM compatibility work:

- Microsoft OS 2.0 / `WINNCM` descriptor integration.
- `bcdUSB = 0x0210` and NCM-mode `bcdDevice = 0x0101`.
- Dependency pinning to the tested ESP-IDF / TinyUSB baseline.
- OTA-safe deployment notes and test evidence.

It does **not** claim to fix unrelated NucleoOS functions. In particular, the USB HID keyboard test enumerated and delivered characters, but a repeated-key defect was observed. That issue is recorded as out of scope and is not attributed to this NCM patch without an upstream-firmware A/B comparison.

## Validation summary

| Area | Result |
|---|---|
| Windows 10 NCM enumeration and `WINNCM` compatible ID | PASS |
| Inbox `UsbNcm` driver binding | PASS |
| DHCP and NCM route | PASS |
| HTTP and PIN pairing | PASS |
| USB Serial/JTAG enumeration and startup log capture | PASS |
| USB MSC directory read | PASS |
| USB MSC write test | NOT RUN (media was writable; no write was attempted) |
| USB HID input | FAIL (repeated `c` after release); outside NCM scope |
| Normal return after USB-Web mode | PASS (UI/device-side) |
| Exact boot partition offset in captured serial log | NOT OBSERVED; candidate identity supported by `REV_0101` and OTA records |

The detailed test matrix is in [docs/ACCEPTANCE.md](docs/ACCEPTANCE.md).

## Repository contents

- `docs/` — root cause, implementation, acceptance, OTA deployment, build and recovery guides.
- `patches/full-diff-complete.patch` — exact diff of the reviewed fix, exported from the local worktree (`8a5c6be..a51c571`, 4 files, +337/−3).
- `tools/` — the two host-side OTA record tools, both SHA256-verified against the engineering record.
- `tests/descriptor-tests/` — descriptor verification results (65 checks) and the checkers that produced them.
- `evidence/` — sanitized serial startup log and capture metadata.
- `SHA256SUMS` — integrity manifest covering every file in this repository.

Firmware binaries and copied upstream source are intentionally not redistributed. See [LICENSE-AND-ATTRIBUTION.md](docs/LICENSE-AND-ATTRIBUTION.md).

## Tested configuration

- Device: M5Stack Cardputer ADV / ESP32-S3 / Stamp-S3A
- Firmware base: NucleoOS v0.8.7
- Candidate revision: `bcdUSB 0x0210`, `bcdDevice 0x0101`
- VID/PID: `303A:4006`
- ESP-IDF: 5.4.4
- `esp_tinyusb`: 1.7.6~2
- TinyUSB: 0.19.0~3
- Host: Windows 10 Pro 22H2, Build 19045.6466

These results are from one physical device and one Windows host. They are not a blanket compatibility guarantee for all Windows builds, Cardputer variants, or other operating systems.

## Upstream

- NucleoOS: https://github.com/indecenti/NucleoOs
- Tested upstream tag: `v0.8.7`
- TinyUSB: https://github.com/hathach/tinyusb
- Microsoft USB device class driver documentation: https://learn.microsoft.com/en-us/windows-hardware/drivers/usbcon/supported-usb-classes

This is an independent community project and is not affiliated with or endorsed by M5Stack, the NucleoOS maintainer, Microsoft, Espressif, or TinyUSB.

## License and redistribution

NucleoOS v0.8.7 declares **PolyForm Noncommercial License 1.0.0**. Do not assume that upstream source, derivative patches, or firmware binaries may be relicensed under MIT/Apache/GPL. Review the upstream license and required notices before publishing derivative source or binaries.

This bootstrap repository deliberately does not include the NucleoOS firmware binary or copied upstream source. A separate license decision is still required for original tools and documentation authored for this project. See [LICENSE-AND-ATTRIBUTION.md](docs/LICENSE-AND-ATTRIBUTION.md).

## Publication status

This repository publishes documentation, evidence, the exact source patch, and the verified host tools. It is **not** a firmware release: no binary is distributed and no upstream source tree is copied.

Before tagging `v1.0.0`:

1. Rebuild from a clean NucleoOS v0.8.7 checkout with the patch applied and confirm the recorded descriptor results.
2. Confirm the license position for the derived patch (see [LICENSE-AND-ATTRIBUTION.md](docs/LICENSE-AND-ATTRIBUTION.md)).
3. Re-check that no private identifiers or machine-local paths were introduced.
4. Decide whether the HID repeated-key observation is worth an upstream report — it is outside this project's scope.
