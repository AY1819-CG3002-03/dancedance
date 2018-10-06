import serial
import struct
from time import sleep
import csv
import sys

#Constants
DISCONN_REQ = 2
ACK = 3
NAK = 4

#Globals
datasets = [];	#2d-array with each row corresponding to one dataset

ser = serial.Serial('/dev/ttyS0', 57600) #open port with baud rate

while True:
	# ============ Connection HandShake ======================
	data = input("Enter a request ID: ")
	ser.reset_input_buffer()
	dataToSend = int(data).to_bytes(1,byteorder='big')
	ser.write(dataToSend)
	ser.flush()

	received_data = ser.read()
	#print(type(received_data),received_data)
	received_data = int.from_bytes(received_data,byteorder='big')
	#received_data = int.from_bytes(received_data,byteorder='big')	#Convert byte to int
	#print(type(received_data),received_data)


	if (received_data == NAK):
		print("<Invalid request ID> Re-enter request ID")
	elif (received_data == ACK):	#if the data i received is not empty
		numDataset = int(input("Enter no. of dataset to receive: "))	#User define no .of dataset before terminating connection
		ackToArduino = ACK.to_bytes(1,byteorder='big')
		#print(ackToArduino, type(ackToArduino))
		ser.write(ackToArduino)
		print("Sent ACK for conn request ACK")

		# =================== Getting Data =======================
		i = 0
		while(i < numDataset):
			received_data = ser.read()	#Expects 1 byte packet containing buffer length to expect
			buffLen = int.from_bytes(received_data,byteorder='big')	#Convert byte to int
			print(buffLen);
			ser.write(ACK.to_bytes(1,byteorder='big'))	#ACK for receiving the buffer length



			received_data = ser.read()	#Read in parity bit
			evenParityBit =  int.from_bytes(received_data, byteorder='big')
			received_data = ser.read(buffLen)
			print("-- Data received: --")

			#print(type(received_data),received_data)

			'''
			sleep(0.02)			# Wait for data to arrive => 20ms
			data_left = ser.in_waiting	 #check for remaining byte
			print("data left below: ")
			print(data_left)

			received_data += ser.read(data_left)
			'''

			#print("the readings below: ", len(received_data))
			print(received_data)
			print("----------------------");

			xorBit = 0
			for b in received_data:
				for k in range(8):
					xorBit ^= ((b >> k) & 1)

			#evenParityBit += 1	#Testing: To fail parity check
			print('xorBit:',xorBit,'parityBit:',evenParityBit, xorBit == evenParityBit)
			if(xorBit == evenParityBit):
				numReading = int(buffLen/4)		#One reading occupies 4 bytes
				tmpArr = []
				for j in range(numReading):
					tmp = int.from_bytes(received_data[:4],byteorder='little', signed=True)	#Convert byte to int
					tmpArr.append(tmp/1000000)
					received_data = received_data[4:]
				datasets.append(tmpArr)
				with open('dataset.csv', 'a') as f:
					writer = csv.writer(f)
					writer.writerow(tmpArr)

				ser.write(ACK.to_bytes(1,byteorder='big')) #transmit acknowledge
			else:
				i -= 1
				ser.write(NAK.to_bytes(1,byteorder='big'))
			i += 1

		# ================= Disconnection handshake =================
		ser.read()					#Wait for Arduino to send data, indicating its waiting for a byte
		#ser.reset_input_buffer()			#Clear input buffer to wait for ACK from Arduino
		ser.write(DISCONN_REQ.to_bytes(1,byteorder='big'))
		received_data = ser.read()
		#print(type(received_data),received_data)
		received_data = int.from_bytes(received_data,byteorder='big')	#Convert byte to int
		if(received_data == ACK):
			print("ACK received for disconnection request")
			ser.write(ACK.to_bytes(1,byteorder='big'))
			print("Sent ACK for disconn requst ACK")
		else:
			print("No ACK received for disconnection request")

		for dataset in datasets:
			print(dataset)


	else:
		print("Received neither ACK nor NAK from Arduino");
