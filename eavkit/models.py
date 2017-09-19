# coding: utf-8
import re
import json
import copy
from collections import OrderedDict
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.conf import settings
from .attributes import StringAttribute


validate_slug = RegexValidator(
    re.compile(r'^[a-z][a-z0-9_]*$'),
    _(u'Must be all lower case, start with a letter,'
      u' and contain only letters, numbers, or underscores.'),
    'invalid'
)


class BaseAttributeOptions(models.Model):
    DATATYPE_CHOICES = (('', '---',),)

    site = models.ForeignKey(
        Site, verbose_name=_(u"site"), default=settings.SITE_ID)

    name = models.CharField(
        _(u"name"), max_length=100,
        help_text=_(u"User-friendly attribute name"))
    slug = models.SlugField(
        _(u"slug"), max_length=50, db_index=True, validators=[validate_slug],
        help_text=_(u"Short unique attribute code"))
    description = models.CharField(
        _(u"description"), max_length=256, blank=True, null=True,
        help_text=_(u"Short description"))

    multiple = models.BooleanField(_(u"multiple"), default=False)
    required = models.BooleanField(_(u"required"), default=False)
    datatype = models.CharField(
        _(u"data type"), max_length=32, choices=DATATYPE_CHOICES)

    code = models.CharField(_(u"code"), max_length=20, blank=True, null=True)
    choices = models.TextField(_(u"choices"), blank=True)

    weight = models.IntegerField(_(u"weight"), default=500)

    created = models.DateTimeField(_(u"created"), auto_now_add=True,)
    modified = models.DateTimeField(_(u"modified"), auto_now=True)

    class Meta:
        verbose_name = _(u'Attribute options')
        verbose_name_plural = _(u'Attributes options')
        unique_together = ('site', 'slug')
        ordering = ('-weight', 'site', 'name', '-id',)
        abstract = True

    def __unicode__(self):
        return u"%s (%s)" % (self.name, self.get_datatype_display())

    def get_attribute(self):
        if not hasattr(self, '_attribute'):
            from .registry import registry
            attr_cls = registry.attributes.get(self.datatype) or StringAttribute
            self._attribute = attr_cls(
                name=self.name, slug=self.slug, required=self.required,
                description=self.description, choices=self.get_choices(),
                multiple=self.multiple, data={'instance': self,})
        return self._attribute

    def clean(self):
        # run options validation, depending on Attribute type
        self.get_attribute().clean_attribute_model_instance(self)

    def get_choices(self):
        # choices, each on new line, value and title separated by equal sign,
        # double equal sign should be used to type equal sign in value or title
        # 1 = one           -> (('1', u'one',),)
        # ==== = two equals -> (('==', u'two equals',),)
        choices = [[k.replace('\x00', '==').strip() for k in i.split('=', 1)]
                   for i in self.choices.replace('==', '\x00').splitlines()
                   if i.strip()]
        choices = [tuple(i if len(i) == 2 else i*2) for i in choices]
        return choices


class Entity(object):
    """
    The Entity class, attributes data container, that will be attached to any
    entity registered with eavkit.
    """
    def __init__(self, instance):
        super(Entity, self).__setattr__('instance', instance)

    def __getattr__(self, name):
        if name.startswith('_'):
            return super(Entity, self).__getattr__(name)
        if not name in self.attributes:
            raise AttributeError(
                _(u"%(obj)s has no EAV attribute named '%(attr)s'")
                % {'obj': self.instance, 'attr': name,})
        return self.storage.get(self.attributes[name].slug, None)

    def __setattr__(self, name, value):
        if name.startswith('_') or not name in self.attributes:
            return super(Entity, self).__setattr__(name, value)
        if not value is None:
            self.attributes[name].validate(value)
        self.storage[name] = value

    def __iter__(self):
        for attribute in self.attributes.values():
            yield (attribute.slug, self.storage.get(attribute.slug, None),)

    @property
    def attributes(self):
        if not hasattr(self, '__attributes__'):
            self.__attributes__ = OrderedDict(
                (i.slug, i,) for i in self.get_all_attributes())
        return self.__attributes__

    @property
    def storage(self):
        if not hasattr(self, '__storage__'):
            data = getattr(self.instance,
                           self.instance._eav_config.eav_field, None)
            self.__storage__ = json.loads(data) if data else {}

            for attribute in self.attributes.values():
                value = self.__storage__.get(attribute.slug, None)
                self.__storage__[attribute.slug] = attribute.value_decode(
                    value) if not value is None else None
        return self.__storage__

    def get_all_attributes(self):
        return self.instance._eav_config.get_attributes(
            instance=self.instance)

    def validate_attributes(self):
        for attribute in self.attributes.values():
            value = self.storage.get(attribute.slug, None)
            if value is None:
                if attribute.required:
                    raise ValidationError(
                        _(u"%(attr)s EAV field cannot be blank")
                        % {'attr': attribute.slug,})
            else:
                try:
                    map(lambda v: v(value), attribute.get_validators())
                except ValidationError as e:
                    raise ValidationError(
                        _(u"%(attr)s EAV field %(err)s")
                        % {'attr': attribute.slug, 'err': e,})

    def save(self):
        data = copy.deepcopy(self.storage)
        for attribute in self.attributes.values():
            value = self.storage.get(attribute.slug, None)
            value = attribute.value_encode(value)
            data[attribute.slug] = value
        jsondata = json.dumps(data)

        eav_field = self.instance._eav_config.eav_field
        self.instance.__setattr__(eav_field, jsondata)
        self.instance.__class__.objects.filter(pk=self.instance.pk).update(
            **{eav_field: jsondata,})

    @staticmethod
    def post_save_handler(sender, *args, **kwargs):
        instance = kwargs['instance']
        entity = getattr(instance, instance._eav_config.eav_attr)
        entity.save()

    @staticmethod
    def pre_save_handler(sender, *args, **kwargs):
        instance = kwargs['instance']
        entity = getattr(instance, instance._eav_config.eav_attr)
        entity.validate_attributes()
