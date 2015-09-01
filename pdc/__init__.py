#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
import os
import subprocess

VERSION = "v0.1.0"

old_cwd = os.getcwd()
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# NOTE(xchu): use `git describe` when under git repository.
if os.system('git rev-parse 2> /dev/null > /dev/null') == 0:
    pipe = subprocess.Popen("git describe",
                            shell=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    label, err = pipe.communicate()
    # We follow semantic versioning to add annotated tags, so the
    # label here can be:
    #     0.1.0                # release tag,
    # or  0.1.0-s5             # pre-release tag with sprint metadata,
    # or  0.1.0-s5-2-gabcdefg  # devel build with 2 commits ahead the latest tag
    #                            with 'g'it short hash('abcdefg') metadata.
    # (more info: http://git-scm.com/docs/git-describe)
    #
    # But only one dash should be used here, so we need to replace other deshes
    # with dot if they exists.
    version_list = label.strip().split('-', 1)
    if len(version_list) == 1:
        VERSION = version_list[0]
    else:
        VERSION = version_list[0] + '-' + version_list[1].replace('-', '.')

os.chdir(old_cwd)


def get_version():
    """
    Get PDC version info
    """
    return VERSION
