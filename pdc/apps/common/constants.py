#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
'''
Created on Aug 27, 2014

Declare PDC constant string here
'''

# Contact Types
QE_GROUP_CONTACT = 'QE_Group'
QE_LEADER_CONTACT = 'QE_Leader'
QE_ACK_CONTACT = 'QE_ACK'
BUILD_CONTACT = 'Build_Owner'
DEVEL_CONTACT = 'Devel_Owner'

# Arch type
ARCH_SRC = 'src'

# PDC warning field in response header
PDC_WARNING_HEADER_NAME = 'pdc-warning'

# Warning when using put method on optional parameter
PUT_OPTIONAL_PARAM_WARNING = {
    'PUT_OPTIONAL_PARAM_WARNING': 'When using the `PUT` method, if an optional field is not specified' +
                                  ' in the input, it will be erased.',
}
