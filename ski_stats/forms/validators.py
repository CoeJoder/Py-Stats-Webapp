from wtforms.validators import DataRequired, ValidationError, StopValidation
from fastnumbers import fast_real
from wtforms.compat import string_types


class CorrectDataRequired(DataRequired):
    """Fixes a bug in the built-in DataRequired validator."""
    def __call__(self, form, field):
        if field.data is None or isinstance(field.data, string_types) and not field.data.strip():
            if self.message is None:
                message = field.gettext('This field is required.')
            else:
                message = self.message
            field.errors[:] = []
            raise StopValidation(message)


class NumpyValidator(object):
    """Checks that the field value can be converted to a NumPy value."""
    def __call__(self, form, field):
        """Convert input values to NumPy-compatible numerical values"""
        if not field.data == "inf" and not field.data == "+inf" and not field.data == "-inf":
            num = fast_real(field.data)
            if not isinstance(num, (int, long, float)):
                raise ValidationError("Invalid value \"{0}\".  Expected: -inf, inf, or a numerical value.".format(field.data))

