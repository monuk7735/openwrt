#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
#
# Copyright (C) 2026 OpenWrt.org
# ZTE ZXHN F670L Firmware Container Packager (upgrade.bin)
# Formats kernel and rootfs with ZTE magic, verhdr, CRC32, and geometry
# for U-Boot TFTP recovery ('downver version') and stock Web upgrade.

import argparse
import binascii
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import time

def parse_args():
    parser = argparse.ArgumentParser(description="Pack ZTE ZXHN F670L upgrade.bin")
    parser.add_argument("--kernel", required=True, help="Input kernel uImage")
    parser.add_argument("--rootfs", default=None, help="Input rootfs squashfs (optional)")
    parser.add_argument("--output", required=True, help="Output upgrade.bin")
    parser.add_argument("--model", default="ZXHN F670L UNI V1.1.20P3N4D", help="Target router model string")
    parser.add_argument("--version", default="V1.1.20P3N4D", help="Target software version string")
    parser.add_argument("--wrap-jffs2", action="store_true", help="Wrap kernel as 0uImage in JFFS2 at offset 0x20000 for ZTE U-Boot")
    return parser.parse_args()

def build_zte_package(kernel_bytes, rootfs_bytes, model_str, ver_str):
    klen = len(kernel_bytes)
    rflen = len(rootfs_bytes)
    total_payload = klen + rflen

    kcrc = binascii.crc32(kernel_bytes) & 0xffffffff
    rfcrc = binascii.crc32(rootfs_bytes) & 0xffffffff if rflen > 0 else 0

    # Header size up to payload offset (0x168) is 360 bytes
    hdr = bytearray(0x168)

    # 1. Outer magic at offset 0x000 (16 bytes)
    hdr[0x00:0x10] = b"\x99\x99\x99\x99\x44\x44\x44\x44\x55\x55\x55\x55\xaa\xaa\xaa\xaa"

    # 2. hdr_ofs at offset 0x010 (4 bytes)
    struct.pack_into("<I", hdr, 0x10, 0x28)

    # 3. Key / magic at 0x038
    struct.pack_into("<I", hdr, 0x38, 0x1312d0e8)

    # Version header body starts relative to r5 (r3=0x28 + 0x14 = 0x3c)
    # r5 + 0x10 (0x4c): Version string (32 bytes)
    ver_ascii = ver_str.encode("ascii")[:31]
    hdr[0x4c : 0x4c + len(ver_ascii)] = ver_ascii

    # r5 + 0x2c (0x68): Active flags
    struct.pack_into("<I", hdr, 0x68, 1)

    # r5 + 0x30 (0x6c): Total payload length
    struct.pack_into("<I", hdr, 0x6c, total_payload)

    # r5 + 0x34 (0x70): Kernel length
    struct.pack_into("<I", hdr, 0x70, klen)

    # r5 + 0x38 (0x74): Payload start offset (0x168)
    struct.pack_into("<I", hdr, 0x74, 0x168)

    # r5 + 0x3c (0x78): Kernel CRC32
    struct.pack_into("<I", hdr, 0x78, kcrc)

    # r5 + 0x40 (0x7c): Rootfs length
    struct.pack_into("<I", hdr, 0x7c, rflen)

    # r5 + 0x44 (0x80): Rootfs payload offset in container (U-Boot: r2 = [r5, #68] + 0x42000000)
    rf_offset = (0x168 + klen) if rflen > 0 else 0
    struct.pack_into("<I", hdr, 0x80, rf_offset)

    # r5 + 0x48 (0x84): Rootfs CRC32
    struct.pack_into("<I", hdr, 0x84, rfcrc)

    # r5 + 0x6c (0xa8): Hardware / Model string
    model_ascii = model_str.encode("ascii")[:63]
    hdr[0xa8 : 0xa8 + len(model_ascii)] = model_ascii

    # r5 + 0xc4 (0x100): Status flag
    struct.pack_into("<I", hdr, 0x100, 1)

    # r5 + 0xd0 (0x10c): Timestamp string (YYYYMMDDHHMMSS)
    ts = time.strftime("%Y%m%d%H%M%S").encode("ascii")
    hdr[0x10c : 0x10c + len(ts)] = ts

    # Header CRC32 computed over 204 bytes (from 0x3c to 0x108)
    hdr_crc = binascii.crc32(hdr[0x3c : 0x3c + 204]) & 0xffffffff
    # r5 + 0xcc (0x108): Header CRC32
    struct.pack_into("<I", hdr, 0x108, hdr_crc)

    return bytes(hdr) + kernel_bytes + rootfs_bytes

def main():
    args = parse_args()

    with open(args.kernel, "rb") as f:
        kernel_bytes = f.read()

    if args.wrap_jffs2:
        with tempfile.TemporaryDirectory() as tmpdir:
            indir = os.path.join(tmpdir, "root")
            os.makedirs(indir, exist_ok=True)
            uimage_path = os.path.join(indir, "0uImage")
            with open(uimage_path, "wb") as f:
                f.write(kernel_bytes)
            jffs2_out = os.path.join(tmpdir, "kernel_jffs2.bin")
            # Prefer host tool in staging_dir if present
            mkfs_cmd = "mkfs.jffs2"
            staging_mkfs = os.path.expanduser("~/src/openwrt-dev/openwrt/staging_dir/host/bin/mkfs.jffs2")
            if os.path.exists(staging_mkfs):
                mkfs_cmd = staging_mkfs
            cmd = [mkfs_cmd, "-e", "0x20000", "-p", "-l", "-n", "-d", indir, "-o", jffs2_out]
            subprocess.run(cmd, check=True)
            with open(jffs2_out, "rb") as f:
                jffs2_bytes = f.read()
            # Pad from 0x168 to 0x20000 with zeroes so JFFS2 lands at eraseblock 1 (0x20000)
            padding = b"\x00" * (0x20000 - 0x168)
            kernel_bytes = padding + jffs2_bytes

    rootfs_bytes = b""
    if args.rootfs:
        with open(args.rootfs, "rb") as f:
            rootfs_bytes = f.read()

    pkg = build_zte_package(kernel_bytes, rootfs_bytes, args.model, args.version)

    with open(args.output, "wb") as f:
        f.write(pkg)

    print(f"[zte-pack] Successfully generated {args.output} ({len(pkg)} bytes)")
    print(f"           Kernel: {len(kernel_bytes)} bytes | Rootfs: {len(rootfs_bytes)} bytes")
    print(f"           Model: {args.model} | Version: {args.version}")

if __name__ == "__main__":
    main()
