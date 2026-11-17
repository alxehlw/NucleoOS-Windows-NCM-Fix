#!/usr/bin/env python3
"""Single-sector otadata planner for ESP-IDF v5.4.4 (NucleoOS / Cardputer ADV).

Reads an 8 KiB otadata dump (`read_flash 0xF000 0x2000`) and plans a boot-slot switch
WITHOUT touching the 4 KiB sector that holds the record of the running image.

Rules mirrored from ESP-IDF v5.4.4 sources (not guessed):
  * record            = esp_ota_select_entry_t {u32 ota_seq, u8 seq_label[20], u32 ota_state, u32 crc}
  * crc               = esp_rom_crc32_le(0xFFFFFFFF, &ota_seq, 4)
                        (bootloader_common_loader.c: bootloader_common_ota_select_crc)
                        the ROM routine inverts its input and its output, so in Python it is
                        zlib.crc32(pack('<I', seq), 0xFFFFFFFF) -- NOT plain zlib.crc32()
                        (anchored to a real device record: seq=1 -> 0x4743989A)
  * invalid record    = ota_seq == 0xFFFFFFFF  or  state in {INVALID(3), ABORTED(4)}
  * valid record      = not invalid  and  crc matches
  * active record     = max ota_seq among valid ones; tie -> index 0; none -> bootloader
                        falls back to ota_0 (bootloader_common_loader.c select_otadata,
                        bootloader_utility.c)
  * boot slot         = (ota_seq - 1) % 2      (0 -> ota_0 @0x20000, 1 -> ota_1 @0x3A0000)
  * next record       = esp_ota_ops.c esp_rewrite_ota_data() / rewrite_ota_seq():
                          sector  = (~active) & 1   (sector 0 when both records are invalid)
                          ota_seq = smallest target-parity value > active seq  (== active+1)
                          state   = ESP_OTA_IMG_NEW (0)
                          seq_label = bytes [4:24] read from the target sector
                          crc     = zlib.crc32(ota_seq)
                        the whole 4 KiB sector is erased and the 32-byte record written at 0
  * first boot        = bootloader turns NEW into PENDING_VERIFY; if the app never confirms,
                        the NEXT boot turns it into ABORTED and the other (untouched, valid)
                        record wins again -> automatic rollback.

This tool never touches a device. It only reads a dump and emits bytes to write.

Usage:
  python otadata_plan.py otadata.bin                     # plan + byte diff, writes nothing
  python otadata_plan.py otadata.bin --emit --outdir .   # also write the 4 KiB sector image
  python otadata_plan.py otadata.bin --target ota_1       # force the non-active target slot
  python otadata_plan.py --selftest
Exit codes: 0 plan ok, 2 refused (unsafe), 3 bad dump, 4 selftest failed.
"""
import json
import os
import struct
import sys
import zlib

OTADATA_BASE = 0xF000
SECTOR = 0x1000
ENTRY_SIZE = 32
OTA_SLOTS = (("ota_0", 0x20000), ("ota_1", 0x3A0000))
NEW, PENDING, VALID, INVALID, ABORTED = 0, 1, 2, 3, 4
STATE_NAME = {0: "NEW", 1: "PENDING_VERIFY", 2: "VALID", 3: "INVALID", 4: "ABORTED",
              0xFFFFFFFF: "UNDEFINED"}


def crc32_le(seq):
    """esp_rom_crc32_le(0xFFFFFFFF, &seq, 4): the ROM routine inverts both its input and
    its output (`crc = ~crc` ... `return ~crc`), so the equivalent Python call keeps
    0xFFFFFFFF as zlib's running value. Plain zlib.crc32() is a different init state."""
    return zlib.crc32(struct.pack("<I", seq), 0xFFFFFFFF) & 0xFFFFFFFF


def parse_record(buf):
    seq, label, state, crc = struct.unpack("<I20sII", buf[:ENTRY_SIZE])
    return {"seq": seq, "label": label, "state": state, "crc": crc,
            "crc_ok": crc == crc32_le(seq)}


def record_bytes(seq, label, state):
    return struct.pack("<I20sII", seq, label, state, crc32_le(seq))


def is_valid(rec):
    if rec["seq"] == 0xFFFFFFFF or rec["state"] in (INVALID, ABORTED):
        return False
    return rec["crc_ok"]


def select_active(recs):
    valid = [is_valid(r) for r in recs]
    if valid[0] and valid[1]:
        return 0 if recs[0]["seq"] >= recs[1]["seq"] else 1
    if valid[0]:
        return 0
    if valid[1]:
        return 1
    return -1


def simulate_boot(recs):
    """Mirror of the bootloader: PENDING -> ABORTED, then take max valid seq."""
    for r in recs:
        if r["state"] == PENDING:
            r["state"] = ABORTED
    idx = select_active(recs)
    if idx < 0:
        return 0, None, "fallback ota_0 (both records invalid, no factory)"
    slot = (recs[idx]["seq"] - 1) % len(OTA_SLOTS)
    return slot, recs[idx]["seq"], f"record #{idx} (seq {recs[idx]['seq']})"


def plan(dump, target=None):
    if len(dump) != 2 * SECTOR:
        raise ValueError(f"dump must be {2 * SECTOR} bytes (0x2000), got {len(dump)}")
    recs = [parse_record(dump[i * SECTOR:i * SECTOR + ENTRY_SIZE]) for i in range(2)]
    active = select_active(recs)
    if active >= 0:
        active_slot = (recs[active]["seq"] - 1) % len(OTA_SLOTS)
        active_seq = recs[active]["seq"]
        if active_seq >= 0xFFFFFFFE:
            raise ValueError("ota_seq is at the end of the range; this needs a full otadata "
                             "re-initialisation, which is out of scope for a single-sector update")
    else:
        active_slot, active_seq = 0, None          # bootloader falls back to ota_0
    target_slot = 1 - active_slot if target is None else OTA_SLOTS.index(
        next(s for s in OTA_SLOTS if s[0] == target))
    if target_slot == active_slot and active >= 0:
        raise ValueError(f"{OTA_SLOTS[target_slot][0]} is the active slot; refusing to overwrite it")
    new_sector = (1 - active) if active >= 0 else 0
    new_seq = (active_seq + 1) if active_seq is not None else target_slot + 1
    if (new_seq - 1) % len(OTA_SLOTS) != target_slot:
        raise ValueError(f"parity mismatch: seq {new_seq} lands on slot {(new_seq - 1) % 2}")
    if new_sector == active:
        raise ValueError("internal: refusing to write the active record's sector")
    label = recs[new_sector]["label"]                 # IDF keeps the bytes it read
    new_entry = record_bytes(new_seq, label, NEW)
    sector_img = b"\xFF" * SECTOR
    sector_img = new_entry + sector_img[ENTRY_SIZE:]
    updated = bytearray(dump)
    updated[new_sector * SECTOR:(new_sector + 1) * SECTOR] = sector_img
    new_recs = [parse_record(bytes(updated[i * SECTOR:i * SECTOR + ENTRY_SIZE])) for i in range(2)]
    sim_slot, sim_seq, sim_why = simulate_boot([dict(r) for r in new_recs])
    keep_idx = 1 - new_sector
    keep_intact = bytes(updated[keep_idx * SECTOR:(keep_idx + 1) * SECTOR]) == \
                  bytes(dump[keep_idx * SECTOR:(keep_idx + 1) * SECTOR])
    keep_valid_before = is_valid(recs[keep_idx])
    checks = {
        "new sector != active sector": new_sector != active,
        "active record bytes untouched": keep_intact,
        "no previously valid record was destroyed":
            keep_intact and (is_valid(new_recs[keep_idx]) if keep_valid_before else True),
        "bootloader selects the new record": sim_seq == new_seq,
        "boot slot == target slot": sim_slot == target_slot,
        "new record state == NEW": new_recs[new_sector]["state"] == NEW,
        "new record crc valid": new_recs[new_sector]["crc_ok"],
    }
    return {
        "records": [{"sector": i, "offset": f"0x{OTADATA_BASE + i * SECTOR:05X}", **{
            k: (v if k != "label" else v.hex()) for k, v in r.items()}} for i, r in enumerate(recs)],
        "active": {"index": active, "slot": OTA_SLOTS[active_slot][0],
                   "offset": f"0x{OTA_SLOTS[active_slot][1]:05X}",
                   "seq": active_seq,
                   "state": STATE_NAME.get(recs[active]["state"]) if active >= 0 else None},
        "target": {"slot": OTA_SLOTS[target_slot][0], "offset": f"0x{OTA_SLOTS[target_slot][1]:05X}"},
        "write": {"sector": new_sector, "flash_offset": f"0x{OTADATA_BASE + new_sector * SECTOR:05X}",
                  "length": SECTOR, "ota_seq": new_seq, "state": "NEW(0)"},
        "verify": {"bootloader_would_select": f"seq {sim_seq} -> {OTA_SLOTS[sim_slot][0]}", "why": sim_why},
        "rollback": {"record": keep_idx, "offset": f"0x{OTADATA_BASE + keep_idx * SECTOR:05X}",
                     "seq": recs[keep_idx]["seq"], "state": STATE_NAME.get(recs[keep_idx]["state"]),
                     "usable": is_valid(recs[keep_idx])},
        "checks": checks,
        "sector_image": sector_img,
        "updated": bytes(updated),
    }


def byte_diff(before, after, base):
    out = []
    for i, (a, b) in enumerate(zip(before, after)):
        if a != b:
            out.append((base + i, a, b))
    return out


def fmt_diff(diff, limit=48):
    if not diff:
        return "  (no differing bytes)"
    lines = [f"  {len(diff)} byte(s) differ:"]
    for off, a, b in diff[:limit]:
        lines.append(f"    0x{off:05X}  {a:02X} -> {b:02X}")
    if len(diff) > limit:
        lines.append(f"    ... {len(diff) - limit} more")
    return "\n".join(lines)


def selftest():
    def mk(*seq_states):
        dump = bytearray(b"\xFF" * (2 * SECTOR))
        for i, st in enumerate(seq_states):
            if st is None or st[0] is None:
                continue
            seq, state = st
            dump[i * SECTOR:i * SECTOR + ENTRY_SIZE] = record_bytes(seq, b"\xFF" * 20, state)
        return bytes(dump)

    fails = []
    # absolute anchor taken from a real device dump (2026-11-17, ota_0 seq=1, VALID):
    # a self-consistent but wrong CRC convention passes every other vector, so pin this.
    if crc32_le(1) != 0x4743989A:
        fails.append(("CRC convention vs real device record", hex(crc32_le(1)))
    vectors = [
        ("blank otadata",        (None, None),                 "ota_1", 2, 0, None),
        ("seq1 only (ota_0)",    ((1, VALID), (None, None)),   "ota_1", 2, 1, 1),
        ("seq2 only (ota_1)",    ((None, None), (2, VALID)),   "ota_0", 3, 0, 2),
        ("seq1 + seq2",          ((1, VALID), (2, VALID)),     "ota_0", 3, 0, 2),
        ("seq3 + seq2 (rolled)", ((3, VALID), (2, VALID)),     "ota_1", 4, 1, 3),
        ("seq1 INVALID + seq2",  ((1, INVALID), (2, VALID)),   "ota_0", 3, 0, 2),
        ("seq1 ABORTED + seq2",  ((1, ABORTED), (2, VALID)),   "ota_0", 3, 0, 2),
        ("tie seq2/seq2",        ((2, VALID), (2, VALID)),     "ota_0", 3, 1, 2),
        ("both ABORTED",         ((1, ABORTED), (2, ABORTED)), "ota_1", 2, 0, None),
    ]
    for name, states, slot, seq, sector, active_seq in vectors:
        dump = mk(*states)
        try:
            p = plan(dump)
        except Exception as e:                                  # noqa: BLE001
            fails.append((name, f"raised {e}"))
            continue
        got = (p["target"]["slot"], p["write"]["ota_seq"], p["write"]["sector"], p["active"]["seq"])
        if not all(p["checks"].values()):
            fails.append((name, f"failed checks {[k for k, v in p['checks'].items() if not v]}"))
        elif got != (slot, seq, sector, active_seq):
            fails.append((name, f"got {got} want {(slot, seq, sector, active_seq)}"))

    d = bytearray(mk((1, VALID), (2, VALID)))
    d[28:32] = b"\x00\x00\x00\x00"                              # break record 0's crc
    if plan(bytes(d))["active"]["seq"] != 2:
        fails.append(("crc mismatch falls back to the other record", plan(bytes(d))["active"]["seq"]))

    d = bytearray(mk((1, VALID), (2, VALID)))
    d[0:4] = b"\xFF\xFF\xFF\xFF"                                 # seq 0xFFFFFFFF is invalid
    if plan(bytes(d))["active"]["seq"] != 2:
        fails.append(("0xFFFFFFFF seq is invalid", plan(bytes(d))["active"]["seq"]))

    for name, dump, kw in (("seq overflow refused", mk((0xFFFFFFFE, VALID), (None, None)), {}),
                           ("refuse to target the active slot", mk((1, VALID), (None, None)),
                            {"target": "ota_0"})):
        try:
            plan(dump, **kw)
            fails.append((name, "no exception"))
        except ValueError:
            pass

    keep = MK_KEEP = mk((1, VALID), (2, VALID))
    if bytes(plan(keep)["updated"][SECTOR:2 * SECTOR]) != keep[SECTOR:2 * SECTOR]:
        fails.append(("active sector untouched", "bytes changed"))

    blank = mk((None, None), (None, None))
    diff = byte_diff(blank, plan(blank)["updated"], OTADATA_BASE)
    if [o - OTADATA_BASE for o, _, _ in diff] != [0, 1, 2, 3, 24, 25, 26, 27, 28, 29, 30, 31]:
        fails.append(("blank diff == seq+state+crc only", [o - OTADATA_BASE for o, _, _ in diff]))

    for f in fails:
        print(f"  FAIL  {f[0]}: {f[1]}")
    total = len(vectors) + 7
    print(f"\nSELFTEST: {'FAIL' if fails else 'PASS'} ({total - len(fails)}/{total})")
    return 4 if fails else 0


def main(argv):
    if "--selftest" in argv:
        return selftest()
    if len(argv) < 2 or argv[1].startswith("-"):
        print(__doc__)
        return 3
    path = argv[1]
    dump = open(path, "rb").read()
    if "--split" in argv:                       # 8 KiB dump -> two 4 KiB rollback sectors
        base = os.path.splitext(path)[0]
        for i in range(2):
            out = f"{base}-s{i}.bin"
            with open(out, "wb") as fh:
                fh.write(dump[i * SECTOR:(i + 1) * SECTOR])
            print(f"wrote {out}  (restore with: write_flash 0x{OTADATA_BASE + i * SECTOR:05X} {os.path.basename(out)})")
        return 0
    target = None
    if "--target" in argv:
        target = argv[argv.index("--target") + 1]
    try:
        p = plan(dump, target=target)
    except ValueError as e:
        print(f"REFUSED: {e}")
        return 2
    print(f"dump      {path}  ({len(dump)} bytes)")
    for r in p["records"]:
        print(f"  record #{r['sector']} @{r['offset']}  seq={r['seq']:>10}  "
              f"state={STATE_NAME.get(r['state'], r['state']):<14} crc_ok={r['crc_ok']}")
    print(f"active    {p['active']}")
    print(f"target    {p['target']}")
    print(f"write     sector #{p['write']['sector']} @{p['write']['flash_offset']} "
          f"({p['write']['length']} bytes)  new ota_seq={p['write']['ota_seq']}  state=NEW")
    print(f"verify    {p['verify']['bootloader_would_select']}  ({p['verify']['why']})")
    print(f"rollback  record #{p['rollback']['record']} @{p['rollback']['offset']} "
          f"seq={p['rollback']['seq']} state={p['rollback']['state']} usable={p['rollback']['usable']}")
    print("checks    " + "  ".join(f"{'PASS' if v else 'FAIL'} {k}" for k, v in p["checks"].items()))
    sec = p["write"]["sector"]
    before = dump[sec * SECTOR:(sec + 1) * SECTOR]
    after = p["updated"][sec * SECTOR:(sec + 1) * SECTOR]
    print(f"\nbyte diff of the written sector ({p['write']['flash_offset']}):")
    print(fmt_diff(byte_diff(before, after, OTADATA_BASE + sec * SECTOR)))
    keep = 1 - sec
    print(f"other sector {keep} @0x{OTADATA_BASE + keep * SECTOR:05X}: "
          f"{'byte-identical (untouched)' if before is not None and p['checks']['active record bytes untouched'] else 'CHANGED'}")
    if not all(p["checks"].values()):
        print("REFUSED: self-checks failed")
        return 2
    if "--emit" in argv:
        outdir = argv[argv.index("--outdir") + 1] if "--outdir" in argv else "."
        base = os.path.splitext(os.path.basename(path))[0]
        out = os.path.join(outdir, f"{base}-sector{sec}-at-0x{OTADATA_BASE + sec * SECTOR:05X}.bin")
        with open(out, "wb") as fh:
            fh.write(p["sector_image"])
        plan_path = os.path.join(outdir, f"{base}-plan.json")
        with open(plan_path, "w", encoding="utf-8") as fh:
            json.dump({k: v for k, v in p.items() if k not in ("sector_image", "updated")},
                      fh, indent=2, ensure_ascii=False)
        print(f"\nwrote {out} ({len(p['sector_image'])} bytes)")
        print(f"wrote {plan_path}")
        print(f"\nflash ONLY that sector, AFTER the app image is already in {p['target']['slot']}:")
        print(f"  python -m esptool --chip esp32s3 -p COM<x> write_flash "
              f"{p['write']['flash_offset']} {os.path.basename(out)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
