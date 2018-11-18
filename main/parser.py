import pandas as pd
import os
import math
from sklearn import preprocessing
import numpy as np
import matplotlib.pyplot as plt
import sys
import calc

import numpy as np
from sklearn.neighbors import KNeighborsClassifier
from sklearn.externals import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC, LinearSVC
from sklearn import metrics
from sklearn.feature_selection import RFECV, RFE
from sklearn import preprocessing
from sklearn.model_selection import cross_val_score, train_test_split
import timeit
import multiprocessing
from sklearn.metrics import confusion_matrix

# parse using pandas seems to be faster
def parse(dance):
    print("Reaading from {} file".format(dance))
    data = pd.read_csv(dance, header=None, skiprows=1, skipfooter=1) #skiprows=1 because first line always error
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
            data = parse(line.strip())
            print(data.isnull().values.any())
            dances.append(data)

    return dances

def obtain_data_map(dance_files):
    dances = []
    with open(dance_files, "r") as f:
        for line in f:
            dance, label = line.strip().split("#")
            dance = dance.strip()
            label = label.strip()
            data = parse(dance)
            # print(data.isnull().values.any())
            dances.append((data, label))

    return dances

# takes in single dance dataframe
# returns a list of segments for dataframe passed in
# segments are dataframes
# returns a list of dataframes
def segment(data, size, overlap):
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

# method might be optional, as in its not critical to run this if we guarantee in external logic
# that all dance dataframes will be of sufficient size to generate windows from them
def min_length(dances):
    min = sys.maxsize
    for dance in dances:
        if (len(dance[0].index) < min):
            min = len(dance[0].index)

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

# input: dataframe
# return: int list
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

def plot(dataframe, column):
    # get number of entries in dataframe row
    step = 0.02
    size = len(dataframe.index)
    t = np.arange(size*step, step=step)
    fig, ax = plt.subplots()
    y = dataframe[column]
    ax.plot(y)
    plt.show()


def gen_xy(dances, X_file, y_file):
    X_file = open(X_file, "w")
    y_file = open(y_file, "w")
    all_dance_frames = []

    # for each dance dataframe
    for dance in dances:

        # generate data segments
        segments_dance = segment(dance[0], length, overlap)

        # list of feature_frames
        feature_frames = []

        for item in segments_dance:
            # Calculate features for each data segment
            feature_frame = calc_features_flex(item)
            temp_test = pd.DataFrame(feature_frame)

            # Conditional breakpoint was set here because under certain window sizes, the duplicate values in
            # sensor readings cause pearsonr to divide by 0 becuase stddev = 0
            # therefore do not use 0.3s window
            temp_test.isnull().values.any()
            feature_frames.append(feature_frame)

        # Normalize
        norm_frames = preprocessing.normalize(feature_frames)

        # so one frame corresponds to one entry in X_train/test and a corresponding y_train/test label
        # list of frames for one dance
        all_dance_frames.append(norm_frames)

        # Need to map the frames to their class
        temp = []
        label = dance[1]
        for frame in norm_frames:
            temp.append((frame, label))

        for item in temp:
            check = np.array_str(item[0]).lstrip('[').rstrip(']').replace("\n", "")
            X_file.write(check + "\n")
            y_file.write(str(item[1]) + "\n")
    X_file.close()
    y_file.close()

# Weird block of global code set up just for the timeit function
# clf1 = KNeighborsClassifier(n_neighbors=5)
# clf2 = RandomForestClassifier(n_estimators=10, random_state=42, n_jobs=-1)
# clf3 = LogisticRegression()
# clf4 = LinearSVC(multi_class="ovr")
# X_train = np.loadtxt("X_train.txt")
# y_train = np.loadtxt("y_train.txt")
# X_test = np.loadtxt("X_test.txt")
# y_test = np.loadtxt("y_test.txt")

def test1(clf,X_test,y_test,X_train,y_train):
    # clf.fit(X_train,y_train)
    clf.score(X_test, y_test)

def load_classifier(clf_file):
    return joblib.load(clf_file)

def classify(clf, input):
    return clf.predict(input)[0]

def wrapper(clf, temp):
    # for loop to convert required format to build dataframe
    tempArr = []
    for item in temp:
        tempArr.append([float(val) for val in item.strip().split(",")])
    df = pd.DataFrame(tempArr)
    df.columns = ["acc_x", "acc_y", "acc_z",
                  "gyro_x", "gyro_y", "gyro_z",
                  "flex_index", "flex_pinky"]
    features = calc_features_flex(df)
    print(classify(clf, [features]))
    return classify(clf, [features])

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
                # for loop to convert required format to build dataframe
                p = multiprocessing.Process(target=wrapper, args=(clf,temp))
                p.start()
                # wrapper(clf,df)
                start += increment
                end = start + length

    while (end <= len(total)):
        temp = total[int(start):int(end)]
        # print("{} : {}".format(start, end))
        # for loop to convert required format to build dataframe
        p = multiprocessing.Process(target=wrapper, args=(clf, temp))
        p.start()
        # wrapper(clf,df)
        start += increment
        end = start + length

    print("END + {} + {}".format(end, length))

if __name__ == "__main__":
    X_train_file = "X_train_new_fs_45.txt"
    y_train_file = "y_train_new_fs_45.txt"
    
    X_train = np.loadtxt(X_train_file)
    y_train = np.loadtxt(y_train_file)
    
    clf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    
    clf.fit(X_train, y_train)
    
    joblib.dump(clf, "random_sp30_ws1_5_o50_final_new_fs45.pkl")
    
