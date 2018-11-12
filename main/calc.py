# script for calculating features from raw data
import numpy as np
from scipy.fftpack import fft, ifft
from scipy.stats import iqr, pearsonr
from scipy import stats
from pandas import Series


# Mathematical functions

# returns type numpy.float64
def mean(values):
    return np.mean(values)

def std(values):
    return np.sqrt(np.var(values))

# median absolute deviation
# not sure if i need to normalize
# normalised version found here at https://gist.github.com/raphaelvallat/d535bf4e93e6ba88c3e6a77b90180251
def mad(values):
    med = np.median(values)
    return np.median(np.abs(values-med))

def max(values):
    return np.amax(values)
    
def min(values):
    # print(values)
    return np.amin(values)

"""
rfft avoid returning the upper half of the spectrum which happens to be symmetric 
when computing the FFT of a real-valued input. It also avoids returning the 
imaginary part of the DC (0Hz) bin and of the Nyquist frequency (half the sampling 
rate) bin since those are always zero when dealing with real-valued inputs.

Thus some duplicate inputs of the upper half is left out when comparing fft and 
rfft. Is it necessary to consider these duplicate inputs?

I saw need to take conjugate and what not: FYI and TBC
"""
"""
current formula taken from https://gist.github.com/endolith/1257010#file-parseval-py
"""

def iqr(values, series=True):
    if (series):
        return stats.iqr(values.tolist())
    return stats.iqr(values)

def correlation(first_axis, second_axis):
    return pearsonr(first_axis, second_axis)[0]

# Variable Calculation functions

# assuming acceleration or any other is sampled at 50 hz
# time between each sample is 0.02s
# https://github.com/danielmurray/adaptiv
# jerk formula found here
# i am also assuming gyrojerk is calculated this way
def jerk(values, freq=50):
    # rate of change of acceleration
    time = 1.0/freq
    jerk_list = np.array()
    for curr, follow in zip(values, values[1:]):
        jerk_list.append((curr-follow) / time)  

    return np.array(jerk_list)

# Also the magnitude of these three-dimensional signals were calculated using the Euclidean norm 
# (tBodyAccMag, tGravityAccMag, tBodyAccJerkMag, tBodyGyroMag, tBodyGyroJerkMag).
# Euclidean norm = square root of the sum of squares
# square and sum each x,y,z then square root
# Aassumes that the data comes in 3 lists
def euclidean_norm(x_list, y_list, z_list):
    x = np.append([x_list], [y_list], [z_list], axis=0) # builds 2d array with x,y,z
    return np.sqrt(np.sum(np.square(x), axis=0)) # returns the euclidean_norm
