# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from rest_framework import serializers

from pdc.apps.release.models import Release
from pdc.apps.componentbranch.models import SLA
from pdc.apps.common.fields import ChoiceSlugField
from contrib.drf_introspection.serializers import StrictSerializerMixin
from .models import ReleaseSchedule


class ReleaseScheduleSerializer(StrictSerializerMixin,
                                serializers.HyperlinkedModelSerializer):
    """
    ReleaseSchedule Serializer
    """

    release = serializers.SlugRelatedField(slug_field='release_id', read_only=False, queryset=Release.objects.all())
    sla = ChoiceSlugField(slug_field='name', queryset=SLA.objects.all())
    date = serializers.DateField()
    active = serializers.BooleanField(read_only=True)
    release_url = serializers.HyperlinkedRelatedField(
        source="release",
        read_only=True,
        view_name='release-detail',
        lookup_field='release_id',
    )
    sla_url = serializers.HyperlinkedRelatedField(
        source="sla",
        read_only=True,
        view_name='sla-detail',
    )

    class Meta:
        model = ReleaseSchedule
        fields = ('id', 'release', 'sla', 'date', 'active', 'release_url', 'sla_url')
