.. _release:


Release
=======

Versioning
----------

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


Release Instruction
-------------------

In practice, we use `tito` to add git tag and do release including tag based releases and current HEAD based test releases.

A short instructions will be as simple as:

#. Tag: tito tag
#. Test Build: tito build --rpm --offline
#. Push: git push origin && git push origin $TAG
#. Release: tito release copr-pdc/copr-pdc-test

For each step, a more detailed version will be:

Tag
```

Every time we are ready to have another release, we should add one git tag, with `tito`, we just need to::

    $ tito tag

It will:

- bump version or release, based on which `tagger`we're using, see `.tito/tito.props`;
- help us create a annotated git tag based on our version;
- update the spec file accordingly, generate changelog even.

For more options about `tito tag`, run `tito tag --help`.

Test Build
``````````

After we have our release tag, we should do some build tests including source tarball checking, and rpm building testing.

   ::

    # generate source tarball
    $ tito build --tgz --offline

    # local rpm build
    $ tito build --rpm --offline

If everything goes well, you could go to next step and push your commit and tag to remote, otherwise you need to untag::

    $ tito tag -u

.. NOTE:: During developing, we could also generate test build at any time we want, it will based on current `HEAD` instead of latest tag.

  ::

    # generate test builds
    $ tito build --test --tgz/srpm/rpm

Push
````

When you're happen with your builds, it's time to push commit and tag to remote.

::

    $ git push origin && git push origin <your_tag>

Release
```````

Thanks to `fedorapeople.org <https://fedorapeople.org/>`_ and `Fedora Copr <https://copr.fedoraproject.org/>`_, we could
use `tito` to release `PDC` as a `yum` or `dnf` repo.
So that user could install `PDC` packages after enable the repo. [#]_

.. NOTE:: Before doing any releases, you should make sure that you have account on both sites and also make sure that you could
  access to your fedorapeople space [#]_ and have enough permissions [#]_ to build `PDC` in `Copr`.

  We need you to create a directory called `pdc_srpms/` under your fedorapeople space `public_html/` to hold all the uploaed
  srpms.

  `copr-cli` will be used, so please `sudo yum/dnf install copr-cli` and configure it. [#]_

Currently we have two projects in `Copr`, `pdc` for all tag based releases and `pdc-test` for test builds. We have two
release targets in `tito`, `copr-pdc` is for `pdc` in `Copr` and `copr-pdc-test` is for `pdc-test`, respectively.

After all setup, release with `tito`::

    $ tito release copr-pdc
    # or
    $ tito release copr-pdc-test

Go and grab a cup of tea or coffee, after a minute or two the release build result will come out then.

.. [#] https://fedorahosted.org/copr/wiki/HowToEnableRepo
.. [#] http://fedoraproject.org/wiki/Infrastructure/fedorapeople.org#Accessing_Your_fedorapeople.org_Space
.. [#] https://fedorahosted.org/copr/wiki/UserDocs#CanIgiveaccesstomyrepotomyteammate
.. [#] https://copr.fedoraproject.org/api/
