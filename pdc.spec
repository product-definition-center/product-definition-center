%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}

%define srcname pdc

Name:           python-%{srcname}
Version:        1.0.0
Release:        2%{?dist}
Summary:        Product Definition Center
Group:          Development/Libraries
License:        MIT
URL:            https://github.com/release-engineering/product-definition-center
Source0:        %{name}-%{version}.tar.gz
BuildArch:      noarch
BuildRequires:  python-setuptools
BuildRequires:  python-sphinx
Requires:       Django >= 1.8.1, Django < 1.9.0
Requires:       django-rest-framework >= 3.1
Requires:       django-rest-framework < 3.2
Requires:       django-mptt >= 0.7.1
Requires:       kobo >= 0.4.2
Requires:       kobo-django
Requires:       kobo-rpmlib
Requires:       koji
Requires:       patternfly1
Requires:       productmd >= 1.1
Requires:       python-django-filter >= 0.9.2
Requires:       python-ldap
Requires:       python-markdown
Requires:       python-mock
Requires:       python-psycopg2
Requires:       python-django-cors-headers
Requires:       python-django-rest-framework-composed-permissions

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
* Tue May 17 2016 Cheng Yu <ycheng@redhat.com> 1.0.0-2
- Pass empty string to productmd instead of None. (chuzhang@redhat.com)

* Wed May 11 2016 Cheng Yu <ycheng@redhat.com> 1.0.0-1
- Change version in code. (ycheng@redhat.com)
- Handle release has no compose in web UI (ycheng@redhat.com)
- Get rpm-mapping when release has no compose. (ycheng@redhat.com)
- Enable query with multi values. (chuzhang@redhat.com)
- Make Release.integrated_with accept null as input. (chuzhang@redhat.com)
- Allow to clone repositories with None product_id (bliu@redhat.com)
- Remove create-plugin.py from server repo (bliu@redhat.com)
- Update the doc in Repo API (bliu@redhat.com)
- Set unique Charfield's default value to None insteadof empty string.
  (chuzhang@redhat.com)
- Disable_eus/aus_repo_checks (bliu@redhat.com)
- Make all update api following rule 'Update missing optional fields are
  erased'. (chuzhang@redhat.com)
- Simplify _bulk_insert_resource func in scripts/create_release_components.py
  (tmlcoch@redhat.com)
- Add doc to note the user when PUT optional parameter. (chuzhang@redhat.com)
- Update tests to work with new productmd (lsedlar@redhat.com)
- Fix the bug about "Manage Overrides" on release without compose
  (bliu@redhat.com)
- Publish two new message topics. (rbean@redhat.com)
- Store relative paths to variant/$arch/$content_category_name dir
  (ycheng@redhat.com)
- Update the view of auth/token api (bliu@redhat.com)
- Return warning when query in boolean field with illegal value.
  (ycheng@redhat.com)
- Add API stability to doc (sochotnicky@redhat.com)
- Correct a documentation's url. (ycheng@redhat.com)
- Create rpc/overridesrpm/clone (bliu@redhat.com)
- Create rpc/overrides-rpm/clone (bliu@redhat.com)
- To create rpc/overrides-rpm/clone API (bliu@redhat.com)
- To create Rpc/Overrides-rpm/clone new API. (bliu@redhat.com)
- Rewrite the get_all_permissions function (bliu@redhat.com)
- Sorte permission list with same api name (bliu@redhat.com)
- Correct the using api doc (bliu@redhat.com)
- Change compose tree location end point url. (ycheng@redhat.com)
- Initial image formats and types from productmd. (ycheng@redhat.com)
- To show Arch names on compose page which get truncated (bliu@redhat.com)
- Check compose rpm mapping parameters strictly and fix bug.
  (ycheng@redhat.com)
- Visible for Arch names on compose page (bliu@redhat.com)
- Compose import images/rpms and full import APIs extra parameter not allowed.
  (ycheng@redhat.com)
- Send signal when product is created or updated. (ycheng@redhat.com)
- Compose-tree-locations be unique over scheme (bliu@redhat.com)
- Update the doc in compose-tree-location (bliu@redhat.com)
- Visible for Arch names on compose page (bliu@redhat.com)
- Remove useless header informations for some APIs (bliu@redhat.com)
- Remove the client test in server repo (bliu@redhat.com)
- Sync Release and BaseProduct models with productmd. (dmach@redhat.com)
- Modify release 'short' and 'version' field validation to use regular
  expressions from productmd. (dmach@redhat.com)
- Remove useless header informations for some APIs (bliu@redhat.com)
- Change corp name to the correct one. (ycheng@redhat.com)
- Avoid double-encoding the fedmsg json payload. (rbean@redhat.com)
- Strip any extra dots from the fedmsg topic. (rbean@redhat.com)
- Fix tests (lsedlar@redhat.com)
- Add subvariant field to images (lsedlar@redhat.com)
- Add set compose tree location function to compose full import
  (ycheng@redhat.com)
- Indicate a compose is deleted in its detail page. (ycheng@redhat.com)
- Remove redundant changelog. (ycheng@redhat.com)
- Fix the full compose import API web page footer error. (ycheng@redhat.com)
- Display deleted compose with special style in web UI. (ycheng@redhat.com)
- Ability to import compose-rpms, compose-images at once (atomicity).
  (ycheng@redhat.com)
- Allow marking composes as deleted (ycheng@redhat.com)
- Modify epochformat to work with both timestamps and datetime.
  (dmach@redhat.com)
- Improve ordering releases, product versions and products. (dmach@redhat.com)
- Remove productmd hacks, deserialize data directly. (dmach@redhat.com)

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
