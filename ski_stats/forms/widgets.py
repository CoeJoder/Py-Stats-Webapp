from wtforms.widgets import HTMLString
from wtforms.widgets import html_params
from flask import url_for


class TitleWidget(object):
    """Renders a header."""
    def __call__(self, field, **kwargs):
        text = kwargs["text"]
        show_desmos_link = kwargs.pop("show_desmos_link", False)
        if show_desmos_link:
            template = u"""
            <h2 class="title">
                {text}
                <a class="desmos_link" href="/desmos">
                    <img class="ui-corner-all" src="{desmos_logo}">
                </a>
            </h2>
            """
        else:
            template = u'<h2 class="title">{text}</h2>'
        return HTMLString(template.format(text=text, desmos_logo=url_for('static', filename='desmos_logo.png')))


class NumberInputWidget(object):
    """Renders a number input."""
    def __call__(self, field, **kwargs):
        kwargs.setdefault("type", "number")
        return _input(field, **kwargs)


class TextInputWidget(object):
    """Renders a text input."""
    def __call__(self, field, **kwargs):
        kwargs.setdefault("type", "text")
        return _input(field, **kwargs)


class MathEquationWidget(object):
    """Renders an empty div which will be populated by JavaScript on document load."""
    def __call__(self, field, **kwargs):
        return HTMLString(u'<div class="math-equation" {attributes}></div>'.format(attributes=html_params(**kwargs)))


class BrowseButtonWidget(object):
    """Renders a file input button."""
    def __call__(self, field, **kwargs):
        kwargs.setdefault("type", "file")
        kwargs.setdefault("name", field.name)
        button_text = kwargs.pop("button_text", "Browse...")

        return HTMLString(u"""
        <div class="browse-button">
            <label>
                <span class="ui-button ui-widget ui-corner-all" role="button">
                    {button_text}
                </span>
                <input style="display: none;" {attributes}/>
            </label>
            <span class="filename"></span>
            <span class="error-message ui-state-error-text"></span>
        </div>
        """.format(attributes=html_params(**kwargs), button_text=button_text))


class RunButtonWidget(object):
    """Renders a form submission button."""
    def __call__(self, field, **kwargs):
        kwargs.setdefault("value", "Upload")
        button_text = kwargs.pop("button_text", "Run")
        icon_class = kwargs.pop("icon_class", "ui-icon ui-icon-gear")

        return HTMLString(u"""
        <div class="run-button">
            <button class="ui-button ui-widget ui-corner-all" type="submit" {attributes}>
                <span class="{icon_class}"></span> {button_text}
            </button>
            <img class="spinner" src="{spinner_url}" style="display: none;"/>
        </div>
        """.format(button_text=button_text, icon_class=icon_class, attributes=html_params(**kwargs), spinner_url=url_for("static", filename="spinner.gif")))


class TopLevelWrapper(object):
    """Renders the wrapped widget as a top-level field."""
    def __init__(self, base_widget, show_label=True):
        self.base_widget = base_widget
        self.show_label = show_label

    def __call__(self, field, **kwargs):
        if self.show_label:
            template = u"""
            <div class="field">
                <div>{label}</div>
                <div>{field}</div>
            </div>
            """
        else:
            template = u"""
            <div class="field">
                <div>{field}</div>
            </div>
            """
        return HTMLString(template.format(label=field.label.text, field=self.base_widget.__call__(field, **kwargs)))


class AdjacentInlineWidget(object):
    """Form widget.  Renders a list of fields as adjacent and in-line."""
    def __init__(self, use_latex_labels=False):
        self.use_latex_labels = use_latex_labels

    def __call__(self, field, **kwargs):
        html_fields = []
        hidden = ''
        for subfield in field:
            if subfield.type in ('HiddenField', 'CSRFTokenField'):
                hidden += subfield
            else:
                if self.use_latex_labels:
                    latex_attributes = {"data-latex": subfield.label.text}
                    html_fields.append(u'<span class="math-equation" {latex_attributes}></span>: {field}'.format(
                        latex_attributes=html_params(**latex_attributes), field=subfield))
                else:
                    html_fields.append(u"{0}: {1}".format(subfield.label.text, subfield))
        if hidden:
            html_fields.append(hidden)

        return HTMLString(u'<div class="adjacent-inline">{fields}</div>'.format(fields="".join(html_fields)))


class AdjacentRowsWidget(object):
    """Form widget.  Renders a list of fields as adjacent rows."""
    def __init__(self, num_columns, show_labels=True, use_latex_labels=False):
        self.num_columns = num_columns
        self.show_labels = show_labels
        self.use_latex_labels = use_latex_labels

    def __call__(self, field, **kwargs):
        html_fields = []
        cur_row = []
        hidden = ''
        for i, subfield in enumerate(field):
            if subfield.type in ('HiddenField', 'CSRFTokenField'):
                hidden += subfield
            else:
                if len(cur_row) >= self.num_columns:
                    html_fields.append(u"<div>{row}</div>".format(row="".join(cur_row)))
                    cur_row = []
                if self.show_labels:
                    if self.use_latex_labels:
                        latex_attributes = {"data-latex": subfield.label.text}
                        cur_row.append(u'<span class="math-equation" {latex_attributes}></span>: {field}'.format(
                            latex_attributes=html_params(**latex_attributes), field=subfield))
                    else:
                        cur_row.append(u"{label}: {field}".format(label=subfield.label.text, field=subfield))
                else:
                    cur_row.append(u"{field}".format(field=subfield))

        html_fields.append(u"<div>{row}</div>".format(row="".join(cur_row)))
        if hidden:
            html_fields.append(u"<div>{hidden}</div>".format(hidden=hidden))
        return HTMLString(u'<div class="adjacent-rows">{fields}</div>'.format(fields="".join(html_fields)))


class InequalityWidget(object):
    """Form widget.  Renders inputs arranged as an inequality."""
    def __init__(self, param_name):
        self.param_name = param_name

    def __call__(self, field, **kwargs):
        widget_attrs = {
            "data-field-name": field.name
        }
        latex_attrs = {
            "data-latex": r"\leq {0} \leq".format(self.param_name),
        }
        field_list = list(field)
        min_field = field_list[0]
        max_field = field_list[1]
        return HTMLString(u"""
        <span class="inequality" {widget_attrs}>
            {min} <span class="math-equation" {latex_attrs}></span> {max}
        </span>""".format(min=min_field, widget_attrs=html_params(**widget_attrs), latex_attrs=html_params(**latex_attrs), max=max_field))


def _append_classes(kwargs, *classes_to_add):
    """Utility.  Adds to the `class_` of widget keyword args."""
    classes = kwargs["class_"].split() if "class_" in kwargs else []
    kwargs["class_"] = " ".join(set(classes).union(classes_to_add))


def _input(field, **kwargs):
    """Factor.  Renders an input."""
    _append_classes(kwargs, "ui-widget", "ui-corner-all")
    kwargs.setdefault("name", field.name)

    return HTMLString(u"""
    <input {attributes}/>
    """.format(attributes=html_params(**kwargs)))

