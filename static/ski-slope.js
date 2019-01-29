jQuery(function($) {
    var DEFAULT_ERROR_MESSAGE = "An unknown exception occurred during processing.";
    var DEFAULT_SERVER_ERROR_STATUS = "SERVER ERROR";

    var $zdistHeader = $("#zdist_header");
    var $zdistForm = $("#zdist_form");
    var $zdistErrorLog = $("#zdist_form .error_log");
    var $zdistImageContainer = $("#zdist_form .image_container");
    var $zdistResultsContainer = $("#zdist_form .calc_results_container");

    var $lsqHeader = $("#lsq_header");
    var $lsqForm = $("#lsq_form");
    var $lsqErrorLog = $("#lsq_form .error_log");
    var $lsqImageContainer = $("#lsq_form .image_container");
    var $lsqResultsContainer = $("#lsq_form .calc_results_container");

    // starts with zdist panel showing
    var $form = $zdistForm;
    var $errorLog = $zdistErrorLog;
    var $imageContainer = $zdistImageContainer;
    var $resultsContainer = $zdistResultsContainer;

    // init analysis selector
    $("#analysis").selectmenu({
        width: "auto",
        change: function(event, ui) {
            var val = $(this).val();
            if (val == "lsq") {
                $zdistHeader.hide();
                $zdistForm.hide();
                $lsqHeader.show();
                $lsqForm.show();
                $form = $lsqForm;
                $errorLog = $lsqErrorLog;
                $imageContainer = $lsqImageContainer;
                $resultsContainer = $lsqResultsContainer;
            }
            else {
                $lsqHeader.hide();
                $lsqForm.hide();
                $zdistHeader.show();
                $zdistForm.show();
                $form = $zdistForm;
                $errorLog = $zdistErrorLog;
                $imageContainer = $zdistImageContainer;
                $resultsContainer = $zdistResultsContainer;
            }
            clearError();
        }
    });

    // toggle the bounds section using a checkbox
    $("#specify_bounds").change(function() {
        if ($(this).is(":checked")) {
            $("#bounds input").prop("disabled", false);
            $("#bounds_overlay").css("z-index", -1);
        }
        else {
            $("#bounds input").prop("disabled", true);
            $("#bounds_overlay").css("z-index", 1);
        }
    });

    // asynchronous form submission
    $("form").submit(function(e) {
        clearError();
        clearImage();
        var $form = $(this);
        $.ajax({
            type: "POST",
            url: $form.attr("action"),
            data: new FormData(this),
            cache: false,
            contentType: false,
            processData: false,
            xhr: function() {
                var xhr = $.ajaxSettings.xhr();
                xhr.responseType = "text";
                xhr.onreadystatechange = function() {
                    if (xhr.readyState == 2) {
                        if (xhr.status == 200) {
                            // successful requests will return an image blob
                            xhr.responseType = "blob";
                        }
                    }
                }
                return xhr;
            },
            success: function(response, textStatus, jqXHR) {
                if (!response) {
                    displayError("Expected an image, but the server response was empty.");
                }
                else {
                    // generate a local URL for the received image blob
                    var url = window.URL || window.webkitURL;
                    var src = url.createObjectURL(response);
                    displayImage(src);
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
                $form.find(".spinner").show();
            },
            complete: function() {
                $form.find(".spinner").hide();
            }
        });
        e.preventDefault();
    });

    function displayError(str, textStatus = "ERROR") {
        $errorLog.append("<span style='padding-right: 10px;'>[" + textStatus +"]</span> " + str).fadeIn(150);
    }

    function isHtml(str) {
        var doc = new DOMParser().parseFromString(str, "text/html");
        return Array.from(doc.body.childNodes).some(function(node) {
            return node.nodeType == 1;
        });
    }

    function displayCaughtException(responseJSON) {
        var msg = responseJSON.description || DEFAULT_ERROR_MESSAGE;
        var status = responseJSON.name || DEFAULT_SERVER_ERROR_STATUS;
        if (responseJSON.hasOwnProperty("code")) {
            status += " ("+responseJSON.code+")";
        }
        displayError(msg, status);
    }

    function displayUncaughtException(html, textStatus) {
        var $iframe = $('<iframe></iframe>').appendTo($errorLog);
        var iframe = $iframe.get(0);
        iframe = iframe.contentWindow || (iframe.contentDocument.document || iframe.contentDocument);
        iframe.document.open();
        iframe.document.write(html);
        iframe.document.close();
        $errorLog.fadeIn(150);
    }

    function clearError() {
        $errorLog.empty().css("display", "none");
    }

    function displayImage(src) {
        $("<img/>").attr("src", src).appendTo($imageContainer).parent().fadeIn();
    }

    function clearImage() {
        $imageContainer.empty().css("display", "none");
    }
});