# Build guide

How the candidate in this project was built and checked. This is a record of what was done, not a general-purpose flashing tutorial.

## What the patch touches

`patches/full-diff-complete.patch` changes four files under `firmware/`:

| File | Change |
|---|---|
| `components/nucleo_usbnet/idf_component.yml` | New. Pins `espressif/tinyusb` so the solver cannot drift to another generation. |
| `components/nucleo_usbnet/include/nucleo_msos20.h` | New, 219 lines. BOS platform capability + MS OS 2.0 descriptor set + `WINNCM` compatible ID + `DeviceInterfaceGUIDs`. |
| `components/nucleo_usbnet/nucleo_usbnet.c` | +89/−3. `bcdUSB` 0x0210, `bcdDevice` from `NUCLEO_USB_BCD_DEVICE`, BOS callback, vendor control request handler. |
| `dependencies.lock` | +25/−3. Records the same pins for reproducible re-solve. |

## Prerequisites

- ESP-IDF **5.4.4** (this is the version the candidate was built with; do not let the installer pick a newer one silently).
- The `xtensa-esp32s3-elf` toolchain that ships with that IDF version.
- Python 3 for the descriptor checkers.
- NucleoOS v0.8.7 source from the upstream repository. The patch does **not** carry upstream source.

## Steps

1. Obtain NucleoOS at the tested baseline and create a working branch:

   ```
   git clone https://github.com/indecenti/NucleoOs.git
   cd NucleoOs
   git checkout v0.8.7
   git switch -c fix/msos20-winncm
   ```

   The base commit of the recorded work was `8a5c6be` (`release: v0.8.7`).

2. Apply the patch from the repository root:

   ```
   git apply --check /path/to/patches/full-diff-complete.patch
   git apply /path/to/patches/full-diff-complete.patch
   ```

   `git apply --check` is expected to pass against `8a5c6be` and to fail against any other baseline. If it fails on `8a5c6be`, stop: the patch and the checkout do not correspond.

3. Confirm the dependency baseline did not move:

   ```
   grep -A2 "espressif/tinyusb" firmware/dependencies.lock
   grep -A2 "espressif/esp_tinyusb" firmware/dependencies.lock
   grep -A2 "idf:" firmware/dependencies.lock
   ```

   Expected: TinyUSB `0.19.0~3`, esp_tinyusb `1.7.6~2`, IDF `5.4.4`. If a re-solve produces 0.21.x, the environment is wrong — do not "fix" it by accepting the upgrade.

4. Build:

   ```
   cd firmware
   idf.py build
   ```

5. Size and link checks against the app partition (`0x380000` = 3,670,016 B):

   ```
   idf.py size
   idf.py size-components
   ```

   The recorded candidate binary was 3,176,592 B, i.e. inside the partition but not by a wide margin.

6. Verify in the linked ELF, not in a standalone header compile, that the new code is actually linked:

   ```
   xtensa-esp32s3-elf-nm -C build/nucleoos.elf | grep -E "nucleo_bos_desc|nucleo_msos20_set|tud_descriptor_bos_cb|tud_vendor_control_xfer_cb|descriptor_dev_default"
   ```

   The linked image is `build/nucleoos.elf` — that is the name ESP-IDF derives from the project name in `firmware/CMakeLists.txt` (`nucleoos`). There is no `build/nucleos.elf`; if an instruction or script refers to that path, it is wrong.

   `tests/descriptor-tests/verification_summary.txt` records the symbol sizes and addresses from the recorded build: `nucleo_bos_desc` 0x21, `nucleo_msos20_set` 0xb2, plus the two callback symbols in `.text`.

7. Run the byte-level descriptor checks:

   ```
   python3 tests/descriptor-tests/check_desc.py <dump>
   python3 tests/descriptor-tests/check_devdesc_prop.py build/nucleoos.elf
   ```

   `check_desc.py` re-parses every field from a raw hex dump according to Microsoft's MS OS 2.0 specification and shares no assumptions with the C structs. `check_devdesc_prop.py` reads the device descriptor out of the linked ELF and asserts that only `bcdUSB` differs from the esp_tinyusb default. See `tests/descriptor-tests/README.md`.

## Expected numbers

- Descriptor checks: **66 PASS** (7 device-descriptor + 41 MS OS 2.0 / BOS + 18 configuration).
- `bcdUSB` = `0x0210`, `bcdDevice` = `0x0101` in NCM mode, VID/PID `303A:4006` unchanged.
- Configuration layout: `interfaces=[(0,0,1,2,13,0),(1,0,0,10,0,1),(1,1,2,10,0,1)]`, `endpoints=[129,130,2]`.

## Boundaries

- Do not upgrade ESP-IDF, esp_tinyusb, or TinyUSB to make the build succeed.
- Do not replace the patch with a hand-written reconstruction.
- Do not treat a successful `idf.py build` as proof that the descriptors work: the check must run against the linked ELF or a device dump.
