.. _versioning:


PDC Versioning
==============

PDC versioning is based on `Semantic Versioning <http://semver.org/spec/v2.0.0.html>`_.

And it's also RPM compatible.

Given a version number MAJOR.MINOR.PATCH, increment the:

#. MAJOR version when you make incompatible API changes,
#. MINOR version when you add functionality in a backwards-compatible manner, and
#. PATCH version when you make backwards-compatible bug fixes.

Additional labels for pre-release and build metadata are available as extensions to the MAJOR.MINOR.PATCH format.

#. A pre-release version MAY be denoted by appending a hyphen and an identifier immediately following the patch version.

   Identifier MUST comprise only ASCII alphanumerics [0-9A-Za-z].
   Identifier MUST NOT be empty.
   Numeric identifier MUST NOT include leading zeroes.
   Pre-release versions have a lower precedence than the associated normal version.
   A pre-release version indicates that the version is unstable and might not satisfy the intended compatibility requirements as denoted by its associated normal version.
   Examples: 1.0.0-alpha, 1.0.0-sprint5, 1.0.0-rc4.

#. Build metadata MAY be denoted by appending a hyphen and a series of dot separated identifiers immediately following the patch or a dot and a series of dot separated identifiers immediately following the pre-release version.

   Identifiers MUST comprise only ASCII alphanumerics [0-9A-Za-z].
   Identifiers MUST NOT be empty.
   Build metadata SHOULD be ignored when determining version precedence.
   Thus two versions that differ only in the build metadata, have the same precedence.
   Examples: 1.0.0-12.g1234abc, 1.0.0-s5.4.g1234abc.


Release Practise
----------------

In practise, we use `git tag` to mark our releases including normal version releases and sprints based pre-releases.

For the git branching, we currently use `master` and `release` two branches, the former is our main branch and we use the later as a stage to hold all the historical releases and the current release candidates.

The reason is, even during the release period, our development keeps moving forwards, commits that need to ship out and commits that belongs to under developing features may mix together out of order.

The `release` branch gives us capabilities to parallel commits that specific to the current release with the commits should go into `master` branch. The Golden Rule here is to narrow down our release phase as shorter as possible. In order to be more agile, let us limit commits that should go into `release` branch to these must-have, non-feature commits, like bump version commit, build metadata(RPM spec file in our case), deploy related, etc. If we do have a must-have feature, I suggest we complete in the `master` branch before we planned to make a release.

When release is done, the `release` branch should be merged back to `master`.

#. At the time we're planning to have another release, we just need to prepare our `release` branch by `merge` forward to the commit that we planned to release with.

   ::

    # switch to release branch
    $ git checkout release

    # merge the code from master
    $ git merge <commit hash>

    # bump version to our target release
    $ vim pdc.spec pdc/__init__.py
    $ git commit && git push

#. by the end of our release stage, we will make our release point by adding tag on the `release` branch, and merge it back to `master`:

   ::

    # switch to release branch
    $ git checkout release

    # and tag on it, for example: 1.0.0
    $ git tag -a <major>.<minor>.<patch>

    # then push it to remote
    $ git push --tags

    # cherry-pick commits from release branch to master
    $ git checkout master
    $ git cherry-pick <commit> ...
    $ git push

#. during daily development and testing, we can produce raw-releases with git hash as build metadata, and the git related information is transformed from `git describe` and made to be RPM compatible.

   Example: 1.0.0-s5.4.g1234abc.

For RPM packaging&distribution, we only need to give and increment `release` for formal version, as for pre-releases and raw-releases, we will take the part after the hyphen as `release`.
