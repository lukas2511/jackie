#!/bin/bash

# Recreate audio devices after jackd restart without disturbing (most) pulseaudio clients

# At least in my setup only spotify has to be restarted as it has configured a fixed sink
# and can't fallback to the dummy (no-device) sink as other applications would do

grep "load devices" ~/.config/pulse/default.pa -A9999 \
	| grep -v '^#' \
	| grep -v '^$' \
	| while read line; do
		pacmd ${line}
	done
