# coding: utf-8
import copy
from django.contrib import admin
from django.contrib.admin.templatetags.admin_list import _boolean_icon
from django.contrib.admin.options import ModelAdmin, InlineModelAdmin
from django.contrib.admin.helpers import (InlineAdminFormSet, InlineAdminForm,
                                          AdminForm)
from django.utils.translation import ugettext_lazy as _
from django import forms
from .forms import BaseEntityForm


eavattrs_js = ('eavkit/js/eavattrs_fieldset.js',)


# EAV Admin Base classes
# ----------------------
class BaseEntityAdmin(admin.ModelAdmin):
    eav_fieldset_template = \
    eav_inline_fieldset_template = (
        _('Attributes'),
        {'classes': ('eavattrs', 'collapse',), 'fields': None,},
    )  # if set to None, mix all fields in first fieldset

    def get_eav_fieldsets(self, form, fieldsets, templates=None):
        template = (['eav_%s_fieldset_template' % i for i in templates]
                     if templates else ['eav_fieldset_template'])
        template = next(getattr(self, i) for i in template if hasattr(self, i))

        if (isinstance(form, BaseEntityForm) and form.eav_fields):
            fieldsets = copy.deepcopy(fieldsets)
            if template is None:
                fieldsets[0][1]['fields'] += form.eav_fields
            else:
                fieldsets.append(copy.deepcopy(template))
                fieldsets[-1][1]['fields'] = form.eav_fields
        return fieldsets

    def render_change_form(self, request, context, add=False, change=False,
                           form_url='', obj=None):
        # reset fieldsets in adminform
        adminform = context['adminform']
        adminform.fieldsets = self.get_eav_fieldsets(adminform.form,
                                                     adminform.fieldsets)

        return super(BaseEntityAdmin, self).render_change_form(
            request, context, add, change, form_url, obj)

    def get_inline_formsets(self, request, formsets, inline_instances,
                            obj=None):
        # update notes: all lines are original except fixed lines - "fl"
        inline_admin_formsets = []
        for inline, formset in zip(inline_instances, formsets):
            fieldsets = list(inline.get_fieldsets(request, obj))
            readonly = list(inline.get_readonly_fields(request, obj))
            prepopulated = dict(inline.get_prepopulated_fields(request, obj))
            inline_admin_formset = EAVMinixInlineAdminFormSet( #  fl
                inline, formset, fieldsets, prepopulated, readonly,
                model_admin=self,
            )
            inline_admin_formsets.append(inline_admin_formset)
        return inline_admin_formsets


class EAVMinixInlineAdminFormSet(InlineAdminFormSet):
    def __iter__(self):
        # allow to customize fieldsets attribute in each form directly
        for inlineadminform in super(EAVMinixInlineAdminFormSet,
                                     self).__iter__():
            modelname = inlineadminform.model_admin.model._meta.model_name
            templates = ('%s_inline' % modelname, 'inline')
            inlineadminform.fieldsets = self.model_admin.get_eav_fieldsets(
                inlineadminform.form, inlineadminform.fieldsets, templates)
            yield inlineadminform


# EAV models Admin classes
# ------------------------
class AttributeOptionsAdmin(admin.ModelAdmin):
    list_display = ('name', 'id', 'weight', 'slug', 'datatype',
                    'code', 'description', 'site',
                    'required', 'has_choices', 'multiple',)
    list_filter = ('site',)
    prepopulated_fields = {'slug': ('name',)}

    def has_choices(self, obj):
        return _boolean_icon(bool(obj.choices.strip()))
    has_choices.allow_tags = True
    has_choices.short_description = _('Choices')
