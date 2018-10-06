import serial
import struct
from time import sleep 
import sys

ser = serial.Serial('/dev/ttyS0', 19200) #open port with baud rate

while True:

	data = input("Enter a number: ")
	#dataToSend = struct.pack('>B',int(data))
	dataToSend = str(data).encode('ascii') #to initiate connection with arduino
	print(type(dataToSend), dataToSend)
	ser.write(dataToSend)
	ser.flush()
	
	#print(type(data))

	received_data = ser.read()
	print(type(received_data),received_data)


	if (received_data == b'\x03'): #if the data i received is not empty
		print("AM I HERE")
		ackToArduino = str('3').encode('ascii')
		print(":ALLALA")
		print(ackToArduino, type(ackToArduino))
		ser.write(ackToArduino)
		print("sdjnkasndk")


	while (ser.read() != ''):

		received_data = ser.read(4)
		print("first received:")
		print(received_data)
		#print(type(received_data))
		#print(len(received_data))
		#sleep(0.03)
		data_left = ser.inWaiting() #check for remaining byte
		print("data left below: ")
		print(data_left)

		received_data += ser.read(data_left)
		print("the readings below: ")
		print(received_data)
		ackToArduino = str('3').encode('ascii')
		ser.write(ackToArduino) #transmit acknowledge
