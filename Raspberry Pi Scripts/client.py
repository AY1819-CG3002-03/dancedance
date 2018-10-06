import time
import socket
import json
from base64 import b64encode
from Crypto.Cipher import AES
from Crypto import Random
from Crypto.Util.Padding import pad
import base64, os

####### BEGIN HERE #######
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host = '172.20.10.3'
port = 8080
s.connect((host,port))

while True:

	private_msg = """#turnclap | 3V | 1.5A | 1.5W | 2.1W""" #34 bytes
	private_msg = bytes(private_msg,'utf-8')
	padding_character = "{"

	secret_key = b"sixteen byte key"
	iv = Random.new().read(AES.block_size)
	cipher = AES.new(secret_key, AES.MODE_CBC,iv)
	padded = pad(private_msg, AES.block_size)
	print(private_msg)
	print(len(private_msg))
	print(padded)
	print(len(padded))
	ct_bytes = cipher.encrypt(pad(private_msg, AES.block_size))
	ct = base64.b64encode(iv + ct_bytes)

	print(secret_key)
	print(iv)
	print(len(iv))
	print("cipher ")
	print(cipher)
	print(ct_bytes)
	print(len(ct_bytes))
	print(ct)
	print(len(ct))

	msg = s.send(ct)
	time.sleep(20)
