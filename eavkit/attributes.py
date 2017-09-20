import datetime
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.utils.dateparse import parse_date, parse_datetime
from eavkit import fields


# Base Attribute class
# --------------------
class BaseAttribute(object):
    datatype = None
    datatype_title = None

    name = None
    slug = None
    description = None
    required = False

    multiple = None
    choices = None

    form_field = None
    data = None

    def __init__(self, name=None, slug=None, required=None, **kwargs):
        self.name = name
        self.slug = slug
        self.description = kwargs.get('description', u'')

        self.required = required if required is not None else self.required
        self.choices = kwargs.get('choices', None)
        self.multiple = kwargs.get('multiple', None)
        self.form_field = kwargs.get('form_field', self.form_field)

        self.data = kwargs.get('data', None)

    def validate(self, value):
        raise NotImplementedError()

    def value_encode(self, value):
        raise NotImplementedError()

    def value_decode(self, value):
        raise NotImplementedError()

    def get_validators(self):
        return [self.validate]

    def to_type(self, value, type, default=None):
        if not isinstance(value, type):
            try:
                value = type(value)
            except Exception:
                value = default
        return value

    def get_form_field_defaults(self):
        kwargs = {
            'label': self.name.capitalize(),
            'required': self.required,
            'help_text': self.description,
        }
        validators = self.get_validators()
        validators and kwargs.update(validators=validators)

        return kwargs

    def get_form_field(self, value=None):
        kwargs = self.get_form_field_defaults()
        kwargs.update(initial=value)
        return self.form_field(**kwargs)

    def clean_attribute_model_instance(self, instance):
        pass


# Attribute Mixins
# ----------------
class ChoicesMixin(BaseAttribute):
    form_field_choices = forms.TypedChoiceField
    form_field_coerce = None

    def clean_attribute_model_instance(self, instance):
        super(ChoicesMixin, self).clean_attribute_model_instance(instance)
        if self.choices:
            for value, title in self.choices:
                decoded = self.value_decode(value)
                if decoded is None:
                    raise ValidationError(_('Choice value "%s" incorrect.')
                                          % value)
                try:
                    self.validate(decoded)
                except ValidationError as e:
                    raise ValidationError(_('Choice value "%s" incorrect: %s.')
                                          % (value, e.message))
            if not len(set(i[0] for i in self.choices)) == len(self.choices):
                raise ValidationError(_('Choice values are not unique.'))

    def get_form_field(self, value=None):
        if not self.choices:
            return super(ChoicesMixin, self).get_form_field(value)

        choices = [(None, u'',)] + [(self.value_decode(cvalue), ctitle)
                                    for cvalue, ctitle in self.choices]
        kwargs = self.get_form_field_defaults()
        kwargs.update(initial=value, choices=choices,
                      coerce=self.form_field_coerce,
                      empty_value=None)
        return self.form_field_choices(**kwargs)


class MultipleMixin(BaseAttribute):
    form_field_multiple = fields.TextMultipleValuesField
    form_field_multiple_delimiter = None
    form_field_coerce = None

    def validate(self, value, entity=None):
        spr = super(MultipleMixin, self)
        if not self.multiple:
            spr.validate(value, entity)
            return

        if not isinstance(value, list):
            value = [value]
        for i in value:
            spr.validate(i, entity)

    def value_decode(self, value, multiple=True):
        spr = super(MultipleMixin, self)
        if not self.multiple or not multiple:
            return spr.value_decode(value)

        if not isinstance(value, list):
            value = [value]
        value = [spr.value_decode(i) for i in value]
        value = [i for i in value if not i is None]
        return value

    def get_form_field(self, value=None):
        if not self.multiple:
            return super(MultipleMixin, self).get_form_field(value)

        kwargs = self.get_form_field_defaults()
        kwargs.update(initial=value, coerce=self.form_field_coerce,
                      delimiter=self.form_field_multiple_delimiter)
        return self.form_field_multiple(**kwargs)


class MultipleChoicesMixin(MultipleMixin, ChoicesMixin):
    form_field_choices_multiple = forms.TypedMultipleChoiceField

    def get_form_field(self, value=None):
        if not self.multiple or not self.choices:
            return super(MultipleChoicesMixin, self).get_form_field(value)

        choices = [(self.value_decode(cvalue, multiple=False), ctitle)
                   for cvalue, ctitle in self.choices]
        kwargs = self.get_form_field_defaults()
        kwargs.update(initial=value, choices=choices,
                      coerce=self.form_field_coerce)
        return self.form_field_choices_multiple(**kwargs)


# Common types base classes
# -------------------------
class BaseStringAttribute(BaseAttribute):
    datatype = 'string'
    datatype_title = _('String')
    form_field = forms.CharField

    def validate(self, value, entity=None):
        if not (isinstance(value, basestring)):
            raise ValidationError(_(u'Must be str or unicode'))

    def value_decode(self, value):
        return unicode(value)

    def value_encode(self, value):
        return value if not value == '' else None


class BaseIntegerAttribute(BaseAttribute):
    datatype = 'int'
    datatype_title = _('Integer')
    form_field = forms.IntegerField

    def validate(self, value, entity=None):
        try:
            int(value)
        except ValueError:
            raise ValidationError(_(u'Must be an integer'))

    def value_decode(self, value):
        return self.to_type(value, int)

    def value_encode(self, value):
        return value


class BaseFloatAttribute(BaseAttribute):
    datatype = 'float'
    datatype_title = _('Float')
    form_field = forms.FloatField

    def validate(self, value, entity=None):
        try:
            float(value)
        except ValueError:
            raise ValidationError(_(u'Must be a float'))

    def value_decode(self, value):
        return self.to_type(value, float)

    def value_encode(self, value):
        return value


# Attribute classes
# -----------------
class StringAttribute(MultipleChoicesMixin, BaseStringAttribute):
    form_field_coerce = unicode
    form_field_multiple_delimiter = '\n'


class TextAttribute(BaseStringAttribute):
    datatype = 'text'
    datatype_title = _('Text')

    def get_form_field_defaults(self):
        kwargs = super(TextAttribute, self).get_form_field_defaults()
        kwargs.update(widget=forms.Textarea)
        return kwargs


class IntegerAttribute(MultipleChoicesMixin, BaseIntegerAttribute):
    form_field_coerce = int
    form_field_multiple_delimiter = '\n'


class FloatAttribute(MultipleChoicesMixin, BaseFloatAttribute):
    form_field_coerce = float
    form_field_multiple_delimiter = '\n'


class BooleanAttribute(BaseAttribute):
    datatype = 'bool'
    datatype_title = _('Boolean')
    form_field = forms.NullBooleanField

    def validate(self, value, entity=None):
        if not isinstance(value, bool) and not value is None:
            raise ValidationError(_(u'Must be a boolean'))

    def value_decode(self, value):
        return self.to_type(value, bool)

    def value_encode(self, value):
        return value


class DateAttribute(BaseAttribute):
    datatype = 'date'
    datatype_title = _('Date')
    form_field = forms.DateField

    def validate(self, value, entity=None):
        if not isinstance(value, datetime.date):
            raise ValidationError(_(u'Must be a date'))

    def value_decode(self, value):
        return parse_date(value) if isinstance(value, basestring) else None

    def value_encode(self, value):
        return (value.isoformat()
                if isinstance(value, datetime.date) else value)


class DateTimeAttribute(BaseAttribute):
    datatype = 'datetime'
    datatype_title = _('Date and Time')
    form_field = forms.DateTimeField

    def validate(self, value, entity=None):
        if not isinstance(value, datetime.datetime):
            raise ValidationError(_(u'Must be a datetime'))

    def value_decode(self, value):
        return parse_datetime(value) if isinstance(value, basestring) else None

    def value_encode(self, value):
        return (value.isoformat()
                if isinstance(value, datetime.datetime) else value)
