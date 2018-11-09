import serial
import struct
from time import sleep, time
import csv
import sys
import os.path

#Constants
DISCONN_REQ = 2
ACK = 3
NAK = 4

#Globals
datasets = [];	#2d-array with each row corresponding to one dataset

ser = serial.Serial('/dev/ttyAMA0', 57600) #open port with baud rate

file_name = "datasets.csv"

if len(sys.argv) > 1:
    file_name = sys.argv[1]
else:
    print("Using default file name: {}".format(file_name))

print("Please plug in the Arduino power cable")

received_str = ""
while "Done" not in received_str:
	received_data = ser.readline()
	print(received_data)
	received_str = received_data.decode("utf-8")

while True:
	# ============ Connection HandShake ======================
	data = input("Enter a request ID: ")
	ser.reset_input_buffer()
	if (os.path.exists(file_name)):
		print(file_name, 'has not been renamed!')
		continue
	dataToSend = int(data).to_bytes(1,byteorder='big')
	ser.write(dataToSend)
	ser.flush()

	print("Waiting for ACK from Arduino")
	received_data = ser.read()
	#received_data = ser.readline()
	print(received_data)
	#print(type(received_data),received_data)
	received_data = int.from_bytes(received_data,byteorder='big')
	print(type(received_data),received_data)


	if (received_data == NAK):
		print("<Invalid request ID> Re-enter request ID")
	elif (received_data == ACK):	#if the data i received is not empty
		numDataset = int(input("Enter no. of seconds to receive: "))	#User define no .of seconds before terminating connection

		ackToArduino = ACK.to_bytes(1,byteorder='big')
		#print(ackToArduino, type(ackToArduino))
		ser.write(ackToArduino)
		print("Sent ACK for conn request ACK")

		# =================== Getting Data =======================
		line_count = 0
		
		startTime = time()
		endTime = startTime + numDataset
		while(time() < endTime):                        
			received_data = ser.read()	#Expects 1 byte packet containing buffer length to expect
			buffLen = int.from_bytes(received_data,byteorder='big')	#Convert byte to int
			#print(buffLen);
			ser.write(ACK.to_bytes(1,byteorder='big'))	#ACK for receiving the buffer length
			received_data = ser.read()	#Read in parity bit
			evenParityBit =  int.from_bytes(received_data, byteorder='big')
			received_data = ser.read(buffLen)
			line_count += 1
			#ser.write(ACK.to_bytes(1,byteorder='big')) #transmit acknowledge
			#print("-- Data received: --")

			#print(type(received_data),received_data)

			'''
			sleep(0.02)			# Wait for data to arrive => 20ms
			data_left = ser.in_waiting	 #check for remaining byte
			print("data left below: ")
			print(data_left)

			received_data += ser.read(data_left)
			'''

			#print("the readings below: ", len(received_data))
			#print(received_data)
			#print("----------------------");
			
			xorBit = 0
			for b in received_data:
				for k in range(8):
					xorBit ^= ((b >> k) & 1)

			#evenParityBit += 1	#Testing: To fail parity check
			#print('xorBit:',xorBit,'parityBit:',evenParityBit, xorBit == evenParityBit)
			if(xorBit == evenParityBit):
				numReading = int(buffLen/4)		#One reading occupies 4 bytes
				tmpArr = []
				for j in range(numReading-2):
					tmp = int.from_bytes(received_data[:4],byteorder='little', signed=True)	#Convert byte to int
					tmpArr.append(tmp/1000000)
					received_data = received_data[4:]                        
                                    
				#datasets.append(tmpArr)
				ser.write(ACK.to_bytes(1,byteorder='big')) #transmit acknowledge
				with open(file_name, 'a') as f:
					writer = csv.writer(f)
					writer.writerow(tmpArr)
				print(tmpArr)
			else:
				ser.write(NAK.to_bytes(1,byteorder='big'))
			
		print('No. of lines received:',line_count)

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
			print("Sent ACK for disconn request ACK")
		else:
			print("No ACK received for disconnection request")

		#for dataset in datasets:
			#print(dataset)


	else:
		print("Received neither ACK nor NAK from Arduino");
