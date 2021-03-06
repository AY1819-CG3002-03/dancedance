import serial
import struct
from time import sleep, time
import csv
import sys
import pandas as pd
import multiprocessing
import math
from sklearn.externals import joblib
from sklearn import preprocessing

# calc.py has to be in the same folder
import calc

#Constants
DISCONN_REQ = 2
ACK = 3
NAK = 4

#Globals
datasets = [];	#2d-array with each row corresponding to one dataset

ser = serial.Serial('/dev/ttyS0', 57600) #open port with baud rate

#############################====Ronald====#############################

# Need to specify in float because of python2/3 integer division problem
size = 2.0
sampling_period = 30.0
overlap = 50.0

# Load classifier
clf_file = "blah.pkl"
try:
    clf = joblib.load(clf_file)
except FileNotFoundError:
    print("Specified classifier file: {} is not found. ".format(clf_file),
          "Check that the file exists and is in the same directory as this script.")
    exit(1)

# input: dataframe
# return: int list
def calc_features(frame):
    acc_x = frame["acc_x"]
    acc_y = frame["acc_y"]
    acc_z = frame["acc_z"]
    gyro_x = frame["gyro_x"]
    gyro_y = frame["gyro_y"]
    gyro_z = frame["gyro_z"]
    flex_index = frame["flex_index"]
    flex_pinky = frame["flex_pinky"]

    gyro_correlation_1 = calc.correlation(gyro_x, gyro_y)
    gyro_correlation_2 = calc.correlation(gyro_x, gyro_z)
    gyro_correlation_3 = calc.correlation(gyro_y, gyro_z)

    acc_mean_x = calc.mean(acc_x)
    acc_mean_y = calc.mean(acc_y)
    acc_mean_z = calc.mean(acc_z)

    acc_std_x = calc.std(acc_x)
    acc_std_y = calc.std(acc_y)
    acc_std_z = calc.std(acc_z)

    acc_mad_x = calc.mad(acc_x)
    acc_mad_y = calc.mad(acc_y)
    acc_mad_z = calc.mad(acc_z)

    acc_max_x = calc.max(acc_x)
    acc_max_y = calc.max(acc_y)
    acc_max_z = calc.max(acc_z)

    acc_min_x = calc.min(acc_x)
    acc_min_y = calc.min(acc_y)
    acc_min_z = calc.min(acc_z)

    acc_iqr_x = calc.iqr(acc_x)
    acc_iqr_y = calc.iqr(acc_y)
    acc_iqr_z = calc.iqr(acc_z)

    acc_correlation_1 = calc.correlation(acc_x, acc_y)
    acc_correlation_2 = calc.correlation(acc_x, acc_z)
    acc_correlation_3 = calc.correlation(acc_y, acc_z)

    gyro_mean_x = calc.mean(gyro_x)
    gyro_mean_y = calc.mean(gyro_y)
    gyro_mean_z = calc.mean(gyro_z)

    gyro_std_x = calc.std(gyro_x)
    gyro_std_y = calc.std(gyro_y)
    gyro_std_z = calc.std(gyro_z)

    gyro_mad_x = calc.mad(gyro_x)
    gyro_mad_y = calc.mad(gyro_y)
    gyro_mad_z = calc.mad(gyro_z)

    gyro_max_x = calc.max(gyro_x)
    gyro_max_y = calc.max(gyro_y)
    gyro_max_z = calc.max(gyro_z)

    gyro_min_x = calc.min(gyro_x)
    gyro_min_y = calc.min(gyro_y)
    gyro_min_z = calc.min(gyro_z)

    gyro_iqr_x = calc.iqr(gyro_x)
    gyro_iqr_y = calc.iqr(gyro_y)
    gyro_iqr_z = calc.iqr(gyro_z)

    feature_frame = [
        acc_mean_x, acc_mean_y, acc_mean_z,
        acc_std_x, acc_std_y, acc_std_z,
        acc_mad_x, acc_mad_y, acc_mad_z,
        acc_max_x, acc_max_y, acc_max_z,
        acc_min_x, acc_min_y, acc_min_z,
        acc_iqr_x, acc_iqr_y, acc_iqr_z,
        acc_correlation_1, acc_correlation_2, acc_correlation_3,
        gyro_mean_x, gyro_mean_y, gyro_mean_z,
        gyro_std_x, gyro_std_y, gyro_std_z,
        gyro_mad_x, gyro_mad_y, gyro_mad_z,
        gyro_max_x, gyro_max_y, gyro_max_z,
        gyro_min_x, gyro_min_y, gyro_min_z,
        gyro_iqr_x, gyro_iqr_y, gyro_iqr_z,
        gyro_correlation_1, gyro_correlation_2, gyro_correlation_3
    ]

    return feature_frame

# takes in a list in string format
# returns a list of list in float
def input_conversion(temp):
    tempArr = []
    for item in temp:
        tempArr.append([float(val) for val in item.strip().split(",")])
    return tempArr


def classify(clf, input):
    return clf.predict(input)[0]


def window_length(size, period):
    milli = 3
    factor = 10 ** milli
    # need to round off the window length to a integer, decided to round down
    return math.floor((size*factor)/period) # number of rows in a dataframe

def load_classifier(clf_file):
    return joblib.load(clf_file)

def simulate(dance_file, sampling_period, window_size, overlap, clf_file):
    total = []
    length = window_length(window_size, sampling_period)
    clf = load_classifier(clf_file)
    start = 0
    increment = int(length - math.floor(length * (overlap / 100.0)))
    end = int(start + length)
    with open(dance_file, "r") as f:
        for line in f:
            total.append(line)
            if (len(total) % length == 0):
                temp = total[int(start):int(end)]
                # print("{} : {}".format(start, end))
                p = multiprocessing.Process(target=wrapper, args=(clf,temp))
                p.start()
                # wrapper(clf,df)
                start += increment
                end = start + length

    while (end <= len(total)):
        temp = total[int(start):int(end)]
        # print("{} : {}".format(start, end))
        p = multiprocessing.Process(target=wrapper, args=(clf, temp))
        p.start()
        # wrapper(clf,df)
        start += increment
        end = start + length

    print("END + {} + {}".format(end, length))


def wrapper(clf, temp):
    # tempArr = input_conversion(temp)
    # no need to call input conversion since datasets is already a list of list in float
    tempArr = temp
    df = pd.DataFrame(tempArr)

    df.columns = ["acc_x", "acc_y", "acc_z",
                  "gyro_x", "gyro_y", "gyro_z",
                  "flex_index", "flex_pinky"]
    features = calc_features(df)
    norm_features = preprocessing.normalize([features])
    res = classify(clf, norm_features)
    print("This is the returned class: {}".format(res))
    # return res


frame_size = window_length(size, sampling_period)
increment = int(frame_size - math.floor(frame_size * (overlap / 100.0)))
start = 0
end = start + frame_size
#######################################################################################

while True:
    # ============ Connection HandShake ======================
    data = input("Enter a request ID: ")
    ser.reset_input_buffer()
    dataToSend = int(data).to_bytes(1,byteorder='big')
    ser.write(dataToSend)
    ser.flush()

    received_data = ser.read()
    # print(type(received_data),received_data)
    received_data = int.from_bytes(received_data,byteorder='big')
    # received_data = int.from_bytes(received_data,byteorder='big')	#Convert byte to int
    # print(type(received_data),received_data)


    if (received_data == NAK):
        print("<Invalid request ID> Re-enter request ID")
    elif (received_data == ACK):    # if the data i received is not empty
        numDataset = int(input("Enter no. of seconds to receive: "))	# User define no .of seconds before terminating connection
        startTime = time()
        endTime = startTime + 5

        ackToArduino = ACK.to_bytes(1,byteorder='big')
        # print(ackToArduino, type(ackToArduino))
        ser.write(ackToArduino)
        print("Sent ACK for conn request ACK")

        # =================== Getting Data =======================

        # Ronald: I am assuming the getting data part is going to run endlessly in our final program
        # Disconnect on maybe keyboard interrupt? wrap the entire code in try block catch keyboard interrupt ^.^
        # Execute disconnection code on keyboard interrupt

        i = 0
        while(time() < endTime):
            received_data = ser.read()	# Expects 1 byte packet containing buffer length to expect
            buffLen = int.from_bytes(received_data,byteorder='big')	#Convert byte to int
            print(buffLen);
            ser.write(ACK.to_bytes(1,byteorder='big'))	# ACK for receiving the buffer length
            received_data = ser.read()	# Read in parity bit
            evenParityBit =  int.from_bytes(received_data, byteorder='big')
            received_data = ser.read(buffLen)
            print("-- Data received: --")

            # print(type(received_data),received_data)

            '''
            sleep(0.02)			# Wait for data to arrive => 20ms
            data_left = ser.in_waiting	 #check for remaining byte
            print("data left below: ")
            print(data_left)
            received_data += ser.read(data_left)
            '''

            # print("the readings below: ", len(received_data))
            print(received_data)
            print("----------------------");

            xorBit = 0
            for b in received_data:
                for k in range(8):
                    xorBit ^= ((b >> k) & 1)

            # evenParityBit += 1	#Testing: To fail parity check
            print('xorBit:',xorBit,'parityBit:',evenParityBit, xorBit == evenParityBit)
            if(xorBit == evenParityBit):
                numReading = int(buffLen/4)		# One reading occupies 4 bytes
                tmpArr = []
                for j in range(numReading):
                    tmp = int.from_bytes(received_data[:4],byteorder='little', signed=True)	#Convert byte to int
                    tmpArr.append(tmp/1000000)
                    received_data = received_data[4:]
                datasets.append(tmpArr)

                # with open('dataset.csv', 'a') as f:
                #     writer = csv.writer(f)
                #     writer.writerow(tmpArr)

                ################################################################################
                # Ronald: Following block is my added code
                if (len(datasets) != 0) and (len(datasets) % frame_size == 0):
                    # maybe i shouldnt do it this way, not sure about RPI processing power
                    temp = datasets[int(start):int(end)]
                    p = multiprocessing.Process(target=wrapper, args=(clf, temp))
                    p.start()
                    start += increment
                    end = start + frame_size
                ################################################################################

                ser.write(ACK.to_bytes(1,byteorder='big')) # transmit acknowledge
            else:
                i -= 1
                ser.write(NAK.to_bytes(1,byteorder='big'))
            i += 1

        # ================= Disconnection handshake =================
        ser.read()					# Wait for Arduino to send data, indicating its waiting for a byte
        # ser.reset_input_buffer()			# Clear input buffer to wait for ACK from Arduino
        ser.write(DISCONN_REQ.to_bytes(1,byteorder='big'))
        received_data = ser.read()
        # print(type(received_data),received_data)
        received_data = int.from_bytes(received_data,byteorder='big')	# Convert byte to int
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
