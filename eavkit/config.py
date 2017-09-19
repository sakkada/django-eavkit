from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class EAVConfig(AppConfig):
    label = u'eavkit'
    name = u'eavkit'
    verbose_name = _(u'EAV Kit')

    def ready(self):
        pass
