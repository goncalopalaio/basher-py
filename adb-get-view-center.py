#!/usr/bin/env python3

import argparse

from libs.adb import *

def main():
	parser = argparse.ArgumentParser(description="Runs 'uiautomator dump' and gets the center coordinates of the view using its id or text. This is done for all connected devices. The coordinates will be printed in the format of the adb shell input tap format.")
	parser.add_argument('-id', help='id or text of the view', required=True)
	parser.add_argument('-retries', help='Determines the number of times to attempt to retrieve the view information per device', default = 1)
	args = parser.parse_args()

	device_ids = adb_get_devices()
	
	for device_id in device_ids:
		print(f"\n# Device: {device_id}")

		found_nodes = False
		for retry in range(args.retries):
			tree = adb_dump_views(device_id)

			if not tree:
				print("Could not retrieve views. Continuing.")
				continue
			
			nodes = adb_find_nodes_ending_with_id(tree, args.id)
			centers = adb_get_center_of_nodes(nodes)
			found_nodes = found_nodes or centers
			adb_print_centers(device_id, centers)

			nodes = adb_find_nodes_with_text(tree, args.id)
			centers = adb_get_center_of_nodes(nodes)
			found_nodes = found_nodes or centers
			adb_print_centers(device_id, centers)
			
			if found_nodes:
				break

if __name__ == '__main__':
	main()