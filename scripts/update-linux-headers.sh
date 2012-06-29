#!/bin/sh -e
#
# Copied from QEMU and adapted for this software
#
# Update Linux kernel headers requires from a specified kernel tree.
#
# Copyright (C) 2012 Virtual Open Systems and Columbia University
#
# Authors:
#  Jan Kiszka        <jan.kiszka@siemens.com>
#  Christoffer Dall  <c.dall@virtualopensystems.com>
#
# This work is licensed under the terms of the GNU GPL version 2.
#

tmpdir=`mktemp -d`
linux="$1"
output="$2"

if [ -z "$linux" ] || ! [ -d "$linux" ]; then
    cat << EOF
usage: update-kernel-headers.sh LINUX_PATH [OUTPUT_PATH]

LINUX_PATH      Linux kernel directory to obtain the headers from
OUTPUT_PATH     output directory, usually the qemu source tree (default: $PWD)
EOF
    exit 1
fi

if [ -z "$output" ]; then
    output="$PWD"
fi

#for arch in x86 powerpc s390 arm; do
arch=arm
make -C "$linux" INSTALL_HDR_PATH="$tmpdir" SRCARCH=$arch headers_install

rm -rf "$output/linux-headers/asm-$arch"
mkdir -p "$output/linux-headers/asm-$arch"
for header in kvm.h kvm_para.h; do
cp "$tmpdir/include/asm/$header" "$output/linux-headers/asm-$arch"
done

rm -rf "$output/linux-headers/linux"
mkdir -p "$output/linux-headers/linux"
for header in kvm.h kvm_para.h vhost.h virtio_config.h virtio_ring.h; do
    cp "$tmpdir/include/linux/$header" "$output/linux-headers/linux"
done
if [ -L "$linux/source" ]; then
    cp "$linux/source/COPYING" "$output/linux-headers"
else
    cp "$linux/COPYING" "$output/linux-headers"
fi

rm -rf "$tmpdir"
