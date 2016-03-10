%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}

%define srcname pdc

Name:           python-%{srcname}
Version:        0.9.rc
Release:        3%{?dist}
Summary:        Product Definition Center
Group:          Development/Libraries
License:        MIT
URL:            https://github.com/release-engineering/product-definition-center
Source0:        %{name}-%{version}.tar.gz
BuildArch:      noarch
BuildRequires:  python-setuptools
BuildRequires:  python-sphinx
Requires:       Django >= 1.8.1
Requires:       django-rest-framework >= 3.1
Requires:       django-rest-framework < 3.2
Requires:       django-mptt >= 0.7.1
Requires:       kobo >= 0.4.2
Requires:       kobo-django
Requires:       kobo-rpmlib
Requires:       koji
Requires:       patternfly1
Requires:       productmd
Requires:       python-django-filter >= 0.9.2
Requires:       python-ldap
Requires:       python-markdown
Requires:       python-mock
Requires:       python-psycopg2
Requires:       python-django-cors-headers

%description
The Product Definition Center, at its core, is a database that defines every Red Hat products, and their relationships with several important entities.
This package contains server part of Product Definition Center (PDC)

%prep
%setup -q -n %{name}-%{version}

%build
make -C docs/ html

%install
rm -rf %{buildroot}
%{__python} setup.py install -O1 --root=%{buildroot}


mkdir -p %{buildroot}/%{_datadir}/%{srcname}/static
mkdir -p %{buildroot}%{_defaultdocdir}/%{srcname}
cp pdc/settings_local.py.dist %{buildroot}/%{python_sitelib}/%{srcname}
cp -R docs %{buildroot}%{_defaultdocdir}/%{srcname}
cp manage.py %{buildroot}/%{python_sitelib}/%{srcname}


# don't need egg info
for egg_info in $(find %{buildroot}/%{python_sitelib} -type d -name '*.egg-info'); do
  rm -rf $egg_info
done

# Install apache config for the app:
install -m 0644 -D -p conf/pdc-httpd.conf.sample %{buildroot}%{_defaultdocdir}/pdc/pdc.conf.sample

# only remove static dir when it's a uninstallation
# $1 == 0: uninstallation
# $1 == 1: upgrade
%preun
if [ "$1" = 0 ]; then
  rm -rf %{_datadir}/%{srcname}/static
fi


%files
%defattr(-,root,apache,-)
%{_defaultdocdir}/pdc
%{python_sitelib}/%{srcname}
%{python_sitelib}/contrib
%exclude %{python_sitelib}/%{srcname}/conf
%{_datadir}/%{srcname}


%changelog
* Fri Feb 26 2016 Cheng Yu <ycheng@redhat.com> 0.9.rc-3
- Change version and organization name. (ycheng@redhat.com)
- Automatic commit of package [python-pdc] minor release [0.9.rc-2].
  (ycheng@redhat.com)
- Remove deprecated API /rpc/compose/import-images/ (ycheng@redhat.com)
- Remove permissions from inactive user accounts (ycheng@redhat.com)
- Remove deprecated end points under repository app. (ycheng@redhat.com)
- Change links from varianttype-list to releasevarianttype-list.
  (ycheng@redhat.com)
- Update the doc for some API (bliu@redhat.com)
- Update the content-delivery-repos URL (bliu@redhat.com)
- Add 2 image formats and 1 image type. (ycheng@redhat.com)
- Rename resource variant-types to release-variant-types. (ycheng@redhat.com)
- Add more detail error info for compose-tree-locations (bliu@redhat.com)
- Allow import images work when filed 'implant_md5' is null.
  (ycheng@redhat.com)
- Fix the bug when change RPM built_for_release field won't record.
  (ycheng@redhat.com)
- Update the error info for compose-tree-location (bliu@redhat.com)
- Make MultiValueRegexFilter could treat empty string or wrong regexp format
  (ycheng@redhat.com)
- Add error message for compose-tree-locations. (bliu@redhat.com)
- Add optional "built-for-release" field in rpms resource (ycheng@redhat.com)
- This task have been fixed and just remove unavaliable code (bliu@redhat.com)
- Add support for regexp for contact searches by component name
  (ycheng@redhat.com)
- Update the doc for release-component clone (bliu@redhat.com)
- Return error info When srouce release doesn't contain component
  (bliu@redhat.com)
- Provide a response header field name "pdc-warning" (ycheng@redhat.com)
- Raise error when there are wrong inputs or wrong input format.
  (chuzhang@redhat.com)
- Add error info when release component clone with inactive (bliu@redhat.com)
- Add response info for composes/{compose_id}/rpm-mapping/{package}
  (bliu@redhat.com)
- Raise error when missing some inputs (chuzhang@redhat.com)
- Improve output when successfully import files composeinfo.json/rpm-
  manifest.json/image-manifest.json (chuzhang@redhat.com)
- Add response info for composes/{compose_id}/rpm-mapping/{package}
  (bliu@redhat.com)
- Try to improve composes list performance. (ycheng@redhat.com)
- Allow PATCH on build-image-rtt-tests with build_nvr/format (bliu@redhat.com)
- Update error info more clear (bliu@redhat.com)
- Add error info when input error para (bliu@redhat.com)
- Fix cmposes/{compose_id}/rpm-mapping/{package}] return error if 'action' is
  invalid (ycheng@redhat.com)
- Rpc/release/clone-components (bliu@redhat.com)
- Some improvements for stare image test results. (ycheng@redhat.com)
- Rpc/release/clone-components (bliu@redhat.com)
- Handle ValueError in exception_handler (ycheng@redhat.com)
- Fix the bug that build image rtt test resluts should not allow put method.
  (ycheng@redhat.com)
- Move contact releated test to new file accroding to master change.
  (ycheng@redhat.com)
- A slightly more friendly default 404 response. (rbean@redhat.com)
- Add compose image RTT tests APIs. (xchu@redhat.com)
- Clean up spec file to remove client related content. (xchu@redhat.com)
- Add format filter for build-image-rtt-tests and fix a bug.
  (ycheng@redhat.com)
- Provide new resource for storing RTT test results of brew image builds
  (ycheng@redhat.com)
- Make tests pass on DRFv3.3 (xchu@redhat.com)
- Allow single NVR (image_id) have multiple different formats
  (ycheng@redhat.com)
- Change required Django version in range [1.8.1, 1.9) (chuzhang@redhat.com)
- Drop old contact API. (chuzhang@redhat.com)

* Wed Dec 16 2015 Cheng Yu <ycheng@redhat.com> 0.3.rc-2
- Fix the bug that when role count original value is unlimited, no constraint.
  (ycheng@redhat.com)

* Fri Dec 04 2015 Xiangyang Chu <xchu@redhat.com> 0.3.rc-1
- Bump Version to '0.3.rc'. (xchu@redhat.com)
- Remove compose/package api. (xchu@redhat.com)
- Specify Accept instead of Content-Type in curl examples. (rbean@redhat.com)
- Use single string field for user names. (ycheng@redhat.com)
- Add new endpoint API ComposeTree (chuzhang@redhat.com)
- Create script that can create release-components from compose information
  (ycheng@redhat.com)
- Remove pdc_client since pdc-client repo created. (xchu@redhat.com)
* Fri Sep 11 2015 Xiangyang Chu <xychu2008@gmail.com> 0.1.0-1
- new package built with tito

* Thu Aug 27 2015 Xiangyang Chu <xchu@redhat.com> 0.1.0-1
- Use release tagger. (xchu@redhat.com)
- init spec for copr build
