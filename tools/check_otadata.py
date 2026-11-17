#!/usr/bin/env python3
"""Decode an ESP-IDF otadata image (8 KiB = two 4 KiB record sectors) and report, per record:
offset, ota_seq, state, CRC and CRC validity, plus which OTA slot the bootloader would select.

Read-only: this tool only parses bytes you already have. It never opens a serial port.

CRC convention (ESP-IDF v5.4.4, bootloader_common_ota_select_crc):
    crc = esp_rom_crc32_le(0xFFFFFFFF, &ota_seq, 4)
which in Python is zlib.crc32(struct.pack('<I', seq), 0xFFFFFFFF) -- not plain zlib.crc32().
Real-device anchors: seq=1 -> 0x4743989A, seq=2 -> 0x55F63774.

Usage:
    python check_otadata.py otadata.bin          # or --image otadata.bin
Exit codes: 0 read ok, 3 bad input.
"""
import struct
import sys
import zlib

BASE = 0xF000
SECTOR = 0x1000
ENTRY = 32
NEW, PENDING, VALID, INVALID, ABORTED = 0, 1, 2, 3, 4
NAMES = {NEW: "NEW", PENDING: "PENDING_VERIFY", VALID: "VALID", INVALID: "INVALID",
         ABORTED: "ABORTED"}
SLOTS = (("ota_0", 0x20000), ("ota_1", 0x3A0000))


def crc_of(seq):
    return zlib.crc32(struct.pack("<I", seq), 0xFFFFFFFF) & 0xFFFFFFFF


def decode(buf, i):
    seq, label, state, crc = struct.unpack("<I20sII", buf[i * SECTOR:i * SECTOR + ENTRY])
    return {"index": i, "offset": BASE + i * SECTOR, "seq": seq, "state": state,
            "crc": crc, "crc_ok": crc == crc_of(seq)}


def usable(r):
    return r["seq"] != 0xFFFFFFFF and r["state"] not in (INVALID, ABORTED) and r["crc_ok"]


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        return 3
    buf = open(args[0], "rb").read()
    if len(buf) != 2 * SECTOR:
        print(f"expected {2 * SECTOR} bytes, got {len(buf)}")
        return 3
    recs = [decode(buf, i) for i in range(2)]
    for r in recs:
        print(f"record #{r['index']} @0x{r['offset']:05X}  seq={r['seq']:>10}  "
              f"state={NAMES.get(r['state'], r['state'])}  crc=0x{r['crc']:08X}  "
              f"crc_ok={r['crc_ok']}  usable={usable(r)}")
    ok = [r for r in recs if usable(r)]
    if not ok:
        print("boot: both records unusable -> bootloader falls back to ota_0")
        return 0
    act = max(ok, key=lambda r: (r["seq"], -r["index"]) if False else r["seq"])
    slot = (act["seq"] - 1) % 2
    print(f"boot: record #{act['index']} seq={act['seq']} -> {SLOTS[slot][0]} @0x{SLOTS[slot][1]:05X}")
    other = recs[1 - act["index"]]
    print(f"other record #{other['index']}: usable={usable(other)} (rollback target)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
