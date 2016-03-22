#!/usr/bin/env python
"""Quick command line python app to get a video stream from a GoPro Hero 4

Launch this script from the command line with a numerical input argument for the number of the camera you want to connect to e.g.
 	./streamGoPro.py 1

Creates 2 processes:
1) A heartbeat, which pings the camera every 2s to keep the connection alive (code based on: https://gist.github.com/3v1n0/38bcd4f7f0cb3c279bad#file-hero4-udp-keep-alive-send-py)
2) A call to ffplay to start streaming over udp

Ensures a connection to the camera with a server callback check on startup.

Requires:
ffmpeg
brew install ffmpeg --with-ffplay
"""
import socket
import sys
import urllib
from time import sleep
from multiprocessing import Process
from subprocess import call, check_output

wifiName = 'cosanlab' + str(sys.argv[1])
wifiPw = '00000000'

def switchWifi(ssid,pw):
	print "Trying to connect to " + ssid + "..."
	currentNetwork = check_output([
		'networksetup','-getairportnetwork','en0'])
	if currentNetwork.strip('Current Wi-Fi Network: \n.') == ssid:
		print 'Already connected to ' + ssid + '!'
		return
	else:
		out = check_output([
			'networksetup','-setairportnetwork','en0',ssid,pw])
		if 'Could not find network' in out:
			raise Exception(out)
		elif not out:
			print "Connection successful!"

def get_command_msg(id):
	return "_GPHD_:%u:%u:%d:%1lf\n" % (0, 0, 2, 0)


def keepAlive():
	UDP_IP = "10.5.5.9"
	UDP_PORT = 8554
	KEEP_ALIVE_PERIOD = 2500
	KEEP_ALIVE_CMD = 2
	MESSAGE = get_command_msg(KEEP_ALIVE_CMD)

	print("UDP target IP:", UDP_IP)
	print("UDP target port:", UDP_PORT)
	print("message:", MESSAGE)

	if sys.version_info.major >= 3:
		MESSAGE = bytes(MESSAGE, "utf-8")

	print "Starting Heartbeat..."
	while True:
		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		sock.sendto(MESSAGE, (UDP_IP, UDP_PORT))
		sleep(KEEP_ALIVE_PERIOD/1000)

def startStream():
	print 'Starting stream in 5s...'
	sleep(5)
	call('ffplay -fflags nobuffer -f:v mpegts -probesize 8192 udp://:8554', shell=True)

def checkCallBack():
	print 'Pinging GoPro in 2s...'
	sleep(2)
	reply = urllib.urlopen('http://10.5.5.9/gp/gpControl/execute?p1=gpStream&c1=restart').read()
	goodCallBack = '{"status":"0"}\n\n'
	attempts = 0
	while reply != goodCallBack and attempts < 6:
		attempts += 1
		print 'GoPro replied with bad response code retrying in 1 second... attempt ' + str(attempts) +'...'
		sleep(1)
		reply = urllib.urlopen('http://10.5.5.9/gp/gpControl/execute?p1=gpStream&c1=restart').read()
	if attempts < 6:
		print "GoPro reply success!"
		return
	else:
		print "Attemped " + str(attempts) + " times, but still got bad reply\n"
		print "Trying to reset GoPro streaming service..."
		urllib.urlopen('http://10.5.5.9/gp/gpControl/execute?p1=gpStream&c1=stop')
		sleep(1)
		reply = urllib.urlopen('http://10.5.5.9/gp/gpControl/execute?p1=gpStream&c1=restart').read()
		while reply != goodCallBack and attempts < 12:
			attempts += 1
			print 'GoPro replied with bad response code retrying in 1 second... attempt ' + str(attempts) + '...'
			sleep(2)
			reply = urllib.urlopen('http://10.5.5.9/gp/gpControl/execute?p1=gpStream&c1=restart').read()
		raise Exception('Could not connect to GoPro streaming service!')

if __name__ == '__main__':
	try:
		switchWifi(wifiName, wifiPw)
		checkCallBack()
		Process(target=keepAlive).start()
		Process(target=startStream).start()
	except KeyboardInterrupt:
		print 'Stream Ended'
