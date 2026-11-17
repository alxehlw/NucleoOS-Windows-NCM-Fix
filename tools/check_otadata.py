#!/usr/bin/env python3
"""Decode the ESP-IDF otadata region and report which OTA slot boots.

Usage:
    python check_otadata.py otadata.bin      # dumped with: esptool read_flash 0xF000 0x2000 otadata.bin

Rules mirrored from ESP-IDF 5.4.4:
  * esp_ota_select_entry_t = ota_seq(u32) + seq_label[20] + ota_state(u32) + crc(u32)
  * crc = crc32_le(0xFFFFFFFF, &ota_seq, 4)      (bootloader_common_ota_select_crc)
  * bootloader_common_select_otadata(max=true) picks the higher ota_seq; if neither entry is
    valid the bootloader falls back to the first OTA partition (ota_0).
  * slot index = (ota_seq - 1) % number_of_ota_slots   -> 1 = ota_0 @0x20000, 2 = ota_1 @0x3A0000
"""
import sys
import zlib

SLOTS = {1: ("ota_0", "0x00020000"), 2: ("ota_1", "0x003A0000")}
ENTRY_SIZE = 32
SECTOR = 0x1000                      # the two records sit at the BASE of each 4 KiB sector
STATES = {0: "NEW", 1: "PENDING_VERIFY", 2: "VALID", 3: "INVALID", 4: "ABORTED"}


def crc_variants(seq_bytes):
    crc = 0xFFFFFFFF
    for b in seq_bytes:
        crc ^= b
        for _ in range(8):
            crc = (crc >> 1) ^ (0xEDB88320 if crc & 1 else 0)
    return {
        "zlib(init0)": zlib.crc32(seq_bytes) & 0xFFFFFFFF,
        "zlib(init0xFFFFFFFF)": zlib.crc32(seq_bytes, 0xFFFFFFFF) & 0xFFFFFFFF,
        "rom(init0xFFFFFFFF,no-xor)": crc & 0xFFFFFFFF,
    }


def decode(blob):
    entries = []
    for i in range(2):
        off = i * SECTOR                      # 0x0000 and 0x1000, NOT 0x0000 and 0x0020
        raw = blob[off:off + ENTRY_SIZE]
        if len(raw) < ENTRY_SIZE:
            entries.append(None)
            continue
        seq = int.from_bytes(raw[0:4], "little")
        state = int.from_bytes(raw[24:28], "little")
        crc = int.from_bytes(raw[28:32], "little")
        blank = raw == b"\xff" * ENTRY_SIZE
        match = [k for k, v in crc_variants(raw[0:4]).items() if v == crc]
        invalid = seq == 0xFFFFFFFF or state in (3, 4)
        print(f"entry[{i}] @0x{off:04X}: ota_seq={seq} ota_state=0x{state:08X} "
              f"({STATES.get(state, 'UNDEFINED')}) crc=0x{crc:08X} blank={blank} "
              f"crc_matches={match or 'none'} invalid={invalid}")
        entries.append({"seq": seq, "crc_ok": bool(match) and not blank and not invalid})

    valid = [e for e in entries if e and e["crc_ok"]]
    if not valid:
        print("RESULT: no valid otadata entry -> bootloader boots ota_0 @ 0x00020000")
        return
    best = max(valid, key=lambda e: e["seq"])
    slot, addr = SLOTS[(best["seq"] - 1) % 2 + 1]
    print(f"RESULT: active slot = {slot} @ {addr} (ota_seq={best['seq']})")


if __name__ == "__main__":
    decode(open(sys.argv[1], "rb").read())
    print("NOTE: roll back without touching NVS/keys by writing the app-only image at the address above.")
