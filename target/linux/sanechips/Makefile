# SPDX-License-Identifier: GPL-2.0-only
#
# Copyright (C) 2026 OpenWrt.org

include $(TOPDIR)/rules.mk

ARCH:=arm
BOARD:=sanechips
BOARDNAME:=Sanechips / ZTE ZX279128
FEATURES:=squashfs nand usb pci pcie gpio ramdisk
CPU_TYPE:=cortex-a9
SUBTARGETS:=generic

KERNEL_PATCHVER:=6.18

define Target/Description
	Build firmware images for Sanechips / ZTE ZX279128 based routers and gateways.
endef

include $(INCLUDE_DIR)/target.mk

KERNELNAME:=zImage dtbs

DEFAULT_PACKAGES += \
	kmod-gpio-button-hotplug \
	kmod-leds-gpio

$(eval $(call BuildTarget))
