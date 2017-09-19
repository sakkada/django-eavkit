# coding: utf-8
from django.forms import ModelForm
from django.utils.translation import ugettext_lazy as _


class BaseEntityForm(ModelForm):
    """
    ModelForm for entity with support for EAV attributes.
    Form fields are created on the fly depending on Schema defined for given
    entity instance.
    """

    def __init__(self, data=None, *args, **kwargs):
        super(BaseEntityForm, self).__init__(data, *args, **kwargs)
        self.eav_entity = getattr(self.instance,
                                  self.instance._eav_config.eav_attr)
        self.eav_fields = []
        self.eav_build_dynamic_fields()

    def eav_build_dynamic_fields(self):
        for attribute in self.eav_entity.get_all_attributes():
            value = getattr(self.eav_entity, attribute.slug)
            self.fields[attribute.slug] = attribute.get_form_field(value=value)
            self.eav_fields.append(attribute.slug)

    def save(self, commit=True):
        if self.errors:
            raise ValueError(_(u"The %s could not be saved because the data"
                               u" didn't validate.") %
                             self.instance._meta.object_name)

        # create entity instance, don't save yet
        instance = super(BaseEntityForm, self).save(commit=False)

        # assign attributes
        for attribute in self.eav_entity.get_all_attributes():
            value = self.cleaned_data.get(attribute.slug)
            setattr(self.eav_entity, attribute.slug, value)

        # save entity and its attributes
        if commit:
            instance.save()

        return instance
