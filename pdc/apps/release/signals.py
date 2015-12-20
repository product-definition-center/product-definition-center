#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from django import dispatch


# This signal is sent before a release object is updated. The argument contains
# the original value.
release_pre_update = dispatch.Signal(providing_args=['request', 'release'])


# This signal is sent after a release object is updated in the database. This
# might be as a result of update call (in which case the `release_pre_update`
# signal was sent before this) or after creating a completely new release (no
# `release_pre_update` in this case).
release_post_update = dispatch.Signal(providing_args=['request', 'release'])

# This signal is sent when a new release is created by cloning. It will be sent
# after the clone is saved. The original_release argument is the Release object
# that was used as the source of cloning.
release_clone = dispatch.Signal(providing_args=['request',
                                                'original_release',
                                                'release'])

# This signal is sent when want to clone components from one release to another.
# The way is to copy all release components, component groups and relationships.
rpc_release_clone_component = dispatch.Signal(providing_args=['request',
                                                              'original_release',
                                                              'release'])

# This signal is sent before validated data is converted into a Release
# instance. Any module that has additional fields in the dict should remove it
# and store it for further processing.
release_serializer_extract_data = dispatch.Signal(providing_args=['validated_data'])

# This signal is sent when a new release is created.
release_serializer_post_create = dispatch.Signal(providing_args=['release'])

# This signal is sent after an existing release is updated.
release_serializer_post_update = dispatch.Signal(providing_args=['release'])
