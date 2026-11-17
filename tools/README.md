# tools/

Two host-side tools used to plan and verify the single 4 KiB `otadata` record update. Both are hash-verified against the final execution record; neither was rebuilt from notes.

| File | Size | SHA256 |
|---|---|---|
| `otadata_plan.py` | 15,950 B | `e281b9135c0b3beea915aade218e9e3de4d047576d153066df1df90c10a8badb` |
| `check_otadata.py` | 2,804 B | `eed94eec6465fa2eed3cfadb76160b9523c8f14daf94b2a44e87b27423e9f09d` |

## otadata_plan.py

Decodes the existing `otadata` image, decides which slot the bootloader will pick next, and generates the replacement bytes for **one** 4 KiB record sector — the inactive one. It never emits a whole-partition image.

CRC convention: `zlib.crc32(data, 0xFFFFFFFF)`. This is the convention ESP-IDF's bootloader uses, and it is the one that was wrong in an earlier build of the tool. The corrected build is validated against real-device anchors:

- `seq=1` → `0x4743989A`
- `seq=2` → `0x55F63774`

Self-test result on the record: **16/16 PASS**, including the two anchors above.

## check_otadata.py

Read-only decoder. Given an `otadata` image it prints, for each of the two record sectors, the `ota_seq`, the state, the CRC, whether the CRC matches (testing three CRC conventions side by side), and which slot the bootloader would select.

## Why the hash matters

An earlier build (`e5db7cde…`) computed the CRC with a different initial value and produced records the bootloader would reject as corrupt. It is deliberately not published here. If you obtain `otadata_plan.py` from anywhere else, check the hash before running it, and check that it reproduces both anchors above.

## Usage pattern

The tools do not touch a device. The workflow they support is:

1. Read `otadata` (read-only) into a local file.
2. Back the file up; keep it unchanged.
3. Decode both records with `check_otadata.py`; confirm the active slot and that the other record is still valid.
4. Decide the target slot (the inactive one) and the next `seq`.
5. Generate one sector with `otadata_plan.py`; inspect the reported plan before writing anything.
6. Write a single 4 KiB sector, then read it back and compare byte for byte.

## Boundaries

- Do not use these tools to erase `otadata` or to rewrite the whole partition.
- Do not write the merged `nucleoos-0.8.7.0.bin` to an OTA slot.
- These tools do not flash firmware and are not a substitute for `esptool.py` verification after a write.
