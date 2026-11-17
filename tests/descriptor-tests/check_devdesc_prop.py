#!/usr/bin/env python3
"""Proves the candidate's device descriptor from the linked ELF: bcdUSB is 0x0210, and every other
field is identical to the esp_tinyusb default that would otherwise have been used."""
import os, re, subprocess, sys, tempfile
# Toolchain prefix: override with XTENSA_ESP32S3_PREFIX, otherwise resolve from PATH.
TOOLS = os.environ.get("XTENSA_ESP32S3_PREFIX")
if not TOOLS:
    import shutil
    _od = shutil.which("xtensa-esp32s3-elf-objdump")
    TOOLS = _od[: -len("objdump")] if _od else None
if not TOOLS:
    sys.exit("xtensa-esp32s3-elf toolchain not found: export XTENSA_ESP32S3_PREFIX or source ESP-IDF")
def run(*a): return subprocess.run(a, capture_output=True, text=True, check=True).stdout
def read(elf, addr, size):
    for l in run(TOOLS+"objdump","-h",elf).splitlines():
        m = re.match(r"\s*(\d+)\s+(\S+)\s+([0-9a-f]+)\s+([0-9a-f]+)\s+([0-9a-f]+)", l)
        if m:
            ss, name, vma = int(m.group(3),16), m.group(2), int(m.group(5),16)
            if vma <= addr < vma+ss:
                t = tempfile.NamedTemporaryFile(delete=False, suffix=".bin"); t.close()
                try:
                    run(TOOLS+"objcopy","-O","binary","--only-section="+name,elf,t.name)
                    d = open(t.name,"rb").read()
                finally: os.unlink(t.name)
                return d[addr-vma:addr-vma+size], name
    raise SystemExit("section not found")
def sym(elf, n):
    for l in run(TOOLS+"nm","-S",elf).splitlines():
        p = l.split()
        if len(p) >= 4 and p[3] == n: return int(p[0],16), int(p[1],16)
    raise SystemExit(f"{n} not found")
elf = sys.argv[1]
mine, sec = read(elf, *sym(elf, "s_net_dev_desc"))
theirs, _ = read(elf, *sym(elf, "descriptor_dev_default"))
print(f"bcdDevice = 0x{mine[12] | (mine[13]<<8):04X}")
print(f"s_net_dev_desc        {mine.hex(' ')}  ({len(mine)} B, {sec})")
print(f"descriptor_dev_default {theirs.hex(' ')}  ({len(theirs)} B)")
fails = []
def check(n, c, d=""):
    print(("  PASS  " if c else "  FAIL  ") + n + ("" if c else f"  {d}"))
    if not c: fails.append(n)
check("both descriptors are 18 bytes", len(mine) == 18 and len(theirs) == 18, (len(mine), len(theirs)))
check("bcdUSB of the NCM device descriptor == 0x0210", mine[2] | (mine[3]<<8) == 0x0210, hex(mine[2]|(mine[3]<<8)))
check("esp_tinyusb default would have been 0x0200", theirs[2] | (theirs[3]<<8) == 0x0200, hex(theirs[2]|(theirs[3]<<8)))
diff = [i for i in range(18) if mine[i] != theirs[i]]
check("only bcdUSB (2..3) and bcdDevice (12..13) differ", set(diff) <= {2, 3, 12, 13}, diff)
check("bcdDevice reports revision 0x0101", (mine[12] | (mine[13]<<8)) == 0x0101, hex(mine[12] | (mine[13]<<8)))
check("VID/PID unchanged (303A:4006)",
      (mine[8] | (mine[9] << 8), mine[10] | (mine[11] << 8)) == (0x303A, 0x4006),
      f"{mine[8]|(mine[9]<<8):04X}:{mine[10]|(mine[11]<<8):04X}")
check("device class triple unchanged vs esp_tinyusb default", mine[4:7] == theirs[4:7], mine[4:7].hex())
print("\nRESULT: " + ("FAIL" if fails else "PASS"))
sys.exit(1 if fails else 0)
