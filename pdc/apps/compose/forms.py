# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#

import django.forms as forms
from django.db.models import Q

from pdc.apps.release.models import Release


class ComposeSearchForm(forms.Form):
    search      = forms.CharField(required=False)

    def get_query(self, request):
        self.is_valid()
        search = self.cleaned_data["search"]

        query = Q()

        if search:
            query |= Q(compose_id__icontains=search)

        return query


class ComposeRPMSearchForm(forms.Form):
    search = forms.CharField(required=False)

    def get_query(self, request):
        query = Q()
        if not self.is_valid():
            return query
        search = self.cleaned_data["search"]

        if search:
            query |= Q(rpm__name__icontains=search)
            query |= Q(rpm__arch__icontains=search)
            query |= Q(rpm__version__icontains=search)
            query |= Q(rpm__release__icontains=search)

        return query


class ComposeImageSearchForm(forms.Form):
    search = forms.CharField(required=False)

    def get_query(self, request):
        query = Q()
        if not self.is_valid():
            return query
        search = self.cleaned_data["search"]

        if search:
            query |= Q(image__file_name__icontains=search)
            query |= Q(image__image_format__name__icontains=search)
            query |= Q(image__image_type__name__icontains=search)
            query |= Q(image__arch__icontains=search)
            query |= Q(image__implant_md5__icontains=search)
            query |= Q(image__volume_id__icontains=search)
            query |= Q(image__md5__icontains=search)
            query |= Q(image__sha1__icontains=search)
            query |= Q(image__sha256__icontains=search)

        return query


class ComposeRpmMappingSearchForm(forms.Form):
    package     = forms.CharField(required=False)
    release     = forms.ChoiceField()

    def __init__(self, *args, **kwargs):
        super(ComposeRpmMappingSearchForm, self).__init__(*args, **kwargs)
        self.fields["release"].choices = [(i.pk, str(i)) for i in Release.objects.all()]

    def get_query(self, request):
        query = Q()
        if not self.is_valid():
            return query

        package = self.cleaned_data["package"]  # noqa
        release = self.cleaned_data["release"]  # noqa

#        if package:
#            package |= Q(compose_id__icontains=search)

        return query


class ComposeRPMDisableForm(forms.Form):
    variant = forms.CharField(widget=forms.HiddenInput())
    arch = forms.CharField(widget=forms.HiddenInput())
    rpm_name = forms.CharField(widget=forms.HiddenInput())
    rpm_arch = forms.CharField(widget=forms.HiddenInput())
    included = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={"class": "form-control input-small"})
    )
    override = forms.CharField(required=False, widget=forms.HiddenInput())


class OverrideRPMForm(forms.Form):
    variant = forms.CharField(widget=forms.HiddenInput(), required=False)
    arch = forms.CharField(widget=forms.HiddenInput(), required=False)
    rpm_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control input-sm'}),
        required=False
    )
    rpm_arch = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control input-sm'}),
        required=False
    )
    new_variant = forms.IntegerField(required=False,
                                     initial=-1,
                                     widget=forms.HiddenInput())

    def clean(self):
        cleaned_data = super(OverrideRPMForm, self).clean()
        if (cleaned_data['rpm_name'] and not cleaned_data['rpm_arch'] or
                cleaned_data['rpm_arch'] and not cleaned_data['rpm_name']):
            raise forms.ValidationError("Both RPM name and arch must be filled in.")
        if (cleaned_data['new_variant'] >= 0 and
                (cleaned_data.get('variant') or cleaned_data.get('arch'))):
            raise forms.ValidationError("Can not reference both old and new variant.arch.")
        return cleaned_data


class VariantArchForm(forms.Form):
    variant = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control input-sm'})
    )
    arch = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control input-sm'})
    )

    def clean(self):
        cleaned_data = super(VariantArchForm, self).clean()
        if (cleaned_data['variant'] and not cleaned_data['arch'] or
                cleaned_data['arch'] and not cleaned_data['variant']):
            raise forms.ValidationError("Both variant and arch must be filled in.")
        return cleaned_data


class OverrideRPMActionForm(forms.Form):
    action = forms.CharField(widget=forms.HiddenInput())
    # release_id = forms.CharField(widget=forms.HiddenInput())
    variant = forms.CharField(widget=forms.HiddenInput())
    arch = forms.CharField(widget=forms.HiddenInput())
    # srpm_name = forms.CharField(widget=forms.HiddenInput())
    rpm_name = forms.CharField(widget=forms.HiddenInput())
    rpm_arch = forms.CharField(widget=forms.HiddenInput())
    include = forms.BooleanField(required=False, widget=forms.HiddenInput())
    comment = forms.CharField(required=False,
                              widget=forms.TextInput(attrs={'class': 'form-control input-sm'}))
    do_not_delete = forms.BooleanField(required=False,
                                       widget=forms.CheckboxInput(attrs={'class': 'form-control'}))
    warning = forms.CharField(required=False)

    def clean(self):
        cleaned_data = super(OverrideRPMActionForm, self).clean()
        if not cleaned_data.get('do_not_delete', False) and cleaned_data['comment']:
            raise forms.ValidationError('Comment needs do_not_delete checked.')
        return cleaned_data
