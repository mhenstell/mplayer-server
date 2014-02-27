import threading
import Queue
import socket
import select
import pymplb
import sys
import time

host = ''
port = 50000

class SocketThread(threading.Thread):
	def __init__(self, incomingQueue, outgoingQueue):
		super(SocketThread, self).__init__()
		self.incomingQueue = incomingQueue
		self.outgoingQueue = outgoingQueue
		self.stoprequest = threading.Event()

	def run(self):
		server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
		server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		server_socket.bind((host, port))
		server_socket.listen(5)
		print "Listening on port %s" % port

		while not self.stoprequest.isSet():
				
			rr, rw, err = select.select([server_socket], [], [], 1)
			if rr:

				sockfd, addr = server_socket.accept()
				data = sockfd.recv(1024)
				if data:
					self.incomingQueue.put(data)
				time.sleep(.5)

				try:
					data = self.outgoingQueue.get(True, 0)
					sockfd.send(data)
				except Queue.Empty:
					sockfd.send("No response\n")
				finally:
					sockfd.close()

	def join(self, timeout=None):
		print "Leaving service thread"
		self.stoprequest.set()
		super(SocketThread, self).join(timeout)

class ControlThread(threading.Thread):
	def __init__(self, incomingQueue, outgoingQueue):
		super(ControlThread, self).__init__()
		self.incomingQueue = incomingQueue
		self.outgoingQueue = outgoingQueue
		self.stoprequest = threading.Event()
		self.player = pymplb.MPlayer()
		self.paused = False

	def run(self):
		
		while True:
			try:
				data = self.incomingQueue.get(True, 0)
				data = data.replace("\n", "")
				print "Got data: [%s]" % data

				try:
					command, param = data.split(":") #stupid
				except ValueError:
					print "Bad command format"
					self.outgoingQueue.put("Bad command format\n")
					continue

				ret = None

				if command == "loadfile": ret = self.loadfile(param)
				elif command == "status": ret = self.setStatus(param)
				elif command == "getProperty": ret = self.getProperty(param)

				if ret is not None:
					if ret is False:
						print "Error processing command"
						self.outgoingQueue.put("Error processing command\n")
					else:
						print "Success: %s\n" % ret
						self.outgoingQueue.put("Success: %s\n" % ret)
				else:
					print "Command not recognized (or returned None)"
					# self.outgoingQueue.put("Command not recognized\n")
				
			except Queue.Empty:
				pass

	def loadfile(self, path):
		self.player.loadfile(path)
		return True

	def getProperty(self, prop):
		return self.player.get_property(prop)

	def setStatus(self, param):
		if param == "stop": return self.player.stop()
		elif param == "pause": return self.player.pause()

	def join(self, timeout=None):
		print "Leaving control thread"
		self.stoprequest.set()
		super(ControlThread, self).join(timeout)

def sigint_handler(signal,frame):
	print("Caught ctrl-C; shutting down.")
	socketThread.join()
	sys.exit(0)

if __name__ == "__main__":

	incomingQueue = Queue.Queue()
	outgoingQueue = Queue.Queue()

	socketThread = SocketThread(incomingQueue=incomingQueue, outgoingQueue=outgoingQueue)
	socketThread.daemon = True
	socketThread.start()

	controlThread = ControlThread(incomingQueue=incomingQueue, outgoingQueue=outgoingQueue)
	controlThread.daemon = True
	controlThread.start()

	while True:
		pass

	