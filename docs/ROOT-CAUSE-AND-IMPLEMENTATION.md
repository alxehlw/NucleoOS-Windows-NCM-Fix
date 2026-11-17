# Root Cause and Implementation Notes

## Observed failure

On the tested Windows 10 Pro 22H2 host (Build 19045.6466), the original NucleoOS v0.8.7 USB NCM function enumerated as a USB device, but Windows did not bind an NCM network driver. Device Manager reported Problem Code 28. The device exposed CDC-NCM class compatible IDs but did not expose the Microsoft OS 2.0 compatible ID expected by the installed inbox `usbncm.inf`.

## Compatibility approach

The repair candidate added Microsoft OS 2.0 descriptor support for the NCM function, including:

- BOS Platform Capability advertising the Microsoft OS 2.0 descriptor set.
- A vendor control request serving the descriptor set.
- `WINNCM` as the NCM function's Compatible ID.
- `DeviceInterfaceGUIDs` registry property.
- NCM function subset bound to interface 0.
- `bcdUSB = 0x0210`.
- NCM-mode `bcdDevice = 0x0101` to create a distinct device revision instance after the earlier `REV_0100` enumeration.

The candidate retained VID/PID `303A:4006`, the NCM control/data interface layout, and the existing NCM network data path.

## Tested dependency baseline

- ESP-IDF 5.4.4
- esp_tinyusb 1.7.6~2
- TinyUSB 0.19.0~3

The local branch pinned TinyUSB to the tested version and included a reproducible dependency lock. The original release's exact resolved TinyUSB version remains unconfirmed because the GitHub Actions release log was not readable in the recorded investigation; do not state that the upstream release definitely used 0.21.x.

## Validation

The final firmware report records 66/66 descriptor checks PASS (7 device-descriptor checks, 41 MS OS 2.0 / BOS checks, 18 configuration-descriptor checks), a clean full build, and a real Windows 10 test:

- `USB\MS_COMP_WINNCM` appeared as the first Compatible ID.
- Microsoft `UsbNcm` bound automatically.
- DHCP, route selection, HTTP and PIN pairing passed.

See `ACCEPTANCE.md`.

## Limitations

- One physical Cardputer ADV and one Windows 10 host were tested.
- Windows 11, macOS, and Linux were not part of the recorded final acceptance.
- The exact boot partition offset was not printed in the captured serial log; candidate identity is supported indirectly by the unique `REV_0101` descriptor and OTA record state.
- USB HID repeated-key behavior was observed but not investigated or attributed to this NCM patch.
