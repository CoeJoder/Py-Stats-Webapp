(function($) {
    const DEFAULT_ERROR_MESSAGE = "An unknown exception occurred during processing.";
    const DEFAULT_SERVER_ERROR_STATUS = "SERVER ERROR";
    const WTFORMS_FIELD_SEPARATOR = "-";

    // returns true if string is valid HTML
    function isHtml(str) {
        const doc = new DOMParser().parseFromString(str, "text/html");
        return Array.from(doc.body.childNodes).some(function(node) {
            return node.nodeType == 1;
        });
    }

    // encapsulation of DOM elements representing an analysis
    function Analysis(id) {
        this.id = id
        this.$form = $("form[data-analysis-id='"+id+"']");
        this.$errorLog = this.$form.find(".error_log");
        this.$imageContainer = this.$form.find(".image_container");
        this.$resultsContainer = this.$form.find(".calc_results_container");
        const that = this;

        // clear validation errors on change
        this.$form.find("input").change(function() {
            that.clearValidationErrors($(this));
        })

        // display uploaded filename on selection
        this.$form.find(".browse-button input").change(function() {
            const $this = $(this);
            const fileList = $this.prop("files");
            if (fileList && fileList.length > 0) {
                $this.closest(".browse-button").find(".filename").text(fileList[0].name);
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
                        if (jqXHR.responseJSON.hasOwnProperty("errors")) {
                            that.processValidationErrors(jqXHR.responseJSON.errors);
                        }
                        else {
                            that.displayCaughtException(jqXHR.responseJSON);
                        }
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

        Analysis.prototype.show = function() {
            this.$form.show();
        }

        Analysis.prototype.hide = function() {
            this.$form.hide();
        }

        Analysis.prototype.processValidationErrors = function(errors) {
            console.log(errors);
            // errors are in a nested tree structure per the WTForms validator
            // node keys are joined with a separator to form field names
            // leaf nodes are arrays of errors strings
            const that = this;
            _processValidationErrors(errors, []);

            // recursive function is OK since widget model is very shallow
            function _processValidationErrors(curObj, keyStack) {
                if (Array.isArray(curObj)) {
                    that.displayValidationError(keyStack.join(WTFORMS_FIELD_SEPARATOR), curObj.pop());
                }
                else {
                    for (key in curObj) {
                        keyStack.push(key);
                        _processValidationErrors(curObj[key], keyStack);
                    }
                }
                keyStack.pop();
            }
        }

        Analysis.prototype.displayValidationError = function(fieldName, errorMessage) {
            // DOM input names are in `name` attributes, widget names are in `data-field-name` attributes
            // if browse button, set the error message in-line.
            // if any other widget, set input elements to error state, labels to error text, and append to error log.
            // if input element, set the error state and append to error log.
            let $input = this.$form.find("input[name='"+fieldName+"']");
            let $widget = this.$form.find("[data-field-name='"+fieldName+"']");
            let $browseButton = $input.closest(".browse-button");
            if ($browseButton.length > 0) {
                $browseButton.find(".error-message").text(errorMessage).show();
            }
            else {
                if ($widget.length > 0) {
                    $widget.addClass("ui-state-error-text").find("input").addClass("ui-state-error");
                }
                else {
                    $input.addClass("ui-state-error");
                }
                this.displayError(errorMessage);
            }
        }

        /**
         * $elm - input or widget.  Exclude to clear all validation errors.
         */
        Analysis.prototype.clearValidationErrors = function($elm) {
            if (typeof $elm == "undefined") {
                clear(this.$form.find("input"), this.$form.find("[data-field-name]"), this.$form.find(".browse-button"));
            }
            else {
                clear($elm.closest("input"), $elm.closest("[data-field-name]"), $elm.closest(".browse-button"));
            }
            this.clearError();

            function clear($input, $widget, $browse) {
                $input.removeClass("ui-state-error");
                $widget.removeClass("ui-state-error-text").find("input").removeClass("ui-state-error");
                $browse.find(".error-message").text("").hide();
            }
        }

        Analysis.prototype.displayError = function(str, textStatus) {
            textStatus = textStatus || "ERROR";
            this.$errorLog.append("<div><span style='padding-right: 10px;'>[" + textStatus +"]</span> " + str + "</div>").fadeIn(150);
        }

        Analysis.prototype.displayCaughtException = function(responseJSON) {
            const msg = responseJSON.description || DEFAULT_ERROR_MESSAGE;
            let status = responseJSON.name || DEFAULT_SERVER_ERROR_STATUS;
            if (responseJSON.hasOwnProperty("code")) {
                status += " ("+responseJSON.code+")";
            }
            this.displayError(msg, status);
        }

        Analysis.prototype.displayUncaughtException = function(html, textStatus) {
            const $iframe = $('<iframe></iframe>').appendTo(this.$errorLog);
            let iframe = $iframe.get(0);
            iframe = iframe.contentWindow || (iframe.contentDocument.document || iframe.contentDocument);
            iframe.document.open();
            iframe.document.write(html);
            iframe.document.close();
            this.$errorLog.fadeIn(150);
        }

        Analysis.prototype.clearError = function() {
            this.$errorLog.empty().hide();
        }

        Analysis.prototype.displayImage = function(src) {
            $("<img/>").attr("src", src).appendTo(this.$imageContainer).parent().fadeIn();
        }

        Analysis.prototype.clearImage = function() {
            this.$imageContainer.empty().hide();
        }
    }

    // on document load
    $(function() {
        // replace Analysis ids with instances
        const instances = [];
        for (let i = 0; i < window.SkiStats.analyses.length; i++) {
            let id = window.SkiStats.analyses[i];
            instances.push(new Analysis(id));
        }
        window.SkiStats.analyses = instances;

        // show current analysis
        window.SkiStats.$analysisSelector.selectmenu("option", "change").bind(window.SkiStats.$analysisSelector)();
    });
})(jQuery);
