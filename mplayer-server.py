import threading
import Queue
import socket
import select
import pymplb
import sys

host = ''
port = 50000

class SocketThread(threading.Thread):
	def __init__(self, queue):
		super(SocketThread, self).__init__()
		self.messageQueue = queue
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
					self.messageQueue.put(data)
				sockfd.close()

	def join(self, timeout=None):
		print "Leaving service thread"
		self.stoprequest.set()
		super(SocketThread, self).join(timeout)

class ControlThread(threading.Thread):
	def __init__(self, queue):
		super(ControlThread, self).__init__()
		self.queue = queue
		self.stoprequest = threading.Event()
		self.player = pymplb.MPlayer()

	def run(self):
		
		while True:
			try:
				data = self.queue.get(True, 0)
				print "Got data: %s" % data

				if "loadfile:" in data:
					path = data.split(":")[1]
					print "Got path: %s" % path
					self.player.loadfile(path)
				elif "pause" in data:
					print "pausing"
					print self.player.get_property('filename', pausing='pausing_toggle')
				
			except Queue.Empty:
				pass

	def join(self, timeout=None):
		print "Leaving control thread"
		self.stoprequest.set()
		super(ControlThread, self).join(timeout)

def sigint_handler(signal,frame):
	print("Caught ctrl-C; shutting down.")
	socketThread.join()
	sys.exit(0)

if __name__ == "__main__":

	queue = Queue.Queue()
	socketThread = SocketThread(queue=queue)
	socketThread.daemon = True
	socketThread.start()

	controlThread = ControlThread(queue=queue)
	controlThread.daemon = True
	controlThread.start()

	while True:
		pass

	