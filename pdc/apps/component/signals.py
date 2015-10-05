#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from django import dispatch


# This signal is sent before a release_component object is updated. The argument contains
# the original value.
releasecomponent_pre_update = dispatch.Signal(providing_args=['request', 'release_component'])

# This signal is sent after a release_component object is updated in the database. This
# might be as a result of update call (in which case the `releasecomponent_pre_update`
# signal was sent before this) or after creating a completely new release (no
# `releasecomponent_pre_update` in this case).
releasecomponent_post_update = dispatch.Signal(providing_args=['request', 'release_component'])

# This signal is sent before validated data is converted into a ReleaseComponent
# instance. Any module that has additional fields in the dict should remove it
# and store it for further processing.
releasecomponent_serializer_extract_data = dispatch.Signal(providing_args=['validated_data'])

# This signal is sent when a new release_component is created.
releasecomponent_serializer_post_create = dispatch.Signal(providing_args=['release_component'])

# This signal is sent after an existing release_component is updated.
releasecomponent_serializer_post_update = dispatch.Signal(providing_args=['release_component'])


# This signal is sent after a release component is cloned. It is a reaction to
# `pdc.apps.release.signals.release_clone` signal. The handler will get access
# to request, primary key of the cloned component and the new instance.
releasecomponent_clone = dispatch.Signal(providing_args=['request',
                                                         'orig_component_pk',
                                                         'new_component'])
