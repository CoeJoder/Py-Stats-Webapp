
/////////////TODO
/////////////-move import button into the regression panel
/////////////-add mesor and other curves to the Desmos graph
/////////////-add a legend
(function($) {

    var X_AXIS_LEFT = -10;
    var MIN_X_AXIS_RIGHT = 85;
    var DEFAULT_LOWER_BOUND = -10;
    var RUN_BUTTON_URL = "/desmosCalculateRegression";
    var IMPORT_BUTTON_URL = "/parseSpreadsheet";
    var DEFAULT_ERROR_MESSAGE = "An unknown exception occurred during processing.";
    var DEFAULT_SERVER_ERROR_STATUS = "SERVER ERROR";
    var DEFAULT_ERROR_STATUS = "ERROR";

    if (typeof window.SkiSlope == "undefined") {
        alert("Module was not initialized (desmos-initial-state.js).");
        return;
    }
    var calculator = Desmos.GraphingCalculator(document.getElementById("calculator"), {border: false});
    window.SkiSlope.calculator = calculator;

    // scales the graph according to the imported measurements
    function scaleGraph(x, y) {
        var oneThirdHeight = Math.max.apply(null, y) / 3;
        calculator.setMathBounds({
            left: X_AXIS_LEFT,
            right: Math.max(MIN_X_AXIS_RIGHT, Math.max.apply(null, x) * 1.5),
            bottom: -oneThirdHeight,
            top: Math.max.apply(null, y) + oneThirdHeight
        });
    }

    // populates the expression list
    function initializeExpressions() {
        // restore a previously saved state
        calculator.setState(SkiSlope.initialGraphState);

        var params = {};

        // listen for changes to expression values
        var listener_h = calculator.HelperExpression({latex: "h"});
        listener_h.observe("numericValue", function() {
            params.h = listener_h.numericValue;
        });

        var listener_b = calculator.HelperExpression({latex: "b"});
        listener_b.observe("numericValue", function() {
            params.b = listener_b.numericValue;
        });

        var listener_v = calculator.HelperExpression({latex: "v"});
        listener_v.observe("numericValue", function() {
            params.v = listener_v.numericValue;
        });

        var listener_p = calculator.HelperExpression({latex: "p"});
        listener_p.observe("numericValue", function() {
            params.p = listener_p.numericValue;
        });

        var listener_data_x1 = calculator.HelperExpression({latex: "x_1"});
        listener_data_x1.observe("listValue", function() {
            params.x1 = listener_data_x1.listValue;
        });

        var listener_data_y1 = calculator.HelperExpression({latex: "y_1"});
        listener_data_y1.observe("listValue", function() {
            params.y1 = listener_data_y1.listValue;
        });

        return params;

        // unfortunately, the below method does not allow adding of notes. Commenting out but retaining
        // since it is useful in case the expression list must be rebuilt from scratch.
        /*
        calculator.setExpressions([
            {id: "func", latex: "y_1\\sim h\\cdot\\cos\\left(\\frac{2\\left(x_1+v\\right)\\pi}{p}\\right)+b"}
            , {id: "h", latex: "h = 700", label: "h", sliderBounds: {min: "-10", max: "1000", step: "0.001"}}
            , {id: "b", latex: "b = 200", label: "b", sliderBounds: {min: "-10", max: "1000", step: "0.001"}}
            , {id: "v", latex: "v = 0", label: "v", sliderBounds: {min: "-10", max: "10", step: "0.001"}}
            , {id: "p", latex: "p = 24", label: "p", sliderBounds: {min: "-10", max: "100", step: "0.001"}}
        ]);
        */
    }

    // adds the measurement data to the expression list, and calls the scale function
    function importData(x, y) {
        // add the table
        calculator.setExpression({id: "data", type: "table", columns: [
                {latex: "x_1", values: x}
                , {latex: "y_1", values: y}
        ]});

        // listen for the deletion of the table data
        var helper = calculator.HelperExpression({latex: "x_1"});
        helper.observe("listValue", function() {
            if (typeof helper.listValue == "undefined"
                    && $(".dcg-expressiontable[expr-id=data]").length == 0) {
                // table deleted; display import button
                $("#upload_button_row").show();
            }
        });

        // scale graph according to imported data
        scaleGraph(x, y);

        // hide the import button
        $("#upload_button_row").hide();
    }

    // the user-selected values will be recorded into the `params` object
    var params = initializeExpressions();

    // remove the new-expression button at bottom of list
    $(".dcg-new-expression").remove();

    // remove the list-collapse button
    $(".dcg-action-hideexpressions").remove();

    // move upload button to bottom of expression list and display it
    $("#upload_button_row").appendTo(".dcg-template-expressioneach").show();

    // move calculate button to top bar and display it
    $("#calculate_button_row").appendTo(".dcg-expression-top-bar .dcg-right-buttons").show();

    // move the regression options panel into place
    $("#regression_options").prependTo(".dcg-exppanel");

    // handle checkbox interactions in the regression options panel
    $("#regression_options").on("click mouseenter mouseleave", ".dcg-component-checkbox", function(e) {
        var $this = $(this);
        if (e.type == "click") {
            if ($this.hasClass("dcg-checked"))
                $this.removeClass("dcg-checked");
            else
                $this.addClass("dcg-checked");
        }
        else if (e.type == "mouseenter") {
            $(".dcg-maxLabel").addClass("highlighted-bounds");
            $this.addClass("dcg-hovered");
        }
        else if (e.type == "mouseleave") {
            $(".dcg-maxLabel").removeClass("highlighted-bounds");
            $this.removeClass("dcg-hovered");
        }
    });

    // handle the import of a spreadsheet file
    // button is not always present, so bind to the top-level element
    $("#calculator").on("change", "#upload_button", function() {
        var $this = $(this);
        var inputName = $this.attr("name");
        var files = $this.get(0).files;
        if (files.length == 1) {
            var file = files[0];
            var formData = new FormData();
            formData.append(inputName, file);

            // submit spreadsheet to server for parsing and populate the Desmos table with results
            $.ajax({
                type: "POST",
                url: IMPORT_BUTTON_URL,
                data: formData,
                cache: false,
                contentType: false,
                processData: false,
                dataType: "json",
                success: function(response, textStatus, jqXHR) {
                    if (!response) {
                        displayError("Import failed; server response was empty!");
                    }
                    else if (response.hasOwnProperty("x") && response.hasOwnProperty("y")) {
                        // add the parsed spreadsheet values as an expression table
                        importData(response.x, response.y);
                    }
                    else {
                        displayError("Import failed; server response was missing data!");
                    }
                },
                error: function(jqXHR, textStatus, errorThrown) {
                    console.log(jqXHR);
                    console.log(textStatus, errorThrown)
                    var responseText = jqXHR.responseText;
                    if (jqXHR.hasOwnProperty("responseJSON")) {
                        displayCaughtException(jqXHR.responseJSON);
                    }
                    else if (typeof responseText != "undefined") {
                        if (isHtml(responseText)) {
                            displayUncaughtException(responseText, errorThrown);
                        }
                        else {
                            displayError(responseText);
                        }
                    }
                    else {
                        displayError(DEFAULT_ERROR_MESSAGE);
                    }
                },
                beforeSend: function() {
                    $("#upload_spinner_container > img").show();
                },
                complete: function() {
                    $("#upload_spinner_container > img").hide();
                }
            });
        }
     });

     // handle the `Calculate Regression` button
    $("#calculate_button").on("click", function() {
        var $this = $(this);
        var $panel = $("#regression_options");
        if ($panel.is(":visible")) {
            $this.removeClass("panel-opened");
            $panel.hide();
        }
        else {
            $this.addClass("panel-opened");
            $panel.show();
        }
    });

    // handle the "Run" button
    $("#run_button").on("click", function() {
        // get the table values
        if (validateParamsBeforeRun()) {
            // construct the POST request
            var formData = {};
            formData.x = params.x1;
            formData.y = params.y1;
            formData.h = params.h;
            formData.b = params.b;
            formData.v = params.v;
            formData.p = params.p;
            formData.max_nfev = $("#max_nfev").val();

            // check if bounds were specified
            var specifyBounds = $("#regression_options .dcg-component-checkbox").hasClass("dcg-checked");
            if (specifyBounds) {
                formData.specify_bounds = "specify_bounds";
                formData.h_lower = $("#h_lower").val();
                formData.b_lower = $("#b_lower").val();
                formData.v_lower = $("#v_lower").val();
                formData.p_lower = $("#p_lower").val();

                formData.h_upper = $("#h_upper").val();
                formData.b_upper = $("#b_upper").val();
                formData.v_upper = $("#v_upper").val();
                formData.p_upper = $("#p_upper").val();
            }

            // submit POST
            $.ajax({
                type: "POST",
                url: RUN_BUTTON_URL,
                data: formData,
                cache: false,
                contentType: "application/x-www-form-urlencoded; charset=UTF-8",
                success: function(response, textStatus, jqXHR) {
                    if (!response) {
                        displayError("Server response was empty.");
                    }
                    else {
                        displayRegressionResults(response);
                    }
                },
                error: function(jqXHR, textStatus, errorThrown) {
                    console.log(jqXHR);
                    console.log(textStatus, errorThrown)
                    var responseText = jqXHR.responseText;
                    if (jqXHR.hasOwnProperty("responseJSON")) {
                        displayCaughtException(jqXHR.responseJSON);
                    }
                    else if (typeof responseText != "undefined") {
                        if (isHtml(responseText)) {
                            displayUncaughtException(responseText, errorThrown);
                        }
                        else {
                            displayError(responseText);
                        }
                    }
                    else {
                        displayError(DEFAULT_ERROR_MESSAGE);
                    }
                },
                beforeSend: function() {
                    $("#run_button_container > img").show();
                },
                complete: function() {
                    $("#run_button_container > img").hide();
                }
            });
        }
    });

    function validateParamsBeforeRun() {
        // just need to validate the imported data since param sliders start with values
        var valid = true;
        var missingCols = [];
        if (!params.hasOwnProperty("x1") || typeof params.x1 == "undefined") {
            valid = false;
            missingCols.push("x1");
        }
        if (!params.hasOwnProperty("y1") || typeof params.y1 == "undefined") {
            valid = false;
            missingCols.push("y1");
        }
        if (!valid) {
            displayError("Imported data not found ("+missingCols.join(", ")+" column"+(missingCols.length > 1 ? "s" : "")+" missing).");
        }
        return valid;
    }

    function displayRegressionResults(response) {
        var missingParams = [];
        var exprList = [];
        var paramNames = ["h", "b", "v", "p"];
        for (var i=0; i<paramNames.length; i++) {
            var paramName = paramNames[i];
            if (response.hasOwnProperty(paramName)) {
                // construct expression which will overwrite the current value
                exprList.push({
                    id: paramName,
                    latex: paramName + " = " + response[paramName],
                    label: paramName
                });
            }
            else {
                missingParams.push(paramName);
            }
        }
        // if no response params were missing, update the slider values
        if (missingParams.length == 0) {
            for (var i=0; i<exprList.length; i++) {
                calculator.setExpression(exprList[i]);
            }
        }
        else {
            displayError("Server response was missing params: " + missingParams.join(", "));
        }
    }

    function displayCaughtException(response) {
        var msg = response.description || DEFAULT_ERROR_MESSAGE;
        var status = response.name || DEFAULT_SERVER_ERROR_STATUS;
        if (response.hasOwnProperty("code")) {
            status += " ("+response.code+")";
        }
        displayError(msg, status);
    }

    function isHtml(str) {
        var doc = new DOMParser().parseFromString(str, "text/html");
        return Array.from(doc.body.childNodes).some(function(node) {
            return node.nodeType == 1;
        });
    }

    function displayUncaughtException(html, textStatus) {
        var $dialog = createErrorDialog();
        var $iframe = $("<iframe></iframe>").appendTo($dialog);
        var iframe = $iframe.get(0);
        iframe = iframe.contentWindow || (iframe.contentDocument.document || iframe.contentDocument);
        iframe.document.open();
        iframe.document.write(html);
        iframe.document.close();

        $dialog.dialog("option", "title", '<span class="ui-icon ui-icon-alert"></span><span>'+textStatus+'</span>');
        $dialog.dialog("option", "width", 1000);
        $dialog.dialog("option", "height", 650);
        $dialog.dialog("open");
    }

    function displayError(str, textStatus = "ERROR") {
        var $dialog = createErrorDialog();
        $dialog.html("<p>"+str+"</p>");
        $dialog.dialog("option", "title", '<span class="ui-icon ui-icon-alert"></span><span>'+textStatus+'</span>');
        $dialog.dialog("option", "width", 375);
        $dialog.dialog("open");
    }

    function createErrorDialog() {
        var $dialog = $("#error_dialog").dialog({
            autoOpen: false,
            width: "auto",
            height: "auto",
            maxHeight: 650,
            maxWidth: 1200,
            appendTo: "#error_dialog_container",
            position: {
                my: "left top-100",
                at: "left+50 middle",
                of: ".dcg-exp-list-resizer",
                within: ".dcg-grapher"
            },
            classes: {
                "ui-dialog": "dcg-popover-interior",
                "ui-dialog-titlebar": "ui-corner-all ui-state-error",
            },
            buttons: {
                "OK": function() {
                    $dialog.dialog("close");
                }
            },
            close: function() {
                $dialog.dialog("destroy");
                $dialog.empty();
            }
        });
        $dialog.data("uiDialog")._title = function(title) {
            title.html(this.options.title);
        };
        return $dialog;
    }

    function clearError() {
        var $diag = $("#error_dialog").dialog("instance");
        if ($diag)
            $diag.close();
    }

})(jQuery);
