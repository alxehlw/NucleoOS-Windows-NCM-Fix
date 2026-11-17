#!/usr/bin/env python3
"""Independent validator for the NucleoOS MS OS 2.0 descriptors.

Reads the hex dump produced by dump_desc.c and re-parses every field from raw bytes according to
Microsoft's "MS OS 2.0 Descriptors Specification" — it shares no assumptions with the C structs.
Anything that Microsoft would reject makes this script exit non-zero.
"""
import re
import sys

FAILURES = []
CHECKS = 0


def check(name, cond, detail=""):
    global CHECKS
    CHECKS += 1
    if cond:
        print(f"  PASS  {name}")
    else:
        print(f"  FAIL  {name}  {detail}")
        FAILURES.append(name)


def load(path):
    blocks = {}
    name, data = None, []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("BEGIN "):
                _, name, _ = line.split()
                data = []
            elif line == "END " + str(name):
                blocks[name] = bytes(data)
                name = None
            elif name and line:
                data += [int(tok, 16) for tok in line.split()]
    return blocks


def u16(b, off):
    return b[off] | (b[off + 1] << 8)


def u32(b, off):
    return b[off] | (b[off + 1] << 8) | (b[off + 2] << 16) | (b[off + 3] << 24)


def validate_bos(bos):
    print("BOS descriptor")
    check("bLength == 5", bos[0] == 5, bos[0])
    check("bDescriptorType == 0x0F (BOS)", bos[1] == 0x0F, hex(bos[1]))
    check("wTotalLength == actual byte count", u16(bos, 2) == len(bos), (u16(bos, 2), len(bos)))
    check("bNumDeviceCaps == 1", bos[4] == 1, bos[4])

    p = 5  # platform capability starts here
    check("platform bLength == 28", bos[p] == 28, bos[p])
    check("platform bDescriptorType == 0x10", bos[p + 1] == 0x10, hex(bos[p + 1]))
    check("bDevCapabilityType == 0x05 (PLATFORM)", bos[p + 2] == 0x05, bos[p + 2])
    check("platform bReserved == 0", bos[p + 3] == 0, bos[p + 3])
    uuid = bos[p + 4:p + 20]
    check(
        "PlatformCapabilityUUID == D8DD60DF-4589-4CC7-9CD2-659D9E648A9F",
        uuid == bytes([0xDF, 0x60, 0xDD, 0xD8, 0x89, 0x45, 0xC7, 0x4C,
                       0x9C, 0xD2, 0x65, 0x9D, 0x9E, 0x64, 0x8A, 0x9F]),
        uuid.hex(),
    )
    check("dwWindowsVersion == 0x06030000", u32(bos, p + 20) == 0x06030000, hex(u32(bos, p + 20)))
    check("platform ends exactly at wTotalLength", p + 28 == len(bos), p + 28)
    return u16(bos, p + 24), bos[p + 26], bos[p + 27]  # declared set length, vendor code, alt enum


def validate_msos20(ms, declared_len, vendor_code):
    print("MS OS 2.0 descriptor set")
    check("byte count == length declared in BOS", len(ms) == declared_len, (len(ms), declared_len))

    # ── Set Header (offset 0) ───────────────────────────────────────────────
    check("SetHeader wLength == 10", u16(ms, 0) == 10, u16(ms, 0))
    check("SetHeader wDescriptorType == 0x0000", u16(ms, 2) == 0x0000, hex(u16(ms, 2)))
    check("SetHeader dwWindowsVersion == 0x06030000", u32(ms, 4) == 0x06030000, hex(u32(ms, 4)))
    check("SetHeader wTotalLength == actual byte count", u16(ms, 8) == len(ms), (u16(ms, 8), len(ms)))
    check("vendor code in BOS matches our bRequest", vendor_code == 0x01, vendor_code)

    # ── Configuration Subset (offset 10) ────────────────────────────────────
    cfg = 10
    check("ConfigSubset wLength == 8", u16(ms, cfg) == 8, u16(ms, cfg))
    check("ConfigSubset wDescriptorType == 0x0001", u16(ms, cfg + 2) == 0x0001, hex(u16(ms, cfg + 2)))
    check("ConfigSubset bConfigurationValue == 0 (all configurations)", ms[cfg + 4] == 0, ms[cfg + 4])
    check("ConfigSubset bReserved == 0", ms[cfg + 5] == 0, ms[cfg + 5])
    check("ConfigSubset wTotalLength == set minus header",
          u16(ms, cfg + 6) == len(ms) - 10, (u16(ms, cfg + 6), len(ms) - 10))

    # ── Function Subset (offset 18) ─────────────────────────────────────────
    fn = 18
    check("FunctionSubset wLength == 8", u16(ms, fn) == 8, u16(ms, fn))
    check("FunctionSubset wDescriptorType == 0x0002", u16(ms, fn + 2) == 0x0002, hex(u16(ms, fn + 2)))
    check("FunctionSubset bFirstInterfaceNumber == 0 (NCM control interface)",
          ms[fn + 4] == 0, ms[fn + 4])
    check("FunctionSubset bReserved == 0", ms[fn + 5] == 0, ms[fn + 5])
    check("FunctionSubset wSubsetLength == function header + its features",
          u16(ms, fn + 6) == len(ms) - 18, (u16(ms, fn + 6), len(ms) - 18))

    # ── Compatible ID feature (offset 26) ──────────────────────────────────
    cid = 26
    check("CompatibleID wLength == 20", u16(ms, cid) == 20, u16(ms, cid))
    check("CompatibleID wDescriptorType == 0x0003", u16(ms, cid + 2) == 0x0003, hex(u16(ms, cid + 2)))
    compat = ms[cid + 4:cid + 12]
    check("CompatibleID == b'WINNCM\\0\\0' (drives usbncm.inf USB\\MS_COMP_WINNCM)",
          compat == b"WINNCM\x00\x00", compat)
    check("SubCompatibleID == all zero", ms[cid + 12:cid + 20] == b"\x00" * 8, ms[cid + 12:cid + 20])

    # ── Registry property: DeviceInterfaceGUIDs (offset 46) ────────────────
    rp = 46
    check("RegProp wLength == 132", u16(ms, rp) == 132, u16(ms, rp))
    check("RegProp wDescriptorType == 0x0004", u16(ms, rp + 2) == 0x0004, hex(u16(ms, rp + 2)))
    check("RegProp wPropertyDataType == 0x0007 (REG_MULTI_SZ)", u16(ms, rp + 4) == 0x0007, u16(ms, rp + 4))
    name_len = u16(ms, rp + 6)
    check("RegProp wPropertyNameLength == 42 (20 chars + NUL, UTF-16)", name_len == 42, name_len)
    raw_name = ms[rp + 8:rp + 8 + name_len]
    check("property name ends with a single UTF-16 NUL", raw_name[-2:] == b"\x00\x00", raw_name[-4:])
    decoded_name = raw_name.decode("utf-16-le")
    check("property name == 'DeviceInterfaceGUIDs\\0'",
          decoded_name == "DeviceInterfaceGUIDs\x00", repr(decoded_name))
    data_len = u16(ms, rp + 8 + name_len)
    check("RegProp wPropertyDataLength == 80 (38 chars + 2 NUL, UTF-16)", data_len == 80, data_len)
    payload = ms[rp + 10 + name_len:rp + 10 + name_len + data_len]
    check("descriptor ends exactly at the end of the set",
          rp + 10 + name_len + data_len == len(ms), rp + 10 + name_len + data_len)
    check("REG_MULTI_SZ payload ends with the double NUL terminator",
          payload[-4:] == b"\x00\x00\x00\x00", payload[-4:].hex())
    guid_text = payload[:-4].decode("utf-16-le")
    check("payload is one GUID string",
          re.fullmatch(r"\{[0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12}\}", guid_text),
          repr(guid_text))
    print(f"        DeviceInterfaceGUIDs = {guid_text}")


def main():
    blocks = load(sys.argv[1])
    if "BOS" not in blocks or "MSOS20" not in blocks:
        print("missing BOS or MSOS20 block")
        return 2
    declared_len, vendor_code, alt_enum = validate_bos(blocks["BOS"])
    validate_msos20(blocks["MSOS20"], declared_len, vendor_code)
    print("Vendor request implied by the BOS: "
          f"bmRequestType=0xC0 bRequest={vendor_code:#04x} wValue=0x0000 wIndex=0x0007 "
          f"wLength={declared_len}")
    print(f"\n{CHECKS - len(FAILURES)}/{CHECKS} checks passed")
    if alt_enum != 0:
        print(f"  FAIL  bAltEnumCode must be 0 (got {alt_enum})")
        FAILURES.append("alt enum")
    if FAILURES:
        print("RESULT: FAIL")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
