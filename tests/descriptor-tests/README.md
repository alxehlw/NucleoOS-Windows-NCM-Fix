# tests/descriptor-tests/

Descriptor verification for the candidate build. Every result here was parsed out of the **linked ELF** or a raw device dump — not from a standalone compile of the header.

## Files

| File | Content |
|---|---|
| `results_all.txt` | The full check output of the final candidate: 66 assertions with per-field detail |
| `results_all-bcddevice-0100-superseded.txt` | The earlier run of the pre-`0x0101` build (65 assertions). History only — not the result of the final firmware |
| `verification_summary.txt` | Link-symbol table (address, size, type), the firmware size/hash, and the app-partition budget |
| `msos20-bytes-from-elf.txt` | The MS OS 2.0 descriptor set exactly as read from the ELF |
| `check_desc.py` | Re-parses every MS OS 2.0 field from raw bytes |
| `check_devdesc_prop.py` | Reads the device descriptor out of the ELF and compares it with the esp_tinyusb default |

## The count

66 checks, in three blocks:

| Block | Checks | What it covers |
|---|---|---|
| Device descriptor | 7 | length, `bcdUSB = 0x0210`, `bcdDevice = 0x0101`, and that every other field matches the esp_tinyusb default that would otherwise have been used (VID/PID `303A:4006`, class triple, …) |
| BOS + MS OS 2.0 set | 41 | set header (length, version, index, total length), platform capability UUID `D8DD60DF-4589-4CC7-9CD2-659D9E648A9F`, `dwWindowsVersion 0x06030000`, function subset header, Compatible ID `WINNCM`, `DeviceInterfaceGUIDs` = `{A4115FDC-0B38-4387-A05B-0D97CF458D40}`, vendor request `bmRequestType=0xC0 bRequest=0x01 wValue=0x0000 wIndex=0x0007 wLength=178`, and internal offset/length consistency |
| Configuration descriptor | 18 | total length, interface count, the `interfaces=[(0,0,1,2,13,0),(1,0,0,10,0,1),(1,1,2,10,0,1)]` layout, `endpoints=[129,130,2]` |

7 + 41 + 18 = 66. The two totals that appear in this repository's history are now reconciled:

- **65** was the run against the earlier build whose descriptor still carried `bcdDevice 0x0100`, checked by the 6-assertion version of the device-descriptor checker. That run is preserved as `results_all-bcddevice-0100-superseded.txt`.
- **66** is the final candidate: the current `check_devdesc_prop.py` adds the `bcdDevice reports revision 0x0101` assertion, so the device-descriptor block has 7 checks. Difference is one added assertion, not a changed verdict.

No verdict was altered to reach either number: each file is the raw output of the checker version that produced it.

## Provenance of the final-candidate output

`results_all.txt` is the recorded raw output of the final linked ELF, captured 2026-11-17 14:51:

- ELF path at capture time: `firmware/build/nucleoos.elf`, SHA256 `c27962647b03d31c52ab96164e288ed5aa52f959dcd47e748281bfc3adc0c216`.
- The build tree was removed afterwards, so the ELF itself is **not** retained in this repository.
- The output was re-established against the shipped candidate binary (`05cf26580fc324e3c4985c27a61f876769add1d8b534b9bf42f1e71e6dbe6e6a`, 3,176,592 B, not redistributed): the device descriptor at file offset `0x752ec` reads `12 01 10 02 00 00 00 40 3a 30 06 40 01 01 01 02 03 01` (bcdUSB `0x0210`, bcdDevice `0x0101`, VID/PID `303A:4006`); the BOS (33 B) and MS OS 2.0 (178 B) blobs are byte-identical to the dumps in `msos20-bytes-from-elf.txt`, and `check_desc.py` re-run on those bytes gives 41/41 PASS; the configuration descriptor (94 B) is byte-identical to the pre-`0x0101` linked build that scored 18/18. Every symbol address maps to its binary offset by the constant `0x3c250000`.

## Running the checkers

`check_desc.py` takes a hex dump in the format produced during the work:

```
python3 check_desc.py <dump-file>
```

`check_devdesc_prop.py` takes the ELF:

```
python3 check_devdesc_prop.py build/nucleoos.elf
```

It needs the `xtensa-esp32s3-elf` toolchain. Set `XTENSA_ESP32S3_PREFIX` to the prefix (everything up to but excluding `objdump`), or have `xtensa-esp32s3-elf-objdump` on `PATH`.

**Publication note:** that one line — a hard-coded toolchain path — was made portable before publication so the file contains no machine-local absolute path. No assertion, threshold, or expected value was altered.

## What the tests do not prove

The checkers validate the descriptor bytes. They do not prove that Windows accepts them, that a driver binds, or that traffic flows. Those are device-and-host facts recorded separately in `docs/ACCEPTANCE.md`.
