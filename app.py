from flask import Flask, url_for, request, redirect, render_template, jsonify, send_file
from werkzeug.exceptions import BadRequest, InternalServerError, HTTPException
from xlrd import open_workbook
import numpy as np
from fastnumbers import fast_real
from ski_slope_least_squares_3_oct import parse_workbook, do_calculations, generate_plot_image, LeastSquaresException

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
    """Convert form inputs to NumPy-compatible numerical values"""
    val = request.form[input_name]
    if val == "inf" or val == "+inf":
        return np.inf
    elif val == "-inf":
        return -np.inf
    else:
        num = fast_real(val)
        if isinstance(num, (int, long, float)):
            return num
        else:
            raise BadRequest(
                "Invalid value for \"{0}\".  Expected: -inf, inf, or a numerical value.".format(input_name))


@app.errorhandler(BadRequest)
@app.errorhandler(InternalServerError)
def handle_invalid_usage(error):
    return error.description, error.code


@app.route("/")
def root():
    return redirect(url_for("ski_slope"))


@app.route("/ski-slope", methods=["GET", "POST"])
def ski_slope():
    if request.method == "GET":
        # serve HTML form
        return render_template("ski-slope.html")
    else:
        # form was submitted
        file_stream = get_uploaded_spreadsheet()
        try:
            # parse the uploaded spreadsheet
            time, data = parse_workbook(open_workbook(file_contents=file_stream.read()))

            # parse the form inputs
            h = get_numpy_val_from_form_input("h")
            b = get_numpy_val_from_form_input("b")
            v = get_numpy_val_from_form_input("v")
            p = get_numpy_val_from_form_input("p")
            max_nfev = get_numpy_val_from_form_input("max_nfev")
            include_text = request.form.get("include_text") is not None

            if request.form.get("specify_bounds"):
                # bounds were specified
                h_upper = request.form["h_upper"]
                b_upper = request.form["b_upper"]
                v_upper = request.form["v_upper"]
                p_upper = request.form["p_upper"]
                h_lower = request.form["h_lower"]
                b_lower = request.form["b_lower"]
                v_lower = request.form["v_lower"]
                p_lower = request.form["p_lower"]
                bounds = ([h_lower, b_lower, v_lower, p_lower], [h_upper, b_upper, v_upper, p_upper])

                # run calculation with bounds
                results = do_calculations(time=time, data=data, params_guess=(h, b, v, p), bounds=bounds, max_nfev=max_nfev)
            else:
                # run calculation without bounds
                results = do_calculations(time=time, data=data, params_guess=(h, b, v, p), max_nfev=max_nfev)

            # generate image and send as response
            buf = generate_plot_image(time, data, results, include_text)
            return send_file(buf, mimetype="image/png")

        except KeyError as err:
            err_msg = "Request was missing param \"{0}\"".format(err.args[0])
            print "[KeyError] {0}".format(err_msg)
            raise BadRequest(err_msg)

        except LeastSquaresException as err:
            print "[LeastSquaresException] {0}".format(str(err))
            raise InternalServerError(str(err))

        except HTTPException as err:
            print "[{0}] {1}".format(type(err).__name__, str(err))
            raise err

        except Exception as err:
            print "[{0}] {1}".format(type(err).__name__, str(err))
            raise InternalServerError(str(err))

