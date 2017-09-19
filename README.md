# A django-eavkit project

Applications, that allows to define attributes and respective values on model
instances (EAV), manage attributes in Admin interface or directly in code and
store it in JSON (by default) format directly in instance.

----

# Requirements

* Python (2.7, 3.3, 3.4, 3.5, 3.6)
* Django (1.8, 1.9, 1.10, 1.11)

# Installation

Install using `pip`:

    pip install django-eavkit

Add `'eavkit'` to your `INSTALLED_APPS` setting:

    INSTALLED_APPS = (
        ...
        'eavkit',
    )

# Example

Starting up a new project...

    pip install django
    pip install django-eavkit
    django-admin.py startproject example .
    ./manage.py migrate
    ./manage.py createsuperuser

Adding `eavkit` in `settings.py` module:

```python
INSTALLED_APPS = (
    ...  # Default installed apps here
    'eavkit',
)
```

Adding AttributeOptions model and registering all required classes
in `main/models.py` (`main` app just for example):

```python
from django.db import models
from eavkit.registry import EavConfig, registry
from eavkit.models import BaseAttributeOptions


class Parent(models.Model):
    name = models.CharField(max_length=256)


class Child(models.Model):
    parent = models.ForeignKey(Parent, null=True, blank=True)
    name = models.CharField(max_length=200)

    # the eav data in json format strorage
    eavdata = models.CharField(max_length=32768, blank=True, editable=False)


# eavkit
# ------
# defining attribute options concrete model
class AttributeOptions(BaseAttributeOptions):
    pass


# defining config class for Child model
class ChildEavConfig(EavConfig):
    def get_attributes(self, instance=None, **kwargs):
        return [i.get_attribute() for i in self.get_attr_model().objects.all()]


registry.register_model(AttributeOptions)   # register attr options model
registry.register_builtin_attributes()      # register all builtin attrs
registry.register(Child, ChildEavConfig)    # register model with with config
```

Adding `AttributeOptions`, `Parent` and `Child` to Django administration
panel (`main/admin.py`):


```python
from django.contrib import admin
from django import forms
from eavkit.admin import BaseEntityAdmin, AttributeAdmin, eavattrs_js
from eavkit.forms import BaseEntityForm
from .models import AttributeOptions, Parent, Child


# admin forms
class ChildEAVForm(BaseEntityForm, forms.ModelForm):
    class Meta:
        model = Child
        fields = '__all__'


# model admins
class ChildStackedInline(admin.StackedInline):
    model = Child
    form = ChildEAVForm
    extra = 0


class ParentAdmin(BaseEntityAdmin, admin.ModelAdmin):
    list_display = ('name', 'id',)
    inlines = (ChildStackedInline,)
    eav_inline_fieldset_template = None  # adding fields to first fieldsets


class ChildAdmin(BaseEntityAdmin, admin.ModelAdmin):
    fieldsets = [(None, {'fields': ['parent', 'name',]})]
    list_display = ('name', 'id',)
    form = ChildEAVForm
    eav_fieldset_template = None  # adding fields to first fieldsets

    class Media:
       js = eavattrs_js  # hiding all optional attrs (optional)


admin.site.register(Parent, ParentAdmin)
admin.site.register(Child, ChildAdmin)
admin.site.register(AttributeOptions, AttributeOptionsAdmin)  # eavkit admin
```

If `eavattrs_js` added to any admin's Media, run:

    python manage.py collectstatic

Run development server:

    python manage.py runserver

And go to the Admin page `127.0.0.1:8000/admin/`.

----
Source code at [bitbucket.org][bitbucket] and [github.com][github].

[github]: https://github.com/sakkada/django-eavkit
[bitbucket]: https://bitbucket.org/sakkada/django-eavkit
