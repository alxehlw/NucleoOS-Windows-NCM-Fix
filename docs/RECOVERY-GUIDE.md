# Recovery guide — returning the device to the original v0.8.7 firmware

**Status: documented procedure. Recovery was not executed during this project and is not claimed as tested.** It is derived from the same single-sector OTA rule that was used and verified in the forward deployment (see `OTA-DEPLOYMENT.md`).

## The layout this assumes

| Slot | Offset | Size | Content at hand-off |
|---|---|---|---|
| `ota_0` | `0x20000` | 0x380000 | original NucleoOS v0.8.7, record `seq=1 / VALID` |
| `ota_1` | `0x3A0000` | 0x380000 | candidate fix, record `seq=2 / VALID` |
| `otadata` record 0 | `0x0F000` | 4 KiB | original boot record — untouched throughout |
| `otadata` record 1 | `0x10000` | 4 KiB | candidate boot record |

Two records exist, each in its own 4 KiB sector. Only the non-active sector was ever rewritten. `0x0F000` was verified byte-identical after the forward flash.

## Two ways back

### A. Let the bootloader roll back (no writes)

If the candidate is not confirmed healthy, ESP-IDF's rollback path returns the device to the last record marked `VALID`. That only applies while the candidate is still `PENDING_VERIFY`; once the candidate has been confirmed `VALID`, rollback no longer triggers. Check the current state first:

```
python3 tools/check_otadata.py --image otadata-before.bin
```

This is read-only and prints each record's `seq`, state, CRC, and which slot the bootloader would pick.

### B. Replace the candidate with the official app-only image (same slot, same rule)

Use this when the candidate has already been confirmed `VALID` and you want the original firmware back.

1. **Read and back up `otadata` before anything else.** Dump `0xF000` and `0x10000`, keep the bytes, and decode both records with `check_otadata.py`. If you cannot decode them, stop.

2. **Get the official image and verify it against the official manifest.** The app-only asset is `nucleoos-0.8.7.0-ota.bin`; its SHA256 must match the upstream release's `SHA256SUMS`. The merged asset `nucleoos-0.8.7.0.bin` is for a full `0x0` write and must never be written to `0x20000` or `0x3A0000`.

3. **Write the official app-only image into `ota_1 @ 0x3A0000`** — the slot the candidate occupies. Do not touch `ota_0 @ 0x20000`, which still holds the original.

4. **Read back and compare the SHA256** of the written region with the official manifest value. Mismatch means stop.

5. **Generate exactly one new 4 KiB record sector** with `otadata_plan.py`, targeting the *inactive* record sector, `seq = previous + 1`, state `NEW (0)`, CRC computed as `zlib.crc32(data, 0xFFFFFFFF)`. Validate the plan against the real-device anchors before writing:

   - `seq=1` → CRC `0x4743989A`
   - `seq=2` → CRC `0x55F63774`

   If the tool cannot reproduce both anchors from your backed-up image, do not write.

6. **Write only that 4 KiB sector.** Then read `0x10000` back and compare byte for byte with the plan, and read `0x0F000` to confirm the original record is unchanged.

7. Boot and confirm the original firmware starts and behaves as v0.8.7 did before the fix — which means the NCM function will again fail to bind on Windows 10. That is the expected outcome, not a regression.

## Hard rules

- Never `erase_otadata`, and never clear the whole `0xF000–0x11000` range.
- Never write the merged image to an OTA slot.
- Never rewrite both records in one operation: the second valid record is the thing that makes a power loss survivable.
- Never change the partition table to make a recovery path work.
- Never accept a tool whose CRC convention you have not checked against the real-device anchors.

## What is not covered

- Recovery after a corrupted `otadata` (both records unreadable). That needs a full `0x0` restore of the official merged image, which rewrites NVS, PHY, and NVS-key sectors. It is **not** a lossless rollback and is out of scope here.
- Recovery on a device whose partition table was already modified.
