from flask import Flask
import socket
import pymplb

app = Flask(__name__)

player = pymplb.MPlayer()


@app.route("/")
def hello():
	return "Hello World!"

@app.route("/loadfile")
def loadfile():
	# client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	# client.connect(('localhost', 50000))
	# client.send("loadfile:/Volumes/Catbus/Downloads/big_buck_bunny_480p_h264.mov")
	# print client.recv(1024)

	return player.loadfile("/Volumes/Catbus/Downloads/big_buck_bunny_480p_h264.mov")

if __name__ == "__main__":
	app.debug = True
	app.run(port=8080)