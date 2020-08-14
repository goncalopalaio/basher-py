import os
import subprocess

import xml.etree.ElementTree as ET
import re

ADB_VERBOSE = False

DEVICE_PORT = int(os.environ.get('UIAUTOMATOR_DEVICE_PORT', '9008'))
LOCAL_PORT = int(os.environ.get('UIAUTOMATOR_LOCAL_PORT', '9008'))
ANDROID_HOME = os.environ.get('ANDROID_HOME', '/Users/goncalopalaio/Library/Android/sdk')

ADB_EXEC_NAME = "adb.exe" if os.name == 'nt' else "adb"
ADB_ABS_CMD = os.path.join(ANDROID_HOME, "platform-tools", ADB_EXEC_NAME)

ADB_SERVER_HOST = 'localhost'
ADB_SERVER_PORT = '5037'

ADB_HOST_PORT_OPTIONS = []

if ADB_SERVER_HOST not in ['localhost', '127.0.0.1']:
	ADB_HOST_PORT_OPTIONS += ["-H", ADB_SERVER_HOST]

if ADB_SERVER_PORT != '5037':
	ADB_HOST_PORT_OPTIONS += ["-P", ADB_SERVER_PORT]

def adb_cmd_prepare(device_id, *args):
	if device_id:
		selected_device_id = ["-s", device_id]
	else:
		selected_device_id = []	

	line = [ADB_ABS_CMD]  + selected_device_id + ADB_HOST_PORT_OPTIONS + list(args)
	if os.name != "nt":
		line = [" ".join(line)]

	if ADB_VERBOSE:
		print(f"adb_cmd_prepare: {line}")
	
	return subprocess.Popen(line, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def adb_cmd_exec(device_id, *args):
	res = adb_cmd_prepare(device_id, *args).communicate()

	out = [] 
	for f in res:
		line = f.decode('utf-8', 'replace').strip()
		out.append(line)
	return out

def _parse_coordinate(str):
	str = str.replace("[", "").replace("]", "")
	str = str.split(",")

	return int(str[0]), int(str[1])

def _parse_node_bounds(bounds_str):
	# There's a better way to do this, probably.
	coords = re.findall('\[.*?\]', bounds_str)
	start_str = coords[0]
	end_str = coords[1]
	
	start_x, start_y = _parse_coordinate(start_str)
	end_x, end_y = _parse_coordinate(end_str)

	return start_x, start_y, end_x, end_y

def adb_get_center_of_nodes(nodes):
	centers = []
	for n in nodes:
		sx, sy, ex, ey = _parse_node_bounds(n.attrib["bounds"])
		cx = sx + (ex - sx) / 2
		cy = sy + (ey - sy) / 2
		centers.append((cx, cy))
	return centers

def adb_get_devices():
	res = adb_cmd_exec("", "devices -l")
	
	if res is None:
		print("No result?")
		return []
	
	res = res[0].split("\n")
	device_ids = []
	res = res[1:]
	for device in res:
		device_id = str(device.split(" ", 1)[0])
		device_ids.append(device_id)

	return device_ids

def adb_dump_views(device_id):
	res = adb_cmd_exec(device_id, "exec-out uiautomator dump /dev/tty")
	res = res[0]

	if "ERROR" in res:
		return None

	if res == "":
		print("Could not dump to tty directly. Falling back to file in the device")
		res = adb_cmd_exec(device_id, "exec-out uiautomator dump")		
		res = adb_cmd_exec(device_id, "shell cat /storage/emulated/legacy/window_dump.xml")
		res = res[0]
		
	res = res.replace("UI hierchary dumped to: /dev/tty", "")

	if not res:
		return None
	return ET.fromstring(res)

def adb_find_nodes_ending_with_id(tree, text):
	res = []
	for el in tree.findall(".//node[@resource-id]"):
		if el.attrib["resource-id"].endswith(text):
			res.append(el)

	if ADB_VERBOSE:
		print(f"Nodes ending with {text}")
		for nd in res:
			print("nd: %s %s enabled: %s" % (nd, _parse_node_bounds(nd.attrib["bounds"]), nd.attrib["enabled"]))
		print("---")

	return res

def adb_find_nodes_with_text(tree, text):
	res = []
	for el in tree.findall(".//node[@resource-id]"):
		if el.attrib["text"] == text:
			res.append(el)

	if ADB_VERBOSE:
		print("Nodes with text %s " % text)
		for nd in res:
			print("nd: %s %s enabled: %s" % (nd, _parse_node_bounds(nd.attrib["bounds"]), nd.attrib["enabled"]))
		print("---")

	return res

def adb_print_centers(id_str, centers):
	if not centers:
		return
	for cx, cy in centers:
		print("adb -s %s shell input tap %s %s " % (id_str, str(int(cx)), str(int(cy))))
