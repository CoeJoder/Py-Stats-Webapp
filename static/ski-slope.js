(() => {
    const DEFAULT_ERROR_MESSAGE = "An unknown exception occurred during processing.";
    const DEFAULT_SERVER_ERROR_STATUS = "SERVER ERROR";

    // returns true if string is valid HTML
    function isHtml(str) {
        const doc = new DOMParser().parseFromString(str, "text/html");
        return Array.from(doc.body.childNodes).some(function(node) {
            return node.nodeType == 1;
        });
    }

    // encapsulation of DOM elements representing an analysis
    class Analysis {
        constructor(headerSelector, formSelector) {
            this.$header = $(headerSelector);
            this.$form = $(formSelector);
            this.$errorLog = this.$form.find(".error_log");
            this.$imageContainer = this.$form.find(".image_container");
            this.$resultsContainer = this.$form.find(".calc_results_container");
            const that = this;

            // display uploaded filename on selection
            this.$form.find(".upload_button").change(function() {
                const fileList = $(this).prop("files");
                if (fileList && fileList.length > 0) {
                    that.$form.find(".upload_filename").text(fileList[0].name);
                }
            });

            // async form submission
            this.$form.submit(function(e) {
                e.preventDefault();
                that.clearError();
                that.clearImage();
                $.ajax({
                    type: "POST",
                    url: that.$form.attr("action"),
                    data: new FormData(this),
                    cache: false,
                    contentType: false,
                    processData: false,
                    xhr: function() {
                        const xhr = $.ajaxSettings.xhr();
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
                            that.displayError("Expected an image, but the server response was empty.");
                        }
                        else {
                            // generate a local URL for the received image blob
                            const url = window.URL || window.webkitURL;
                            const src = url.createObjectURL(response);
                            that.displayImage(src);
                        }
                    },
                    error: function(jqXHR, textStatus, errorThrown) {
                        console.log(jqXHR);
                        console.log(textStatus, errorThrown)
                        const responseText = jqXHR.responseText;
                        if (jqXHR.hasOwnProperty("responseJSON")) {
                            that.displayCaughtException(jqXHR.responseJSON);
                        }
                        else if (typeof responseText != "undefined") {
                            if (isHtml(responseText)) {
                                that.displayUncaughtException(responseText, errorThrown);
                            }
                            else {
                                that.displayError(responseText);
                            }
                        }
                        else {
                            that.displayError(DEFAULT_ERROR_MESSAGE);
                        }
                    },
                    beforeSend: function() {
                        that.$form.find(".spinner").show();
                    },
                    complete: function() {
                        that.$form.find(".spinner").hide();
                    }
                });
            });
        }

        show() {
            this.$header.show();
            this.$form.show();
        }

        hide() {
            this.$header.hide();
            this.$form.hide();
        }

        displayError(str, textStatus = "ERROR") {
            this.$errorLog.append("<span style='padding-right: 10px;'>[" + textStatus +"]</span> " + str).fadeIn(150);
        }

        displayCaughtException(responseJSON) {
            const msg = responseJSON.description || DEFAULT_ERROR_MESSAGE;
            let status = responseJSON.name || DEFAULT_SERVER_ERROR_STATUS;
            if (responseJSON.hasOwnProperty("code")) {
                status += " ("+responseJSON.code+")";
            }
            this.displayError(msg, status);
        }

        displayUncaughtException(html, textStatus) {
            const $iframe = $('<iframe></iframe>').appendTo(this.$errorLog);
            let iframe = $iframe.get(0);
            iframe = iframe.contentWindow || (iframe.contentDocument.document || iframe.contentDocument);
            iframe.document.open();
            iframe.document.write(html);
            iframe.document.close();
            this.$errorLog.fadeIn(150);
        }

        clearError() {
            this.$errorLog.empty().hide();
        }

        displayImage(src) {
            $("<img/>").attr("src", src).appendTo(this.$imageContainer).parent().fadeIn();
        }

        clearImage() {
            this.$imageContainer.empty().hide();
        }
    }

    // on document load
    jQuery(function($) {

        // we currently have two analyses on the page
        const zdist = window.SkiSlope.zdist = new Analysis("#zdist_header", "#zdist_form");
        const lsq = window.SkiSlope.lsq = new Analysis("#lsq_header", "#lsq_form");

        // for lsq, toggle the bounds section using a checkbox
        lsq.$form.find("#specify_bounds").change(function() {
            if ($(this).is(":checked")) {
                lsq.$form.find("#bounds input").prop("disabled", false);
                lsq.$form.find("#bounds_overlay").css("z-index", -1);
            }
            else {
                lsq.$form.find("#bounds input").prop("disabled", true);
                lsq.$form.find("#bounds_overlay").css("z-index", 1);
            }
        });

        // ensure selected analysis is still displayed on page refresh
        window.SkiSlope.$analysisSelector.selectmenu("option", "change").bind(window.SkiSlope.$analysisSelector)();
    });
})();
