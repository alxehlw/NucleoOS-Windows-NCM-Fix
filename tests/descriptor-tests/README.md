# tests/descriptor-tests/

Descriptor verification for the candidate build. Every result here was parsed out of the **linked ELF** or a raw device dump — not from a standalone compile of the header.

## Files

| File | Content |
|---|---|
| `results_all.txt` | The full check output: 65 assertions with per-field detail |
| `verification_summary.txt` | Link-symbol table (address, size, type) and the app-partition budget |
| `msos20-bytes-from-elf.txt` | The MS OS 2.0 descriptor set exactly as read from the ELF |
| `check_desc.py` | Re-parses every MS OS 2.0 field from raw bytes |
| `check_devdesc_prop.py` | Reads the device descriptor out of the ELF and compares it with the esp_tinyusb default |

## The count

65 checks, in three blocks:

| Block | Checks | What it covers |
|---|---|---|
| Device descriptor | 6 | length, `bcdUSB = 0x0210`, and that every other field matches the esp_tinyusb default that would otherwise have been used (VID/PID `303A:4006`, `bcdDevice`, class triple, …) |
| BOS + MS OS 2.0 set | 41 | set header (length, version, index, total length), platform capability UUID `D8DD60DF-4589-4CC7-9CD2-659D9E648A9F`, `dwWindowsVersion 0x06030000`, function subset header, Compatible ID `WINNCM`, `DeviceInterfaceGUIDs` = `{A4115FDC-0B38-4387-A05B-0D97CF458D40}`, vendor request `bmRequestType=0xC0 bRequest=0x01 wValue=0x0000 wIndex=0x0007 wLength=178`, and internal offset/length consistency |
| Configuration descriptor | 18 | total length, interface count, the `interfaces=[(0,0,1,2,13,0),(1,0,0,10,0,1),(1,1,2,10,0,1)]` layout, `endpoints=[129,130,2]` |

An earlier verbal summary said "66 checks". The file says 65, and 6 + 41 + 18 = 65. The summary was corrected to the file; no individual verdict was changed to make a round number.

## Running the checkers

`check_desc.py` takes a hex dump in the format produced during the work:

```
python3 check_desc.py <dump-file>
```

`check_devdesc_prop.py` takes the ELF:

```
python3 check_devdesc_prop.py build/nucleos.elf
```

It needs the `xtensa-esp32s3-elf` toolchain. Set `XTENSA_ESP32S3_PREFIX` to the prefix (everything up to but excluding `objdump`), or have `xtensa-esp32s3-elf-objdump` on `PATH`.

**Publication note:** that one line — a hard-coded toolchain path — was made portable before publication so the file contains no machine-local absolute path. No assertion, threshold, or expected value was altered.

## What the tests do not prove

The checkers validate the descriptor bytes. They do not prove that Windows accepts them, that a driver binds, or that traffic flows. Those are device-and-host facts recorded separately in `docs/ACCEPTANCE.md`.
