from django import forms


class BaseMultipleValuesField(forms.CharField):
    delimiter = None

    def __init__(self, *args, **kwargs):
        self.coerce = kwargs.pop('coerce', lambda value: value)
        self.delimiter = kwargs.pop('delimiter', None) or self.delimiter
        super(BaseMultipleValuesField, self).__init__(*args, **kwargs)

    def clean(self, value):
        value = super(BaseMultipleValuesField, self).clean(value)
        return self.values_coerce(value)

    def values_coerce(self, value):
        if value in self.empty_values:
            return None
        values = []
        for vitem in value:
            try:
                values.append(self.coerce(vitem))
            except (ValueError, TypeError, forms.ValidationError):
                raise forms.ValidationError('Value "%s" is incorrect.' % vitem)
        return values

    def to_python(self, value):
        # value convertation from string to python list
        sprtp = super(BaseMultipleValuesField, self).to_python
        value = ([sprtp(i).strip() for i in value]
                 if isinstance(value, list) else
                 [i.strip() for i in sprtp(value).split(self.delimiter)])
        return value

    def prepare_value(self, value):
        # value convertation from python list to string
        if isinstance(value, (list, tuple)):
            value = self.delimiter.join([unicode(i) for i in value])
        return value


class CharMultipleValuesField(BaseMultipleValuesField):
    widget = forms.TextInput
    delimiter = u','


class TextMultipleValuesField(BaseMultipleValuesField):
    widget = forms.Textarea
    delimiter = u'\n'
