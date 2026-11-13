#!/bin/sh
# SPDX-License-Identifier: GPL-2.0-only
# Copyright (C) 2026 OpenWrt.org

REQUIRE_IMAGE_METADATA=0

platform_check_image() {
	return 0
}

platform_do_upgrade() {
	default_do_upgrade "$1"
}
