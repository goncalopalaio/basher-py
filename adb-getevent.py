#!/usr/bin/env python3

import sys
import argparse
import time
import re

from libs.input_event_codes import *

ABS_MT_POSITION_X = "ABS_MT_POSITION_X"
ABS_MT_POSITION_Y = "ABS_MT_POSITION_Y"

def convert_hex_to_int(hex_value):
	return int('0x' + hex_value, 0)

def convert_event_data_to_int(value):
	if value in EVENT_DATA:
		return EVENT_DATA[value]
	return convert_hex_to_int(value)

def convert_input_event_code_to_int(value):
	success = False
	if str(value) in INPUT_EVENT_CODES:
		success = True
		value = INPUT_EVENT_CODES[str(value)]
	return (success, value)

def parse_event(line):
	components = re.split('\s+', line)
	
	if ABS_MT_POSITION_X in line:
		return (ABS_MT_POSITION_X, convert_hex_to_int(components[3]))
	elif ABS_MT_POSITION_Y in line:
		return (ABS_MT_POSITION_Y, convert_hex_to_int(components[3]))

	return (None, None)

def transform_to_adb_shell_sendevent(line):
	components = re.split('\s+', line)
	
	if len(components) != 4:
		return

	device = components[0]
	b = components[1]
	c = components[2]
	d = components[3]

	# Add a marker when the home key is pressed ince the adb shell getevent command might not immediatly give us the output. This will make it easier to know when the user actions actually started (For example after your sequence of events press the home button).
	if c.startswith("KEY_") or c.startswith("BTN_"):
		print(f"# Pressed {c}")


	b_succeed, b = convert_input_event_code_to_int(components[1])
	c_succeed, c = convert_input_event_code_to_int(components[2])

	if b_succeed and c_succeed:

		# Remove trailing ':'
		device = device.replace(":", "") 

		d = convert_event_data_to_int(components[3].strip())

		# Convert into a command that replicates the event
		print(f"adb shell sendevent {device} {b} {c} {d}")

		# Note that sendevent is pretty slow by default:
		# https://stackoverflow.com/a/54547196/868164

		# Here's an example of how to actually push a binary and have permissions to run the executable:
		# https://github.com/Cartucho/android-touch-record-replay
		# adb push mysendevent /data/local/tmp/
		# adb shell chmod +x /data/local/tmp/mysendevent
		# adb shell /data/local/tmp/mysendevent

	else:
		# print(f"Error: Could not perform full conversion -> {b} {c} {d}")
		pass


# Notes:
# It appears that adb shell getevent -l doesn't immediately produces the output. It's likely that it's buffering it's output.
# Since sdk 23 we have exec-out which doesn't do buffering? (https://github.com/Cartucho/android-touch-record-replay/blob/master/record_touch_events.sh)	

def main():
	parser = argparse.ArgumentParser(description="""
	Transforms the output of 'adb shell getevent -l' into a human readable format.

	By default it only prints the X, Y coordinates that were tapped on the screen.
	This is useful to use with 'adb shell input tap X Y'
	Keep in mind that getevent outputs all events in the system and a XY,XY,XY, etc. order is not guaranteed in this case (It appears that the touchscreen sensor events are only reported if there's a change in the values).

	Example:
	adb shell getevent -l | python3 adb-getevent.py
	""")
	parser.add_argument('-t', '--include-time', help='Include time on seconds between events in the output.', action='store_true')
	parser.add_argument('-v', '--verbose', help='Print event data.', action='store_true')
	parser.add_argument('-f', '--full', help='When set it will format all events that were received in the adb shell sendevent command format. By default only X, Y taps are displayed.', action='store_true')
	args = parser.parse_args()


	time_start = time.time()
	for line in sys.stdin:
		line = line.strip()

		time_end = time.time()
		time_diff_secs = round(time_end - time_start, 3)
		if args.include_time and time_diff_secs > 0:
			print(f"sleep {time_diff_secs}")

		field, coordinate = parse_event(line)

		if args.verbose:
			print(f"line: ${line} field: {field} coordinate: {coordinate}")

		if not args.full:
			if field:
				# This is assuming that Y always comes after X
				if field == ABS_MT_POSITION_Y:
					print(f"Y -> {coordinate}")
				
				elif field == ABS_MT_POSITION_X:
					print(f"X -> {coordinate}")

		else:
			transform_to_adb_shell_sendevent(line)

		time_start = time.time()


if __name__ == '__main__':
	main()