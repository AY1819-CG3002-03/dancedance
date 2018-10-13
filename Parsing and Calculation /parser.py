import pandas as pd
import os
import math
from sklearn import preprocessing
import numpy as np
import matplotlib.pyplot as plt
import sys
import calc

# parse using pandas seems to be faster
def parse(dance):
    print("Reaading from {} file".format(dance))
    data = pd.read_csv(dance, sep=" ", header=None)
    data.columns = ["acc_x", "acc_y", "acc_z",
                    "gyro_x", "gyro_y", "gyro_z",
                    "flex_index", "flex_pinky"]
    return data

# parse using the zip function
def parse2(dance):
    f = open(dance, "r")
    readings = []

    with open(dance, "r") as f:
        for line in f:
            readings.append([float(val) for val in line.strip().split()])

    data = list(zip(*readings))

    return data


# add file to text file containing name of dance files
def write_to_dances(file_name, dances="all_dances.txt"):
    with open(dances, "a") as f:
        f.write(file_name + "\n")


def gen_output_name(dance, counter):
    return dance.strip(".txt") + "_broken_{}.txt".format(counter)


# Breaks the file
def break_file(dance, seperator="SEPARATOR"):
    counter = 0
    output_name = gen_output_name(dance, counter)
    o = open(output_name, "w")

    new_files = []

    with open(dance, "r") as f:
        for line in f:
            if (seperator in line) or ("SEPERATOR" in line):
                o.close()
                # write_to_dances(os.path.basename(o))
                new_files.append(os.path.basename(o.name))
                counter += 1
                output_name = gen_output_name(dance, counter)
                o = open(output_name, "w")
            else:
                o.write(line)

    o.close()
    # write_to_dances(os.path.basename(o))
    new_files.append(os.path.basename(o.name))

    return new_files


def clear_file(file):
    open(file, "w").close()


def break_all_files(dance_files):
    to_split = []
    not_to_split = []

    with open(dance_files, "r") as f:
        for file in f:
            if ("#seperate" not in file):
                not_to_split.append(file.strip())
            else:
                to_split.append(file.strip().strip("#seperate").strip())

    # break all required files
    if len(to_split):
        new_gen_files = []
        for file in to_split:
            new_files = break_file(file)
            for item in new_files:
                new_gen_files.append(item)

        # rewrite the all_dances_file
        clear_file(dance_files)
        for line in new_gen_files:
            write_to_dances(line, dance_files)
        for line in not_to_split:
            write_to_dances(line, dance_files)

# returns dance dataframes for all the files listed in the all_dances.txt
def obtain_data(dance_files):
    dances = []  # all dance dataframes
    break_all_files(dance_files)
    with open(dance_files, "r") as f:
        for line in f:
            dances.append(parse(line.strip()))

    return dances

# takes in single dance dataframe
# returns a list of segments for dataframe passed in
# segments are dataframes
# returns a list of dataframes
def segment(data, size, overlap):
    all_segments = []

    start = 0
    # need to ensure that the increment is an integer
    increment = math.floor(size*(overlap/100))
    end = start + size

    while (end <= len(data.index)):
        window = data.iloc[start:end]
        all_segments.append(window)
        start += increment
        end = start + size

    return all_segments

# method might be optional, as in its not critical to run this if we guarantee in external logic
# that all dance dataframes will be of sufficient size to generate windows from them
def min_length(dances):
    min = sys.maxsize
    for dance in dances:
        if (len(dance.index) < min):
            min = len(dance.index)

    return min

# checks if the list of dance dataframes is not too small given the required window size
def check_size(min, length):
    return (min > length)

# input: window size: seconds, period = miliseconds
# return window_length
def window_length(size, period):
    milli = 3
    factor = 10 ** milli
    # need to round off the window length to a integer, decided to round down
    return math.floor((size*factor)/period) # number of rows in a dataframe


def calc_features(frame):

    acc_x = frame["acc_x"]
    acc_y = frame["acc_y"]
    acc_z = frame["acc_z"]
    gyro_x = frame["gyro_x"]
    gyro_y = frame["gyro_y"]
    gyro_z = frame["gyro_z"]
    flex_index = frame["flex_index"]
    flex_pinky = frame["flex_pinky"]

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

    gyro_correlation_1 = calc.correlation(gyro_x, gyro_y)
    gyro_correlation_2 = calc.correlation(gyro_x, gyro_z)
    gyro_correlation_3 = calc.correlation(gyro_y, gyro_z)
    
    feature_frame = [
        acc_mean_x, acc_mean_y, acc_mean_z, acc_std_x, acc_std_y, acc_std_z, acc_mad_x, acc_mad_y, acc_mad_z, acc_max_x, acc_max_y, acc_max_z, acc_min_x, acc_min_y, acc_min_z, acc_iqr_x, acc_iqr_y, acc_iqr_z, acc_correlation_1, acc_correlation_2, acc_correlation_3,
        gyro_mean_x, gyro_mean_y, gyro_mean_z,
        gyro_std_x, gyro_std_y, gyro_std_z,
        gyro_mad_x, gyro_mad_y, gyro_mad_z,
        gyro_max_x, gyro_max_y, gyro_max_z,
        gyro_min_x, gyro_min_y, gyro_min_z,
        gyro_iqr_x, gyro_iqr_y, gyro_iqr_z,
        gyro_correlation_1, gyro_correlation_2, gyro_correlation_3
    ]

    return feature_frame

def plot(dataframe, column):
    # get number of entries in dataframe row
    step = 0.02
    size = len(dataframe.index)
    t = np.arange(size*step, step=step)
    fig, ax = plt.subplots()
    y = dataframe[column]
    ax.plot(y)
    plt.show()

if __name__ == "__main__":
    dance_files = "all_dances.txt"
    dances = obtain_data(dance_files)  # all dance dataframes

    # print(dances[0].shape)

    # Dont have to care about flex sensor data for now because we dont have dance moves that use them yet
    # plot(dances[0], "flex_index")

    # in milliseconds
    sampling_period = 30

    # in seconds
    window_size = 3.5

    # in floating point or decimal numbers
    overlap = 50

    # Need to guarantee that the window_size is not larger than smallest dataframe
    min = min_length(dances)

    length = window_length(window_size, sampling_period)

    if (check_size(min, length)):
        # start processing
        all_dance_frames = []

        X_file = open("X.txt", "w")
        y_file = open("y.txt", "w")

        # for each dance dataframe
        for dance in dances:

            # generate data segments
            segments_dance = segment(dance, length, overlap)

            # list of feature_frames
            feature_frames = []

            for item in segments_dance:
                # Calculate features for each data segment
                feature_frame = calc_features(item)
                feature_frames.append(feature_frame)

            # Normalize
            norm_frames = preprocessing.normalize(feature_frames)

            print(norm_frames)
            # so one frame corresponds to one entry in X_train/test and a corresponding y_train/test label
            # list of frames for one dance
            all_dance_frames.append(norm_frames)

            # Need to map the frames to their class
            temp = []
            label = 1
            for frame in norm_frames:
                temp.append((frame, label))

            for item in temp:
                check = np.array_str(item[0]).lstrip('[').rstrip(']').replace("\n", "")
                X_file.write(check+"\n")
                y_file.write(str(item[1])+"\n")
        X_file.close()
        y_file.close()

    else:
        print("Check size failed\nSpecified window length is larger than smallest dance dataframe size")














