# coding: utf-8
from collections import OrderedDict
from django.db.models.signals import post_init, pre_save, post_save
from .models import Entity, BaseAttributeOptions
from . import attributes


class EavConfig(object):
    """
    The default EevConfig class used if it is not overriden on registration.
    This is where all the default eav attribute names are defined.
    """
    eav_attr = 'eav'
    eav_field = 'eavdata'
    model_cls = None
    entity_cls = None

    def __init__(self, model_cls, entity_cls):
        self.model_cls = model_cls
        self.entity_cls = entity_cls

    def get_attr_model(self):
        return registry.attr_model

    def get_attributes(self, **kwargs):
        """
        By default, all eavkit.models.BaseAttributeOptions object apply to an
        entity, unless you provide a custom EavConfig class overriding this.
        """
        return [i.get_attribute() for i in self.get_attr_model().objects.all()]


class Registry(object):
    attributes = None
    attr_model = None
    entity_cls = None

    def __init__(self):
        self.attributes = OrderedDict()
        self.entity_cls = Entity

    def register_attribute(self, attribute):
        self.attributes[attribute.datatype] = attribute
        self.set_datatype_choices()

    def unregister_attribute(self, attribute):
        self.attributes.pop(attribute.datatype)
        self.set_datatype_choices()

    def register_builtin_attributes(self):
        self.register_attribute(attributes.StringAttribute)
        self.register_attribute(attributes.TextAttribute)
        self.register_attribute(attributes.IntegerAttribute)
        self.register_attribute(attributes.FloatAttribute)
        self.register_attribute(attributes.BooleanAttribute)
        self.register_attribute(attributes.DateAttribute)
        self.register_attribute(attributes.DateTimeAttribute)

    def register_model(self, attr_model, force=False):
        if issubclass(attr_model, BaseAttributeOptions) or force:
            self.attr_model = attr_model
            self.set_datatype_choices()

    def register_entity(self, entity_cls, force=False):
        if issubclass(entity_cls, Entity) or force:
            self.entity_cls = entity_cls

    def register(self, model_cls, config_cls=None, entity_cls=None):
        """
        Registers model_cls with eav.
        You can pass an optional config_cls and entity_cls.
        """
        if hasattr(model_cls, '_eav_config'):
            return

        if config_cls is None:
            config_cls = EavConfig
        setattr(model_cls, '_eav_config',
                config_cls(model_cls, entity_cls or self.entity_cls))

        self.attach_signals(model_cls)

    def unregister(self, model_cls):
        """Unregisters model_cls with eav."""
        if not getattr(model_cls, '_eav_config', None):
            return
        self.detach_signals(model_cls)
        delattr(model_cls, '_eav_config')

    def attach_signals(self, model_cls):
        """Attach all signals for eav"""
        entity_cls = model_cls._eav_config.entity_cls
        post_init.connect(self.attach_eav_attr, sender=model_cls)
        pre_save.connect(entity_cls.pre_save_handler, sender=model_cls)
        post_save.connect(entity_cls.post_save_handler, sender=model_cls)

    def detach_signals(self, model_cls):
        """Detach all signals for eav"""
        entity_cls = model_cls._eav_config.entity_cls
        post_init.disconnect(self.attach_eav_attr, sender=model_cls)
        pre_save.disconnect(entity_cls.pre_save_handler, sender=model_cls)
        post_save.disconnect(entity_cls.post_save_handler, sender=model_cls)

    def attach_eav_attr(self, sender, *args, **kwargs):
        instance = kwargs['instance']
        config = instance.__class__._eav_config
        setattr(instance, config.eav_attr, config.entity_cls(instance))

    def set_datatype_choices(self):
        if self.attr_model and self.attributes:
            self.attr_model._meta.get_field('datatype').choices = (
                self.attr_model.DATATYPE_CHOICES +
                tuple([(k, v.datatype_title,)
                       for k, v in self.attributes.items()])
            )

registry = Registry()
