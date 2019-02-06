"""
Common functions used in stats analysis.

Author: Evan Raiewski
"""

import numpy as np


class CalcResults:
    # simple container for holding calc results
    def __init__(self, results=None):
        for key in results:
            self.__dict__[key] = results[key]


class CurveFitException(Exception):
    # raised if error during curve fitting
    pass


def parse_workbook(workbook, use_arrays=True):
    # parse spreadsheet with time (Column A) and data (Column B)
    sheet = workbook.sheet_by_index(0)

    # create blank lists to store excel columns
    time = []
    data = []

    # retrieve time (col A) and data (col B)
    for row in range(sheet.nrows):
        time.append(sheet.cell_value(row, 0))
        data.append(sheet.cell_value(row, 1))

    # caller may need regular list, as NumPy arrays are not JSON serializable
    if not use_arrays:
        return time, data

    # convert the lists to NumPy arrays, which are much faster, and can be
    # passed as parameters to NumPy/SciPy matrix functions
    return np.array(time), np.array(data)


def midpoint_peak_auc(time, data):
    # midpoint auc calculation
    total_sum = 0
    for i in range(len(time)-1):
        mp_sum = (time[i+1] - time[i])*((data[i] + data[i + 1])/2)
        total_sum += mp_sum
    return total_sum


def peak_auc(time, data):
    # trapezoidal area under curve function to find auc between all qualifying onset and offset times
    # uses peak_time_list, and peak_data_list
    if len(time) < 1:
        first_last_duration_amount = 0
        print "peak not found"
    elif (2*len(time))*(data[0]+data[len(data)-1]) != 0:
        first_last_duration_amount = ((time[len(time)-1] - time[0])/((2*(len(time)-1))*(data[0]+data[len(data)-1])))
    else:
        first_last_duration_amount = 0

    # all other indices
    tote = 0
    for pts in data:
        if pts != data[0] or pts != data[len(data)-1]:
            mid_duration_amount = ((time[len(time)-1]) - time[0])/(2*(len(time)-1))*2*pts
            tote += mid_duration_amount
    night_total = tote + first_last_duration_amount
    return night_total


def pearson(x, y):
    # computes pearson correlation coefficient (r) and coefficient of determination (r^2) between arrays x and y.
    # also computes means (xmean, ymean), sums of squares (SSx, SSy) standard deviations (SDy, SDy), /
    # covariance (COVxy) and degrees of freedom (rdf).

    xlen = len(x)
    ylen = len(y)

    xsum = float(0)
    ysum = float(0)

    for values in x:
        xsum += float(values)
    for values in y:
        ysum += float(values)

    xmean = float(xsum/xlen)
    ymean = float(ysum/ylen)
    ss_x = float(0)
    ss_y = float(0)

    for values in x:
        ss_x += float((values-xmean)**2)
    for values in y:
        ss_y += float((values-ymean)**2)

    sd_x = float(ss_x/xlen)**.5
    sd_y = float(ss_y/ylen)**.5

    cov_xy = 0
    rdf = len(x) - 2

    for a, b in zip(x, y):
        cov_xy += float((a-xmean)*(b-ymean))
    # convert this to str containing dfs?
    return float((cov_xy/xlen)/(sd_x*sd_y))

