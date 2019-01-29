import numpy as np
import matplotlib as mpl
mpl.use('Agg')  # standard rendering tool for matplotlib above
import matplotlib.pyplot as plt
from scipy import optimize
from matplotlib import rcParams
from io import BytesIO
from PIL import Image
from xlrd import open_workbook
import ski_stats

DEFAULT_INITIAL_PARAMS_GUESS = (700, 200, 0, 24)
DEFAULT_BOUNDS = ([-np.inf, -np.inf, -np.inf, -np.inf], [np.inf, np.inf, np.inf, np.inf])
DEFAULT_MAX_NFEV = 1000000000


def cos_fit(params, x):
    """Fit function.  The parameters are arranged in the way required by SciPy.
    params -- [h, b, v, p]
    x      -- time array
    """
    h, b, v, p = params
    # NumPy's cosine function can accept an array of `x` values and return
    # an array of data instead of a scalar; no looping required.
    return h * (np.cos((2 * np.pi * (x + v)) / p)) + b


def residuals(params, x, y):
    """Residuals computation.  The parameters are arranged in the way required by SciPy.
    params -- [h, b, v, p]
    x      -- time array
    y      -- data array
    """
    return cos_fit(params, x) - y


def least_squares(time, data, params_guess, loss, bounds, max_nfev):
    """Get the solved params and residuals.
    time -- the time array
    data -- the data array
    params_guess -- the initial guess for the fit function params
    loss -- determines the loss function: "linear", "soft_l1", "huber", "cauchy", or "arctan"
            (see: https://scipy-cookbook.readthedocs.io/items/robust_regression.html)
    bounds -- a pair of lists specifying the upper and lower parameter bounds
    max_nfev -- max number of function evaluations
    """
    # fit the data using a least squares calculation
    # (see: https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.least_squares.html)
    result = optimize.least_squares(residuals, params_guess, loss=loss, bounds=bounds, max_nfev=max_nfev,
                                    args=(time, data))
    if not result.success:
        raise ski_stats.CurveFitException("Failed to fit the function: " + result.message)
    # solved params are stored in `x`, residuals are stored in `fun`
    return result.x, result.fun


def do_calculations(time, data, params_guess=DEFAULT_INITIAL_PARAMS_GUESS, bounds=DEFAULT_BOUNDS, max_nfev=DEFAULT_MAX_NFEV):
    """Fit the curve and perform additional calculations."""

    lsq_params, lsq_residuals = least_squares(time, data, params_guess, "linear", bounds, max_nfev)
    lsq_r = ski_stats.pearson(cos_fit(lsq_params, time), data)
    lsq_r2 = lsq_r ** 2

    # find SS (Sum of squared residuals. The defining value of the "fitted" function is to return the smallest possible SS
    ss_lsq = sum((cos_fit(lsq_params, time) - data) ** 2)

    # find acrophase (x, y coordinates of highest point of cosine function: lsq_peak value is y value, acro(x) finds x
    lsq_peak_value = lsq_params[1] + lsq_params[0]

    # acrophase time directly related to lsq_params[3], "v" which is x offset for fit. \
    # for example if v = 0, peak timing would occur at x = 0
    def acro(x):
        if x < 0:
            return abs(x) + lsq_params[3]
        else:
            return lsq_params[3] - x

    # find mesor (midpoint between peak and trough, also when standard cosine function cos(x) for x = -pi/2 and x = pi/2
    # but most easily is found from lsq_params[1], "b" as the vertical offset raising or lowering ht of function

    # create list populated from mesor value equal in length to time (and thus data) list in order to compare values later
    lsq_mesor = lsq_params[1]
    lsq_mesor_list = []
    for items in time:
        lsq_mesor_list.append(lsq_mesor)

    # lsq_acro plugs in v, returns x value
    lsq_acro = acro(lsq_params[2])

    # lsq_std_cos removes lsq_params[1] "b" and lsq_params[0] "h" to return y values back to -1<=y<=1
    lsq_std_cos = (cos_fit(lsq_params, time) - lsq_params[1]) / lsq_params[0]

    # lsq_cos_prime returns the first order derivates to lsq_std_cos function
    lsq_cos_prime = -np.sin(lsq_std_cos)

    # lsq_acos returns the cos integral of lsq_std_cos
    # assumed beneficial for known y values where it is desired to know x (time)
    lsq_acos = np.arccos(lsq_std_cos)

    # lsq_time_up generates timepoints where mesor is crossed by cos_fit going up (onset)
    lsq_time_up = (((2 * np.pi - lsq_acos) * lsq_params[3]) / (2 * np.pi)) - lsq_params[2] + lsq_params[3]

    # lsq_time_down generates timepoints where mesor is crossed by cos_fit going down (offset)
    lsq_time_down = ((lsq_acos * lsq_params[3]) / (2 * np.pi)) - lsq_params[2] + lsq_params[3]

    # tuple pairing time and mesor values
    lsq_mesor_tuple = zip(time, lsq_mesor_list)

    # tuple pairing time and data values
    time_data_tuple = zip(time, data)

    # repeat acro coords across figure rather than displaying 1 point \
    # should plot point for every peak occurring within dataset
    lsq_acro_list_x = []
    lsq_acro_list_y = []

    acro_point_total = lsq_acro

    while acro_point_total <= max(time):
        lsq_acro_list_x.append(acro_point_total)
        lsq_acro_list_y.append(lsq_peak_value)
        acro_point_total += lsq_params[3]

    # mesor-data intersection points

    # below returns data index points prior to mesor crossing, writes these index values to y_int
    idx = np.argwhere(np.diff(np.sign(lsq_mesor_list - data))).flatten()
    x_int = time[idx]
    y_int = []
    for coords in x_int:
        y_int.append(lsq_mesor)

    crossing_points = []

    # finds time values where mesor intersects with data (assuming straight line from point to point) \
    # by generating straight line y = mx+b from two known points at each interval, and inverse to solve for y w/known time
    # writes each of these intersection timepoints to crossing_points list (y value is always mesor, this list is x "time")
    for intersect in idx:
        crossing_points.append(
            (lsq_mesor - ((data[intersect]) - ((data[intersect + 1] - data[intersect]) / (time[intersect + 1] -
                                                                                          time[intersect])) *
                          time[intersect])) / ((data[intersect + 1] - data[intersect]) / (time[intersect + 1] -
                                                                                          time[intersect])))
    crossing_points = np.array(crossing_points)

    # determine area under curve between onset and offset using trapezoidal rule
    # combine time,data coords with crossing_points, lsq_mesor list, then arrange by time
    crossing_coords = sorted((zip(crossing_points, lsq_mesor_list)) + time_data_tuple)
    sorted_coords = zip(*crossing_coords)
    # all_time is every original timepoint plus mesor intersection timepoints
    all_time = sorted_coords[0]
    # all_data is every original datapoint plus mesor value when mesor intersects data
    all_data = sorted_coords[1]

    # find position in sorted coords where crossing points appear (start and end of each auc computation)

    index_coords = []

    for pts in crossing_points:
        for items in all_time:
            if items == pts:
                index_coords.append(all_time.index(items))

    # introduce lists that will be written as a function of whether curve is going up during mesor crossing (onset) \
    # or down during crossing (offset) These are onset_coords and offset_coords, respectively.
    # onset and offset index_coords display the index number of these locations relative to position in all_time
    onset_coords = []
    onset_index_coords = []
    offset_coords = []
    offset_index_coords = []
    peak_data_list = []
    peak_time_list = []

    for pts in index_coords[0:(len(index_coords) - 1)]:
        if all_data[pts + 1] > all_data[pts]:
            onset_coords.append(pts)
            onset_index_coords.append(index_coords.index(pts))

    for pts in index_coords[1:len(index_coords)]:
        if all_data[pts + 1] < all_data[pts]:
            offset_coords.append(pts)
            offset_index_coords.append(index_coords.index(pts))

    # filters all_time, and all_data arrays into arrays of lists, each sub-list beginning at onset, ending at offset
    # all other coordinates ignored
    # time list written to peak_time_list, data written to peak_data_list

    step = 0
    while step < (len(index_coords)):
        if len(index_coords) <= 1:
            print "only 1 mesor crossing; cannot compute peak duration"
            step = len(index_coords)
        elif index_coords[0] == onset_coords[0] and len(index_coords) % 2 == 0 and len(index_coords) >= 2:
            peak_data_list.append(all_data[index_coords[step]:index_coords[step + 1] + 1])
            peak_time_list.append(all_time[index_coords[step]:index_coords[step + 1] + 1])
            step += 2
        elif index_coords[0] == onset_coords[0] and len(index_coords) % 2 != 0 and len(index_coords) >= 3:
            index_coords.pop()
            peak_data_list.append(all_data[index_coords[step]:index_coords[step + 1] + 1])
            peak_time_list.append(all_time[index_coords[step]:index_coords[step + 1] + 1])
            step += 2
        elif index_coords[0] != onset_coords[0] and len(index_coords) % 2 == 0 and len(index_coords) >= 3:
            index_coords = index_coords[1:-1]
        elif index_coords[0] != onset_coords[0] and len(index_coords) % 2 != 0 and len(index_coords) >= 3:
            index_coords = index_coords[1:]
        elif index_coords[0] != onset_coords[0] and len(index_coords) % 2 == 0 and len(index_coords) <= 2:
            print "not enough coordinates to determine"
        else:
            print "on-off coordinates not found"
            step = len(index_coords)

    # write all trapezoidal auc computations to list called peak_auc_list
    peak_cycle = 0
    peak_auc_list = []

    while peak_cycle < len(peak_time_list):
        peak_auc_list.append(ski_stats.peak_auc(peak_time_list[peak_cycle], peak_data_list[peak_cycle]))
        peak_cycle += 1

    # write all peak_mp_auc calculations to a list
    mp_cycle = 0
    peak_mp_auc_list = []

    while mp_cycle < len(peak_time_list):
        peak_mp_auc_list.append(ski_stats.midpoint_peak_auc(peak_time_list[mp_cycle], peak_data_list[mp_cycle]))
        mp_cycle += 1

    # box-up and return the results
    return ski_stats.CalcResults({
        "ss_lsq": ss_lsq, "lsq_residuals": lsq_residuals, "lsq_r": lsq_r, "lsq_r2": lsq_r2, "lsq_acro": lsq_acro,
        "lsq_peak_value": lsq_peak_value, "lsq_mesor": lsq_mesor, "y_int": y_int, "lsq_acro_list_x": lsq_acro_list_x,
        "lsq_acro_list_y": lsq_acro_list_y, "lsq_params": lsq_params, "idx": idx, "x_int": x_int,
        "crossing_points": crossing_points, "all_time": all_time, "all_data": all_data, "index_coords": index_coords,
        "onset_coords": onset_coords, "onset_index_coords": onset_index_coords, "offset_coords": offset_coords,
        "offset_index_coords": offset_index_coords, "peak_time_list": peak_time_list, "peak_data_list": peak_data_list,
        "peak_auc_list": peak_auc_list, "peak_mp_auc_list": peak_mp_auc_list
    })


def generate_plot_image(time, data, results, include_text=True):
    # setup the figure plot params
    rcParams["figure.figsize"] = (10, 14 if include_text else 7)
    rcParams["legend.fontsize"] = 16
    rcParams["axes.labelsize"] = 16

    # create a blank figure
    fig = plt.figure()

    # add a plot (2x1 grid in the 1st position)
    axes = fig.add_subplot(211 if include_text else 111)

    # generate smooth fitted curves by upping the resolution to 100
    time_fit = np.linspace(time.min(), time.max(), 500)
    lsq_data_fit = cos_fit(results.lsq_params, time_fit)
    acro_x_y = (results.lsq_acro, results.lsq_peak_value)
    # plot the data ("ro" = red circles) and the fit ("r-" = red line)
    axes.plot(time, data, "k-", label="Actual Data")
    axes.plot(time, data, "ko")
    axes.plot(time_fit, lsq_data_fit, "r-", label="Cosine Fit")
    axes.plot(results.lsq_acro_list_x, results.lsq_acro_list_y, "ro")
    plt.hlines(results.lsq_mesor, time[0], time[len(time) - 1], "y", label="Mesor")
    axes.plot(results.crossing_points, results.y_int, "yo")

    # add a legend
    axes.set_title("Ski Slope Cosine Fit")
    axes.set_xlabel("Hour")
    axes.set_ylabel("Measurement")
    axes.legend()

    if include_text:
        # string containing all calculated data to be appended to plot image
        all_text = (
            "SS = {0:,.2f}\n\n"
            "$r({1:d}) = {2:,.3f}$,  $r^2({1:d}) = {3:,.3f}$\n\n"
            "Peak Coordinates = ({4:,.4f}, {5:,.4f})\n\n"
            "Mesor = {6:,.3f}  Number of Mesor Crossings = {7:d}\n\n"
            "Times of Mesor Crossings:\n"
            "{8:s}\n\n"
            "On-Off AUC:\n"
            "{9:s}\n\n"
            "h = {10:.4f}, b = {11:.4f}, v = {12:.4f}, p = {13:.4f}").format(
            results.ss_lsq, results.lsq_residuals.size - 2, results.lsq_r, results.lsq_r2, results.lsq_acro,
            results.lsq_peak_value, results.lsq_mesor, len(results.crossing_points), results.crossing_points,
            results.peak_mp_auc_list, *results.lsq_params)

        # insert string below the plot, left-aligned
        axes2 = fig.add_subplot(212)
        axes2.axis("off")
        axes2.text(
            .02, .96,
            all_text,
            color="k",
            fontsize=16,
            horizontalalignment="left",
            verticalalignment="top",
            wrap=True,
            transform=axes2.transAxes)

    # save the image to an in-memory buffer (must be closed when done)
    fig.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format="png")
    buf.seek(0)
    return buf


def main():
    """The main runner for interactive commandline invocation.  Performs calc, generates image, prints results."""
    import os
    import sys

    # retrieve xlsx file, user inputs name of file
    file_name = raw_input("What is the name of your excel file?")
    file_path = os.path.join(os.getcwd(), str(file_name) + ".xlsx")
    script_name_no_ext = os.path.splitext(os.path.basename(sys.argv[0]))[0]
    image_output_path = os.path.join(os.getcwd(), str(file_name) + "_" + script_name_no_ext + ".png")

    # parse spreadsheet, do calculations, generate image
    time, data = ski_stats.parse_workbook(open_workbook(file_path))
    try:
        results = do_calculations(time, data)
    except ski_stats.CurveFitException as err:
        print err.message
        sys.exit(-1)

    # read image from the buffer and save it as a file
    buf = generate_plot_image(time, data, results)
    try:
        img = Image.open(buf)
        img.save(image_output_path)
    finally:
        buf.close()

    # print results to standard-out
    print("{0}\nr = {1:.4f}\nr^2 = {2:.4f}\nSS = {3:.4f}\nh = {4:.4f}\nb = {5:.4f}\nv = {6:.4f}\np = {7:.4f}\n".format(
        "linear", results.lsq_r, results.lsq_r2, results.ss_lsq, *results.lsq_params))
    print (time[results.idx])
    print results.x_int
    print results.idx
    print results.crossing_points
    print results.all_time
    print results.all_data
    print results.index_coords
    print results.onset_coords
    print results.onset_index_coords
    for on in results.onset_coords:
        print results.all_time[on]
    print results.offset_coords
    print results.offset_index_coords
    for off in results.offset_coords:
        print results.all_time[off]

    print results.peak_time_list
    print results.peak_data_list
    print results.peak_auc_list
    print results.peak_mp_auc_list
    # to do restrict p range 0:48
    # to do restrict h to 5x max data value
    # to do restrict b to max data value
    # change auc to midpoint formula
    # export to excel file
    # triple check all crossing point possibilities:
    # on: test8- check
    # off: test1- check
    # on-off: test- check, test214- check test212(on-off on off)- check
    # off-on: test5fail(modified)- check
    # on-off-on: test234(on-off on-off on)- check
    # off-on-off: test6- check
    # off-on-off-on: test7- check


# if script is being run directly from commandline
if __name__ == "__main__":
    main()
