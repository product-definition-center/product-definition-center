#
# Copyright (c) 2017 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from django import dispatch


# This signal is sent before a release_schedule object is updated. The argument contains
# the original value.
releaseschedule_pre_update = dispatch.Signal(providing_args=['request', 'release_schedule'])

# This signal is sent after a release_schedule object is updated in the database. This
# might be as a result of update call (in which case the `releaseschedule_pre_update`
# signal was sent before this) or after creating a completely new release (no
# `releaseschedule_pre_update` in this case).
releaseschedule_post_update = dispatch.Signal(providing_args=['request', 'release_schedule'])

# This signal is sent before validated data is converted into a ReleaseSchedule
# instance. Any module that has additional fields in the dict should remove it
# and store it for further processing.
releaseschedule_serializer_extract_data = dispatch.Signal(providing_args=['validated_data'])

# This signal is sent when a new release_schedule is created.
releaseschedule_serializer_post_create = dispatch.Signal(providing_args=['release_schedule'])

# This signal is sent after an existing release_schedule is updated.
releaseschedule_serializer_post_update = dispatch.Signal(providing_args=['release_schedule'])
