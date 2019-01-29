from flask import Flask, url_for, request, redirect, render_template, jsonify, send_file
from werkzeug.exceptions import BadRequest, InternalServerError, HTTPException
from xlrd import open_workbook
import numpy as np
from fastnumbers import fast_real
import ski_slope_least_squares_3_oct as lsq
import z_dist_fit_10_nov as zdist
import ski_stats

EXCEL_EXTENSIONS = {'xlsx', 'xls'}

app = Flask(__name__)


def is_spreadsheet(filename):
    """Spreadsheet filename validator."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in EXCEL_EXTENSIONS


def get_uploaded_spreadsheet():
    """Get a stream for the uploaded spreadsheet file."""
    if "spreadsheet" not in request.files:
        raise BadRequest("Must select a spreadsheet containing time and data measurements.")

    file_stream = request.files["spreadsheet"]
    if file_stream is None or file_stream.filename == "":
        raise BadRequest("Spreadsheet file not found.")

    if not is_spreadsheet(file_stream.filename):
        raise BadRequest("File must be a spreadsheet with one of the following extensions: " +
                         ", ".join(EXCEL_EXTENSIONS))
    return file_stream


def get_numpy_val_from_form_input(input_name):
    """Get a NumPy-compatible numerical value from the request object"""
    return get_numpy_val(input_name, request.form[input_name])


def get_numpy_val(input_name, input_val):
    """Convert input values to NumPy-compatible numerical values"""
    if input_val == "inf" or input_val == "+inf":
        return np.inf
    elif input_val == "-inf":
        return -np.inf
    else:
        num = fast_real(input_val)
        if isinstance(num, (int, long, float)):
            return num
        else:
            raise BadRequest(
                "Invalid value for \"{0}\" ({1}).  Expected: -inf, inf, or a numerical value.".format(input_name, input_val))


@app.errorhandler(HTTPException)
def handle_httpexception(error):
    print str(error)
    return jsonify(code=error.code, name=error.name, description=error.description), error.code


@app.errorhandler(Exception)
def handle_exception(error):
    print str(error)
    return jsonify(code=500, description=error.message), 500


@app.route("/desmos")
def desmos_graph():
    return render_template("desmos-graph.html")


@app.route("/parseSpreadsheet", methods=["POST"])
def parse_uploaded_spreadsheet():
    # spreadsheet submitted for parsing only
    file_stream = get_uploaded_spreadsheet()
    time, data = ski_stats.parse_workbook(open_workbook(file_contents=file_stream.read()), use_arrays=False)
    return jsonify(x=time, y=data)


@app.route("/desmosCalculateRegression", methods=["POST"])
def desmos_calculate_regression():
    try:
        # parse the form inputs
        time = [get_numpy_val("x["+str(i)+"]", listVal) for i, listVal in enumerate(request.form.getlist("x[]"))]
        data = [get_numpy_val("y["+str(i)+"]", listVal) for i, listVal in enumerate(request.form.getlist("y[]"))]
        time = np.array(time)
        data = np.array(data)

        h = get_numpy_val_from_form_input("h")
        b = get_numpy_val_from_form_input("b")
        v = get_numpy_val_from_form_input("v")
        p = get_numpy_val_from_form_input("p")
        max_nfev = get_numpy_val_from_form_input("max_nfev")

        if request.form.get("specify_bounds"):
            # bounds were specified
            h_upper = get_numpy_val_from_form_input("h_upper")
            b_upper = get_numpy_val_from_form_input("b_upper")
            v_upper = get_numpy_val_from_form_input("v_upper")
            p_upper = get_numpy_val_from_form_input("p_upper")

            h_lower = get_numpy_val_from_form_input("h_lower")
            b_lower = get_numpy_val_from_form_input("b_lower")
            v_lower = get_numpy_val_from_form_input("v_lower")
            p_lower = get_numpy_val_from_form_input("p_lower")
            bounds = ([h_lower, b_lower, v_lower, p_lower], [h_upper, b_upper, v_upper, p_upper])

            # run calculation with bounds
            results = lsq.do_calculations(time=time, data=data, params_guess=(h, b, v, p), bounds=bounds, max_nfev=max_nfev)
        else:
            # run calculation without bounds
            results = lsq.do_calculations(time=time, data=data, params_guess=(h, b, v, p), max_nfev=max_nfev)

        # for now, the Desmos-style page expects just the param solutions
        h, b, v, p = results.lsq_params
        return jsonify(h=h, b=b, v=v, p=p)

    except KeyError as err:
        raise BadRequest("[KeyError] {0}".format("Request was missing param \"{0}\"".format(err.args[0])))

    except Exception as err:
        raise InternalServerError("[{0}] {1}".format(type(err).__name__, str(err)))


@app.route("/", methods=["GET"])
def start_page():
    return render_template("ski-slope.html")


@app.route("/zdistAnalysis", methods=["POST"])
def submit_zdist_analysis():
    file_stream = get_uploaded_spreadsheet()
    try:
        # parse the uploaded spreadsheet
        time, data = ski_stats.parse_workbook(open_workbook(file_contents=file_stream.read()))
        user_threshold_raw = request.form["user_threshold"]
        user_threshold = fast_real(user_threshold_raw)
        if not isinstance(user_threshold, (int, long, float)) or not (1 <= user_threshold <= 100):
            raise BadRequest("Invalid value for \"user_threshold\" ({1}).  Expected value between 1 and 100."
                             .format(user_threshold_raw))

        # run the zdist calculation
        user_threshold = float(user_threshold)
        results = zdist.do_calculations(time, data, user_threshold)
        buf = zdist.generate_plot_image(time, data, user_threshold, results)
        return send_file(buf, mimetype="image/png")

    except KeyError as err:
        raise BadRequest("[KeyError] {0}".format("Request was missing param \"{0}\"".format(err.args[0])))

    except Exception as err:
        raise InternalServerError("[{0}] {1}".format(type(err).__name__, str(err)))


@app.route("/lsqAnalysis", methods=["POST"])
def submit_lsq_analysis():
    file_stream = get_uploaded_spreadsheet()
    try:
        # parse the uploaded spreadsheet
        time, data = ski_stats.parse_workbook(open_workbook(file_contents=file_stream.read()))

        # parse the form inputs
        h = get_numpy_val_from_form_input("h")
        b = get_numpy_val_from_form_input("b")
        v = get_numpy_val_from_form_input("v")
        p = get_numpy_val_from_form_input("p")
        max_nfev = get_numpy_val_from_form_input("max_nfev")
        include_text = request.form.get("include_text") is not None

        if request.form.get("specify_bounds"):
            # bounds were specified
            h_upper = get_numpy_val_from_form_input("h_upper")
            b_upper = get_numpy_val_from_form_input("b_upper")
            v_upper = get_numpy_val_from_form_input("v_upper")
            p_upper = get_numpy_val_from_form_input("p_upper")

            h_lower = get_numpy_val_from_form_input("h_lower")
            b_lower = get_numpy_val_from_form_input("b_lower")
            v_lower = get_numpy_val_from_form_input("v_lower")
            p_lower = get_numpy_val_from_form_input("p_lower")
            bounds = ([h_lower, b_lower, v_lower, p_lower], [h_upper, b_upper, v_upper, p_upper])

            # run calculation with bounds
            results = lsq.do_calculations(time=time, data=data, params_guess=(h, b, v, p), bounds=bounds, max_nfev=max_nfev)
        else:
            # run calculation without bounds
            results = lsq.do_calculations(time=time, data=data, params_guess=(h, b, v, p), max_nfev=max_nfev)

        # generate image and send as response
        buf = lsq.generate_plot_image(time, data, results, include_text)
        return send_file(buf, mimetype="image/png")

    except KeyError as err:
        raise BadRequest("[KeyError] {0}".format("Request was missing param \"{0}\"".format(err.args[0])))

    except Exception as err:
        raise InternalServerError("[{0}] {1}".format(type(err).__name__, str(err)))
