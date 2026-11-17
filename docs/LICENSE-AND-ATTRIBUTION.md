# License and Attribution Notes

## Upstream project

NucleoOS v0.8.7's `LICENSE` declares **PolyForm Noncommercial License 1.0.0** and identifies the upstream copyright holder as indecenti.

Official license:
https://github.com/indecenti/NucleoOs/blob/v0.8.7/LICENSE

License text:
https://polyformproject.org/licenses/noncommercial/1.0.0/

Do not replace the upstream license with MIT, Apache-2.0, GPL, or another license for copied or derivative upstream code. The upstream license limits permitted purposes to noncommercial purposes and imposes distribution notice requirements.

## Rights split in this repository

Four distinct categories exist here, and they are not licensed alike:

| Category | Files | Position |
|---|---|---|
| 1. Original documentation | `README.md`, `README.zh-CN.md`, `CHANGELOG.md`, `docs/*.md` | Written for this project. No license is granted beyond viewing and quoting with attribution; the author may choose a license later. |
| 2. Original host tools | `tools/otadata_plan.py`, `tools/check_otadata.py`, `tests/descriptor-tests/check_desc.py`, `tests/descriptor-tests/check_devdesc_prop.py` | Written for this project. No license is granted beyond viewing and local reproduction of the documented checks. |
| 3. Derived patch | `patches/full-diff-complete.patch` | Derived from NucleoOS v0.8.7 source. It remains subject to **PolyForm Noncommercial License 1.0.0** and carries the upstream copyright notice below. |
| 4. Third-party components | ESP-IDF, esp_tinyusb, TinyUSB | Not redistributed here. Their own licenses govern them. |

### Derived patch notice

`patches/full-diff-complete.patch` modifies NucleoOS v0.8.7 files:

- `firmware/components/nucleo_usbnet/nucleo_usbnet.c`
- `firmware/components/nucleo_usbnet/include/nucleo_msos20.h`
- `firmware/components/nucleo_usbnet/idf_component.yml`
- `firmware/dependencies.lock`

Upstream copyright: **indecenti / NucleoOS**, licensed under PolyForm Noncommercial License 1.0.0. This repository does not relicense the patch, does not remove the upstream attribution, and does not grant commercial rights. Anyone applying the patch must obtain NucleoOS itself from the upstream repository and comply with the upstream license; the patch alone is not a substitute for the upstream work.

If the intended use of the patch is commercial (including a commercial product or a paid service), obtain permission from the rights holder or professional legal advice first. This document is not legal advice.

## What is not redistributed

- The NucleoOS firmware binary, released or otherwise.
- The NucleoOS source tree.
- Any repackaged upstream release artifact.

`docs/ACCEPTANCE.md` publishes the candidate firmware SHA256 for verification purposes only. A hash is not a distribution of the binary.

## Third-party references

- TinyUSB: https://github.com/hathach/tinyusb
- ESP-IDF: https://github.com/espressif/esp-idf
- Microsoft USB device class drivers: https://learn.microsoft.com/en-us/windows-hardware/drivers/usbcon/supported-usb-classes
- Microsoft OS 2.0 descriptors: https://learn.microsoft.com/en-us/windows-hardware/drivers/usbcon/microsoft-os-2-0-descriptors-specification
- PolyForm Noncommercial 1.0.0: https://polyformproject.org/licenses/noncommercial/1.0.0/

This project is independent and is not affiliated with or endorsed by the upstream maintainers or vendors.
