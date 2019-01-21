////////////TODO
////////////-ensure that initial guess is within bounds if specified
jQuery(function($) {
    var UNKNOWN_ERROR = "An unknown exception occurred during processing.";

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
    $("#spreadsheet_upload").submit(function(e) {
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
                else if (response.hasOwnProperty("message")) {
                    displayError(response.message || UNKNOWN_ERROR);
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
                console.error(textStatus, errorThrown)
                if (typeof jqXHR.responseText != "undefined") {
                    displayError(jqXHR.responseText, errorThrown);
                }
                else {
                    displayError(UNKNOWN_ERROR);
                }
            },
            beforeSend: function() {
                $("#spinner").show();
            },
            complete: function() {
                $("#spinner").hide();
            }
        });
        e.preventDefault();
    });

    function displayError(str, textStatus = "ERROR") {
        $("#error_log").append("<span style='padding-right: 10px;'>[" + textStatus +"]</span> " + str).fadeIn(150);
    }

    function clearError() {
        $("#error_log").empty().css("display", "none");
    }

    function displayImage(src) {
        $("<img/>").attr("src", src).appendTo("#image_container").parent().fadeIn();
    }

    function clearImage() {
        $("#image_container").empty().css("display", "none");
    }
});