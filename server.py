#!/usr/bin/env python

import socket


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
while 1:
	data = conn.recv(1024)
	if (not data):
		break;
	print("received data:", data)
	conn.send(data)  # echo
conn.close()