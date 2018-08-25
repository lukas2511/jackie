#!/usr/bin/env bash

eval $(cat "/sys${DEVPATH}/../device/uevent")

set > "/tmp/bar_$(echo "${PRODUCT}" | tr "/" "_").log"

if [ "${PRODUCT}" = "1397/bc/100" ]; then
	printf "bcf2000"
fi
