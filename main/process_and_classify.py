import serial
import struct
import csv
import sys
import pandas as pd
import numpy as np
import multiprocessing
import math
from sklearn.externals import joblib
from sklearn import preprocessing
import time
import socket
import json
from base64 import b64encode
from Cryptodome.Cipher import AES
from Cryptodome import Random
from Cryptodome.Util.Padding import pad
import base64, os

# calc.py has to be in the same folder
import calc

#Constants
DISCONN_REQ = 2
ACK = 3
NAK = 4

#Globals
datasets = [];	#2d-array with each row corresponding to one dataset

ser = serial.Serial('/dev/ttyAMA0', 57600) #open port with baud rate

#############################====Ronald====#############################

size = 2.4
sampling_period = 30.0
overlap = 50.0
default_model = "random_sp30_ws1_8_o50_flex_neutral_everyone_fs80.pkl"

# Take in sys.argv
host = sys.argv[1]
port = int(sys.argv[2])

# Load classifier
if len(sys.argv) < 4 or "pkl" not in sys.argv[3]:
    print("Using default model file: {}".format(default_model))
    clf_file = default_model
else:
    clf_file = sys.argv[3]
clf = joblib.load(clf_file)

if "flex" in clf_file:
    flex = True
else:
    flex = False
    

def map(res):
    label_map = ["wipers", "turnclap", "sidestep", "chicken", "number7", "neutral"]
    return label_map[res-1]


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

def calc_features_flex(frame):

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

    mean_flex_index = calc.mean(flex_index)
    mean_flex_pinky = calc.mean(flex_pinky)

    std_flex_index = calc.std(flex_index)
    std_flex_pinky = calc.std(flex_pinky)

    mad_flex_index = calc.mad(flex_index)
    mad_flex_pinky = calc.mad(flex_pinky)

    max_flex_index = calc.max(flex_index)
    max_flex_pinky = calc.max(flex_pinky)

    min_flex_index = calc.min(flex_index)
    min_flex_pinky = calc.min(flex_pinky)

    iqr_flex_index = calc.iqr(flex_index)
    iqr_flex_pinky = calc.iqr(flex_pinky)
    
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
        gyro_correlation_1, gyro_correlation_2, gyro_correlation_3,
        mean_flex_index, mean_flex_pinky,
        std_flex_index, std_flex_pinky,
        mad_flex_index, mad_flex_pinky,
        max_flex_index, max_flex_pinky,
        min_flex_index, min_flex_pinky,
        iqr_flex_index, iqr_flex_pinky
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


def send(dance_result, s, voltage, current, power, energy, curTime):
    private_msg = "#{} | {}V | {}A | {}W | {}Wh | {}".format(dance_result, voltage, current, power, energy, curTime)  # 34 bytes
    private_msg = bytes(private_msg, 'utf-8')
    padding_character = "{"
    secret_key = b"sixteen byte key"
    iv = Random.new().read(AES.block_size)
    cipher = AES.new(secret_key, AES.MODE_CBC, iv)
    padded = pad(private_msg, AES.block_size)
    ct_bytes = cipher.encrypt(pad(private_msg, AES.block_size))
    ct = base64.b64encode(iv + ct_bytes)
    msg = s.send(ct)

def wrapper(clf, temp, s, voltage, current, power, energy, send_time, flex, sent):
    if (time.time() - send_time.value >= 4):
        start_time = time.time()
        tempArr = temp
        df = pd.DataFrame(tempArr)
        df.columns = ["acc_x", "acc_y", "acc_z",
                      "gyro_x", "gyro_y", "gyro_z",
                      "flex_index", "flex_pinky"]
        if flex:
            features = calc_features_flex(df)
        else:
            features = calc_features(df)
        norm_features = preprocessing.normalize([features])
        res = classify(clf, norm_features)
        
        res_string = map(int(res))
        print("This is the returned class: {}".format(res_string))
        print("Elapsed time in wrapper: {}".format(time.time() - start_time))
        print("Elapsed time since last send: {}".format(time.time() - send_time.value))
        print("Current time: {}\n".format(time.time()))
        # if sent.value != 1:
        send(res_string, s, voltage, current, power, energy, time.time())
        send_time.value = time.time()
        """    sent.value = 1
        elif res == "neutral" and sent.value == 1:
            sent.value = 0
        """

# takes in single dance dataframe
# returns a list of segments for dataframe passed in
# segments are dataframes
# returns a list of dataframes
def segment(data, size = 100, overlap = 50.0):
    all_segments = []

    start = 0
    # need to ensure that the increment is an integer
    increment = size - math.floor(size*(overlap/100))
    end = start + size

    while (end <= len(data.index)):
        window = data.iloc[start:end]
        all_segments.append(window)
        start += increment
        end = start + size

    return all_segments

def wrapper2(clf, temp, s, voltage, current, power, energy, send_time, flex, sent):
    start_time = time.time()
    tempArr = temp
    df = pd.DataFrame(tempArr)
    df.columns = ["acc_x", "acc_y", "acc_z",
                  "gyro_x", "gyro_y", "gyro_z",
                  "flex_index", "flex_pinky"]
    frames = segment(df)
    print("Frames size: {}".format(len(frames)))
    res_buffer = []
    for frame in frames:
        if flex:
            features = calc_features_flex(frame)
        else:
            features = calc_features(frame)
        norm_features = preprocessing.normalize([features])
        res = classify(clf, norm_features)
        print("This is the class: {}".format(map(int(res))))
        res_buffer.append(res)
    
    voted = np.bincount(res_buffer).argmax()
    
    res_string = map(int(voted))
    if sent.value != 1 and res_string != "neutral":
        print("This is the voted class: {}".format(res_string))
        print("Elapsed time in wrapper: {}".format(time.time() - start_time))
        print("Elapsed time since last send: {}".format(time.time() - send_time.value))
        print("Current time: {}".format(time.time()))
        print()
        send(res_string, s, voltage, current, power, energy, time.time())
        send_time.value = time.time()
        sent.value = 1
    elif res_string == "neutral" and sent.value == 1:
        sent.value = 0


frame_size = window_length(size, sampling_period)
increment = int(frame_size - math.floor(frame_size * (overlap / 100.0)))
start = 0
end = int(start + frame_size)

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    s.connect((host,port))
except Exception as e:
    print("Did you forget to include the host and port number? If not maybe the destination server has not been started.")
    print(e)
    exit(1)

print("Please plug in the Arduino power cable.")

received_str = ""
while "Done" not in received_str:
	received_data = ser.readline()
	print(received_data)
	received_str = received_data.decode("utf-8")

#######################################################################################

while True:
    # ============ Connection HandShake ======================
    data = input("Enter a request ID: ")
    ser.reset_input_buffer()
    dataToSend = int(data).to_bytes(1,byteorder='big')
    ser.write(dataToSend)
    ser.flush()
  
    received_data = ser.read()
    received_data = int.from_bytes(received_data,byteorder='big')

    if (received_data == NAK):
        print("<Invalid request ID> Re-enter request ID")
    elif (received_data == ACK):    # if the data i received is not empty
        ackToArduino = ACK.to_bytes(1,byteorder='big')
        ser.write(ackToArduino)
        print("Sent ACK for conn request ACK")

        # =================== Getting Data =======================

        i = 0
        voltage = 0
        current = 0
        power = 0
        energy = 0
        prevTime = time.time()
        send_time = multiprocessing.Value("d", time.time())
        sent = multiprocessing.Value("i", 0)
        while True:
            try:
                received_data = ser.read()	# Expects 1 byte packet containing buffer length to expect
                buffLen = int.from_bytes(received_data,byteorder='big')	#Convert byte to int
                ser.write(ACK.to_bytes(1,byteorder='big'))	# ACK for receiving the buffer length
                received_data = ser.read()	# Read in parity bit
                evenParityBit =  int.from_bytes(received_data, byteorder='big')
                received_data = ser.read(buffLen)

                xorBit = 0
                for b in received_data:
                    for k in range(8):
                        xorBit ^= ((b >> k) & 1)

                if(xorBit == evenParityBit):
                    numReading = int(buffLen/4)		# One reading occupies 4 bytes
                    tmpArr = []
                    for j in range(numReading-2):
                        tmp = int.from_bytes(received_data[:4],byteorder='little', signed=True)	#Convert byte to int
                        tmpArr.append(tmp/1000000)
                        received_data = received_data[4:]

                    voltage = int.from_bytes(received_data[:4],byteorder='little', signed=True)	#Convert byte to int
                    voltage = voltage / 1000000
                    received_data = received_data[4:]
                    current = int.from_bytes(received_data[:4],byteorder='little', signed=True)	#Convert byte to int
                    current = current / 1000000
                    power = voltage * current

                    energy += (power * (time.time() - prevTime) / 3600)

                    prevTime = time.time()

                    datasets.append(tmpArr)
                    
                    
                    if (len(datasets) == (frame_size)):
                        temp = datasets[start:end]
                        datasets = datasets[increment:]
                        
                        p = multiprocessing.Process(target=wrapper, args=(clf, temp, s, voltage, current, power, energy, send_time, flex, sent))
                        p.start()
                    
                    """
                    if (len(datasets) == (frame_size + 2*increment)):
                        temp = datasets
                        slice_index = frame_size + increment 
                        datasets = datasets[slice_index: ]
                        p = multiprocessing.Process(target=wrapper2, args=(clf, temp, s, voltage, current, power, energy, send_time, flex, sent))
                        p.start()
                        """
                    
                    
                    ser.write(ACK.to_bytes(1,byteorder='big')) # transmit acknowledge
                else:
                    i -= 1
                    ser.write(NAK.to_bytes(1,byteorder='big'))
                i += 1
            except KeyboardInterrupt:
                # ================= Disconnection handshake =================
                ser.read()					# Wait for Arduino to send data, indicating its waiting for a byte
                ser.write(DISCONN_REQ.to_bytes(1,byteorder='big'))
                received_data = ser.read()
                received_data = int.from_bytes(received_data,byteorder='big')	# Convert byte to int
                if(received_data == ACK):
                    print("ACK received for disconnection request")
                    ser.write(ACK.to_bytes(1,byteorder='big'))
                    print("Sent ACK for disconn requst ACK")
                else:
                    print("No ACK received for disconnection request")

    else:
        print("Received neither ACK nor NAK from Arduino");