#!/usr/bin/env python

import socket
import threading
import time

global _FINISH;
_FINISH = False;

def doScan(str):
	# TODO: call motor/camera code
	#print("directory:", str);
	global _FINISH;
	for i in range(1, 11):
		if _FINISH:
			_FINISH = False;
			break;
		time.sleep(1)
		print(i)
	print('done')
	conn.send("done".encode());

def stopScan():
	global _FINISH;
	# TODO: call code to interrupt scan
	print("scan stopped");
	_FINISH = True;
	return;


#TCP_IP = '127.0.0.1' #localhost
TCP_IP = ''
TCP_PORT = 5005

#BUFFER_SIZE = 20  # Normally 1024, but we want fast response

#print('test0')
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#print('test1')
s.bind((TCP_IP, TCP_PORT))
#print('test2')
s.listen(1)

print('waiting for connections')

conn, addr = s.accept()
print('Connection address:', addr)
conn.send("Connected!".encode());
while 1:
	data = conn.recv(1024)
	if (not data):
		break;
	print("received data:", data)
	str = data.decode('UTF-8','strict');
	print("data as string=", str)
	if(str == "cancel"):
		stopScan();
	else:
		scan = threading.Thread(target=doScan, args=(str,)).start();
	conn.send(data)  # echo
conn.close()