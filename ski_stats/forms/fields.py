from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import Field, DecimalField, StringField, SubmitField, FormField
from wtforms.validators import NumberRange
from wtforms.widgets import HTMLString
from ski_stats.forms import widgets
from ski_stats.forms.validators import NumpyValidator, CorrectDataRequired
from ski_stats.common import parse_workbook
from cgi import escape
from xlrd import open_workbook
from fastnumbers import fast_real
import numpy as np


class Title(Field):
    """Title header."""
    widget = widgets.TitleWidget()

    def __init__(self, text, show_desmos_link=False, **kwargs):
        render_kw = kwargs.setdefault("render_kw", {})
        render_kw["text"] = escape(text)
        render_kw["show_desmos_link"] = show_desmos_link
        super(Title, self).__init__(**kwargs)


class BrowseSpreadsheetInput(FileField):
    """Browse button for spreadsheet files."""
    widget = widgets.TopLevelWrapper(widgets.BrowseButtonWidget())

    def __init__(self, label="Select file", **kwargs):
        validators = [
            FileRequired(),
            FileAllowed(["xls", "xlsx"], "File must be an Excel spreadsheet.")
        ]
        super(BrowseSpreadsheetInput, self).__init__(label=label, validators=validators, **kwargs)

    def parse(self):
        """Returns (time, data) as NumPy arrays."""
        return parse_workbook(open_workbook(file_contents=self.data.read()))


class NumberInput(DecimalField):
    """Numeric input."""
    widget = widgets.TopLevelWrapper(widgets.NumberInputWidget())

    def __init__(self, label="Enter a number", validators=None, required=True, default=None, size=None, is_subfield=False, min=None, max=None, **kwargs):
        validators = validators or []
        if required:
            validators.append(CorrectDataRequired())
        if min is not None or max is not None:
            validators.append(NumberRange(min=min, max=max))

        # append bounds to label and as input attributes
        render_kw = kwargs.setdefault("render_kw", {})
        render_kw["required"] = required
        bounds = ""
        if min is not None and max is not None:
            bounds = " ({0}-{1})".format(min, max)
            render_kw["min"] = min
            render_kw["max"] = max
        elif min is not None:
            bounds = " ({0} minimum)".format(min)
            render_kw["min"] = min
        elif max is not None:
            bounds = " ({0} maximum)".format(max)
            render_kw["max"] = max

        if size is not None:
            render_kw["style"] = "width: {0}em".format(escape(str(size)))
        if default is not None:
            render_kw["value"] = default
        if is_subfield:
            kwargs["widget"] = NumberInput.widget.base_widget

        label = HTMLString("{label}{bounds}".format(label=label, bounds=bounds))
        super(NumberInput, self).__init__(label=label, validators=validators, **kwargs)


class TextInput(StringField):
    """Text input."""
    widget = widgets.TopLevelWrapper(widgets.TextInputWidget())

    def __init__(self, label=None, validators=None, required=True, size=None, default=None, is_subfield=False, **kwargs):
        validators = validators or []
        if required:
            validators.append(CorrectDataRequired())

        # set the input attributes
        render_kw = kwargs.setdefault("render_kw", {})
        render_kw["required"] = required
        if size is not None:
            render_kw["size"] = size
        if default is not None:
            render_kw["value"] = default
        if is_subfield:
            kwargs["widget"] = TextInput.widget.base_widget

        super(TextInput, self).__init__(label=label, validators=validators, **kwargs)


class NumpyInput(TextInput):
    """Text input for NumPy values."""
    def __init__(self, label=None, validators=None, required=True, size=None, default=None, is_subfield=False, **kwargs):
        validators = validators or []
        validators.append(NumpyValidator())
        super(NumpyInput, self).__init__(label=label, validators=validators, required=required, size=size, default=default, is_subfield=is_subfield, **kwargs)

    @property
    def numpy_val(self):
        """Convert field data to a NumPy-compatible numerical values"""
        if self.data == "inf" or self.data == "+inf":
            return np.inf
        elif self.data == "-inf":
            return -np.inf
        else:
            return fast_real(self.data)


class MathEquation(Field):
    """A LaTeX-rendered field."""
    widget = widgets.TopLevelWrapper(widgets.MathEquationWidget())

    def __init__(self, label=None, latex="", **kwargs):
        render_kw = kwargs.setdefault("render_kw", {})
        render_kw["data-latex"] = escape(latex)
        super(MathEquation, self).__init__(label=label, validators=[], **kwargs)


class RunButton(SubmitField):
    """Form submission button."""
    widget = widgets.TopLevelWrapper(widgets.RunButtonWidget())

    def __init__(self, label=None, validators=None, button_text=None, **kwargs):
        validators = validators or []
        if button_text is not None:
            render_kw = kwargs.setdefault("render_kw", {})
            render_kw["button_text"] = button_text
        super(RunButton, self).__init__(label=label, validators=validators, **kwargs)


class ParamInput(NumberInput):
    """Numeric input, where the param letter is also the label."""
    def __init__(self, param, validators=None, required=True, size=None, default=None, is_subfield=True, **kwargs):
        validators = validators or []
        self.param = param
        super(ParamInput, self).__init__(label=param, validators=validators, required=required, size=size, default=default, is_subfield=is_subfield, **kwargs)


class ParamBoundsInput(FormField):
    """Bounds input for a param."""
    def __init__(self, param, size=5, default_min=None, default_max=None, required=True, **kwargs):
        self.param = param

        # inner class will encapsulate the actual fields
        class F(FlaskForm):
            min = NumpyInput(label="", size=size, default=default_min, is_subfield=True)
            max = NumpyInput(label="", size=size, default=default_max, is_subfield=True)

            def validate(self):
                if not super(F, self).validate():
                    return False
                self._errors = []
                min_val = self.min.numpy_val
                max_val = self.max.numpy_val
                if not min_val <= max_val:
                    self._errors.append("Lower bound must be less-than-or-equal-to upper bound.")
                    return False
                return True

        render_kw = kwargs.setdefault("render_kw", {})
        render_kw["required"] = required
        super(ParamBoundsInput, self).__init__(F, widget=widgets.InequalityWidget(param_name=param), **kwargs)


class ParamGroup(FormField):
    """Arranges a list of ParamInputs in a row."""
    def __init__(self, label, fields, **kwargs):
        field_dict = {field.kwargs["param"]: field for field in fields}
        form_class = _get_dynamic_form(field_dict)
        super(ParamGroup, self).__init__(form_class, label=label, widget=widgets.TopLevelWrapper(widgets.AdjacentInlineWidget(use_latex_labels=True)), **kwargs)

    def as_list(self, *params):
        # raises a KeyError exception if a param is missing
        return map(self.data.__getitem__, params)


class ParamBoundsGroup(FormField):
    """Arranges a list of ParamBoundsInputs into a column."""
    def __init__(self, label, fields, **kwargs):
        field_dict = {field.kwargs["param"]: field for field in fields}
        form_class = _get_dynamic_form(field_dict)
        super(ParamBoundsGroup, self).__init__(form_class, label=label, widget=widgets.TopLevelWrapper(widgets.AdjacentRowsWidget(num_columns=1, use_latex_labels=True, show_labels=False)), **kwargs)

    def as_minmax_pair(self, *params):
        # raises a KeyError exception if param bounds are missing
        bounds_list = map(self.data.__getitem__, params)
        return [bounds.__getitem__("min") for bounds in bounds_list], [bounds.__getitem__("max") for bounds in bounds_list]


def _get_dynamic_form(fields):
    class F(FlaskForm):
        pass
    for field_name, field in fields.iteritems():
        setattr(F, field_name, field)
    return F

