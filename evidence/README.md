# evidence/

Sanitized captures from the real-device G test (USB Serial/JTAG).

| File | Size | Content |
|---|---|---|
| `g-boot-raw3.log` | 3,248 B | 43 lines of startup log, from `BOOTSTEP boot-start` through the last reported step `pre-app-run` |
| `g-boot-meta3.txt` | 307 B | Capture metadata: window, port, baud, and open/read errors |

## Capture conditions

- Port opened with DTR and RTS driven low so the capture itself would not reset the device.
- Baud 115200, capture started **before** the operator pressed RST.
- Window: 18:11:09 → 18:15:09 (4 minutes), with an automatic reconnect after a read error.
- Boot to screensaver: 65.40 s, according to the log's own timestamps.
- No panic, abort, or watchdog reset in the captured window.

## Sanitization

- The USB serial number in the metadata file is replaced with `[REDACTED]`.
- No device MAC address appears in either file; this was checked by search before publication.
- No host paths, usernames, or machine names appear.

## What the log shows, and what it does not

Shows: the boot sequence reached application start without a panic, and the controlled-degradation path is visible — a single `oom: alloc fail: 32404 B` line followed immediately by `canvas fitted to 240x130`, i.e. the canvas fell back to a smaller size instead of aborting.

Does **not** show the partition the application was loaded from. The log never printed `Loaded app from partition at offset`, so the boot partition offset is recorded as **NOT OBSERVED** rather than inferred. Candidate identity is supported only indirectly, by the unique `REV_0101` descriptor reported by Windows and by the `seq=2 / VALID` OTA record.

Do not cite this file as evidence of the boot slot. It is evidence of a clean boot and of the degradation behavior.
