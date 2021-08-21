#!/usr/bin/env bash

eval $(cat "/sys${DEVPATH}/device/uevent")

set > "/tmp/foo_$(echo "${PRODUCT}" | tr "/" "_").log"

if [ "${DRIVER}" = "snd_hda_intel" ]; then
	printf "onboard"
elif [ "${DRIVER}" = "snd-usb-audio" ]; then
	if [ "${PRODUCT}" = "8bb/2902/100" ]; then
		num="$(echo ${DEVPATH} | rev | cut -d'/' -f4 | rev | cut -d. -f2)"
		name="$(printf "uca222_%d" "${num}")"
		kill -9 $(ps auxwww | grep -v grep | grep zita | grep "hw:${name}" | awk '{print $2}') || true
		printf "%s" "${name}"
	elif [ "${PRODUCT}" = "1235/8200/41b" ]; then
		name="scarlett2i4"
		kill -9 $(ps auxwww | grep -v grep | grep zita | grep "hw:${name}" | awk '{print $2}') || true
		printf "%s" "${name}"
	elif [ "${PRODUCT}" = "a12/bc/1004" ]; then
		name="bcf2000"
		kill -9 $(ps auxwww | grep -v grep | grep zita | grep "hw:${name}" | awk '{print $2}') || true
		printf "%s" "${name}"
	elif [ "${PRODUCT}" = "a12/1004/2519" ]; then
		name="bluetooth"
		kill -9 $(ps auxwww | grep -v grep | grep zita | grep "hw:${name}" | awk '{print $2}') || true
		printf "%s" "${name}"
	else
		echo "drv: ${DRIVER}" >> /tmp/unknown-soundcards.txt
		echo "prd: ${PRODUCT}" >> /tmp/unknown-soundcards.txt
		printf "unknowndev_%04x" ${RANDOM}
	fi
else
	echo "drv: ${DRIVER}" >> /tmp/unknown-soundcards.txt
	echo "prd: ${PRODUCT}" >> /tmp/unknown-soundcards.txt
	printf "unknowndrv_%04x" ${RANDOM}
fi
