# SPDX-License-Identifier: GPL-2.0-only
#
# Copyright (C) 2026 OpenWrt.org

include $(TOPDIR)/rules.mk
include $(INCLUDE_DIR)/image.mk

DEVICE_VARS += ZTE_MODEL ZTE_VERSION

define Build/zte-f670l-initramfs-header
	python3 $(TOPDIR)/target/linux/sanechips/image/zte-pack.py \
		--kernel $(BIN_DIR)/$(KERNEL_INITRAMFS_IMAGE) \
		--wrap-jffs2 \
		--output $@ \
		--model "$(ZTE_MODEL)" \
		--version "$(ZTE_VERSION)"
	cp -f $@ $(BIN_DIR)/upgrade.bin
	cp -f $@ $(TOPDIR)/../ztef670l_data/upgrade.bin
	cp -f $(BIN_DIR)/$(KERNEL_INITRAMFS_IMAGE) $(TOPDIR)/../ztef670l_data/uImage_initramfs.bin
endef

zte_zxhn-f670l-images:

define Device/Default
  PROFILES := Default
  KERNEL_NAME := zImage
  KERNEL_LOADADDR := 0x40008000
  KERNEL_ENTRY := 0x40008000
  DEVICE_DTS_DIR := ../dts
  KERNEL := kernel-bin | append-dtb | uImage none
  KERNEL_INITRAMFS := kernel-bin | append-dtb | uImage none
endef

define Device/zte_zxhn-f670l
  $(Device/Default)
  DEVICE_VENDOR := ZTE
  DEVICE_MODEL := ZXHN F670L
  DEVICE_VARIANT := v1.1
  DEVICE_DTS := zx279128-zte-f670l
  DEVICE_PACKAGES := kmod-mt7603 kmod-mt76x2 iw hostapd-basic-mbedtls dnsmasq luci uhttpd rpcd
  ZTE_MODEL := ZXHN F670L UNI V1.1.20P3N4D
  ZTE_VERSION := V1.1.20P3N4D
  IMAGES :=
  ARTIFACTS := upgrade.bin
  ARTIFACT/upgrade.bin := zte-f670l-initramfs-header
endef
TARGET_DEVICES += zte_zxhn-f670l

$(eval $(call BuildImage))
