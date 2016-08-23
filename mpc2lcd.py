import sys
import glob
import serial
import time
import subprocess
import threading
import time as t
from mpd import MPDClient
import traceback
import mpd

#Global Variables
ser = None
rcommand = None
killprocess = False
client = None
client1 = None
songTime = "--:--"

stopSongTracker = False
songTrackerRunning = False
songTrackerCurrentSongID = 0
songTrackerCurrentSongTitle = ""
songTrackerPlaylistLength = 0

def updateLCD():
	"""This function will be executed via thread"""
	global ser
	global client1
	global stopSongTracker
	global songTrackerRunning
	global songTrackerCurrent
	global songTrackerCurrentSongID
	global songTrackerCurrentSongTitle
	global songTrackerPlaylistLength

	state = ""
	stateSent = False
	titleSent = False
	songIdSent = False
	plLengthSent = False

	try:
		while 1:
			if(not client1.currentsong()):
				sendSerial("state", "")
				time.sleep(0.01);
				sendSerial("song", "")
				time.sleep(0.01);
				sendSerial("playtimeremaining", "")
				time.sleep(0.01);
				sendSerial("songid", "")
				time.sleep(0.01);
				sendSerial("playlistlength", "")
				print("Player inactive!")
				stopSongTracker = True
				time.sleep(0.5)
				while(not client1.currentsong()):
					time.sleep(1)
					continue
				#~ raise Exception
				
			if(state!=client1.status()["state"]):
				state = client1.status()["state"]
				stateSent = False

			if(state=="stop"):
				if(not stateSent):
					if sendSerial("state", state):
						stateSent = True
					sendSerial("playtimeremaining", "")
				raise Exception

			songTrackerPlaylistLength = client1.status()["playlistlength"]
			if(songTrackerCurrentSongID!=str(int(client1.status()["song"])+1)):
				songTrackerCurrentSongID = str(int(client1.status()["song"])+1)
				songTrackerCurrentSongTitle = client1.currentsong()["title"]
				titleSent = False
				stateSent = False
				songIdSent = False
				plLengthSent = False
				
				print("[%s/%s] %s" % (songTrackerCurrentSongID, songTrackerPlaylistLength, songTrackerCurrentSongTitle))
				
			if(state=="play"):
				if(not stateSent):
					if sendSerial("state", state):
						stateSent = True
				if(not songIdSent):
					if sendSerial("songid", str(int(client1.status()["song"])+1)):
						songIdSent = True
				if(not plLengthSent):
					if sendSerial("playlistlength", client1.status()["playlistlength"]):
						plLengthSent = True
				if(not titleSent):
					if sendSerial("song", client1.currentsong()["title"]):
						titleSent = True
				
			if(state=="pause"):
				if(not stateSent):
					if sendSerial("state", state):
						stateSent = True
				if(not songIdSent):
					if sendSerial("songid", str(int(client1.status()["song"])+1)):
						songIdSent = True
				if(not plLengthSent):
					if sendSerial("playlistlength", client1.status()["playlistlength"]):
						plLengthSent = True
				if(not titleSent):
					if sendSerial("song", client1.currentsong()["title"]):
						titleSent = True
					
					songTime = int(client1.status()["time"].split(":")[1])
					elapsedTime = int(client1.status()["time"].split(":")[0])
					if(songTime>=elapsedTime):
						playtimeremaining = songTime - elapsedTime
						m = int(playtimeremaining / 60)
						s = playtimeremaining % 60
						outdata = "%02d:%02d" % (m, s)
						sendSerial("playtimeremaining", outdata)
					else:
						sendSerial("playtimeremaining", "")
				if stopSongTracker:
					raise Exception
				if killprocess:
					raise KeyboardInterrupt
				time.sleep(0.5)
				continue

			if stopSongTracker:
				raise Exception
			if killprocess:
				raise KeyboardInterrupt
				
			songTrackerRunning = True
			while client1.status()["state"]=="play":
				if(not stateSent):
					if sendSerial("state", state):
						stateSent = True
				if(not stateSent):
					if sendSerial("state", state):
						stateSent = True
				if(not songIdSent):
					if sendSerial("songid", str(int(client1.status()["song"])+1)):
						songIdSent = True
				if(not plLengthSent):
					if sendSerial("playlistlength", client1.status()["playlistlength"]):
						plLengthSent = True
				if(not titleSent):
					if sendSerial("song", client1.currentsong()["title"]):
						titleSent = True
				if(songTrackerCurrentSongID!=client1.currentsong()["id"]):
					break
					
				songTime = int(client1.status()["time"].split(":")[1])
				elapsedTime = int(client1.status()["time"].split(":")[0])

				if(songTime>=elapsedTime):
					playtimeremaining = songTime - elapsedTime
					m = int(playtimeremaining / 60)
					s = playtimeremaining % 60
					outdata = "%02d:%02d" % (m, s)
					sendSerial("playtimeremaining", outdata)
				else:
					sendSerial("playtimeremaining", "")

				if stopSongTracker:
					raise Exception
				if killprocess:
					raise KeyboardInterrupt
				time.sleep(1)
	except (SerialException):
		traceback.print_exc()
		pass
	except (Exception):
		traceback.print_exc()
		pass
	except (KeyboardInterrupt):
		traceback.print_exc()
		ser.close()
	finally:
		songTime = ""
		songTrackerCurrentSongID = 0
		songTrackerCurrentSongTitle = ""
		songTrackerRunning = False
		#~ try:
			#~ client1.close()
			#~ client1.disconnect()
		#~ except:
			#~ pass
		exit()
	return

def takeInput():
	"""This function will be executed via thread"""
	global rcommand
	global ser
	try:
		while True:
			result = ser.readline()
			remotecommand = result.rstrip('\r\n').lower()
			if rcommand!=remotecommand and remotecommand!="":
				rcommand = remotecommand
				if rcommand == "right":                
					p = subprocess.Popen(["mpc", "next"], stdout=subprocess.PIPE)
				elif rcommand == "left":
					p = subprocess.Popen(["mpc", "prev"], stdout=subprocess.PIPE)
				elif rcommand == "select":
					p = subprocess.Popen(["mpc", "toggle"], stdout=subprocess.PIPE)
				elif rcommand == "up":
					p = subprocess.Popen(["mpc", "volume", "+5"], stdout=subprocess.PIPE)
				elif rcommand == "down":
					p = subprocess.Popen(["mpc", "volume", "-5"], stdout=subprocess.PIPE)
				rcommand = None
			if killprocess:
				raise KeyboardInterrupt
			time.sleep(0.5)
	except (SerialException):
		traceback.print_exc()
		pass
	except (KeyboardInterrupt):
		ser.close()
	finally:
		exit()
	return

def sendSerial(key, message):
	global ser
	transfersuccess = False
	if key!=None and key!="":
		tries = 0
		while( not transfersuccess ):
			if key!="playtimeremaining":
				print("Sending key: %s | %s" % (key, message[:128]))
			ser.write("%s|%s\n" % (key, message[:128]))
			time.sleep(0.05)
			result = ser.readline()
			response = result.rstrip('\r\n').lower()
			if response=="ok":
				transfersuccess = True
				if key!="playtimeremaining":
					print("Response OK")
				break
			else:
				transfersuccess = False
				tries = tries + 1
				if tries>30:
					break
	return transfersuccess



def get_device_serial_port():
	global ser
	global killprocess
	""" Lists serial port names

		:raises EnvironmentError:
			On unsupported or unknown platforms
		:returns:
			A list of the serial ports available on the system
	"""
	if sys.platform.startswith('win'):
		ports = ['COM%s' % (i + 1) for i in range(256)]
	elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
		# this excludes your current terminal "/dev/tty"
		ports = glob.glob('/dev/tty[A-Za-z]*')
	elif sys.platform.startswith('darwin'):
		ports = glob.glob('/dev/tty.*')
	else:
		raise EnvironmentError('Unsupported platform')

	for strport in ports:
		try:
#           print("Testing device " + strport)
			ser = serial.Serial(
				port = strport,\
				baudrate=9600,\
				parity=serial.PARITY_NONE,\
				stopbits=serial.STOPBITS_ONE,\
				bytesize=serial.EIGHTBITS,\
				timeout=0)
#           print("connected to: " + ser.portstr + ". Waiting for response...")
			while 1:
				result = ser.readline()
				remotecommand = result.rstrip('\r\n').lower()
				if remotecommand == "ready":
					sendSerial("title", "*Music Machine*")
					time.sleep(1)
					break
			break
		except (OSError, serial.SerialException):
			pass
	return None

# Detect device and connect to serial port
get_device_serial_port()

if ser!=None:
#   print("Waiting for remote command")
	print("*MUSIC MACHINE*")

	client = MPDClient()
	client.connect("localhost", 6600)
	client1 = MPDClient()
	client1.connect("localhost", 6600)
	
	lastcommand = ""
	remotecommand = ""

	thread1 = threading.Thread(target=takeInput)
	thread1.start()

	firstIteration = True
	while 1:
		try:
			if(firstIteration):
				firstIteration = False
				state = ["player"]
			else:
				client.send_idle()
				time.sleep(0.3)
				state = client.fetch_idle()
				
			if (state[0] == 'player'):
				try:
					station = client.currentsong()['name']
				except KeyError:
					station = ''

				try:
					title = client.currentsong()['title']
				except KeyError:
					title = ''
				try:
					artist = client.currentsong()['artist']
					if isinstance(artist, list):
						artist = artist[0]
				except KeyError:
					artist = ''
					
				try:
					songid = str(int(client.status()["song"])+1)
				except KeyError:
					songid = '0'
					
				try:
					playlistlength = client.status()["playlistlength"]
				except KeyError:
					playlistlength = '0'
					
				try:
					repeat = client.status()["repeat"]
				except KeyError:
					repeat = '0'
					
				try:
					consume = client.status()["consume"]
				except KeyError:
					consume = '0'
					
				try:
					shuffle = client.status()["random"]
				except KeyError:
					shuffle = '0'
					
				try:
					state = client.status()["state"]
					if(state=="play" or state=="pause"):
						if(not songTrackerRunning):
							stopSongTracker = False
							thread2 = threading.Thread(target=updateLCD)
							thread2.start()
					elif(state=="stop" or state=="" and not client.currentsong()):
						stopSongTracker = True
						if(not songTrackerRunning):
							thread2 = threading.Thread(target=updateLCD)
							thread2.start()
				except KeyError:
					state = ''
					
				try:
					volume = client.status()["volume"]
				except KeyError:
					volume = '0'
		
				try:
					songtime = client.currentsong()["time"]
				except KeyError:
					songtime = '0'
					
				try:
					elapsedtime = client.currentsong()["pos"]
				except KeyError:
					elapsedtime = '0'
					
		except (Exception):
			killprocess = True
			pass
		except KeyboardInterrupt:
			killprocess = True
			print("\nStopped")
			break
	try:
		client.close()
		client.disconnect()
	except mpd.ConnectionError:
		pass

	try:
		client1.close()
		client1.disconnect()
	except mpd.ConnectionError:
		pass
		
	ser.close()
	print("Connection closed")
else:
	print("Device not found")
