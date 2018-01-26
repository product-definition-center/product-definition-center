%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}

%define srcname pdc

Name:           python-%{srcname}
Version:        1.9.0
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
Requires:       django-rest-framework >= 3.2
Requires:       django-rest-framework < 3.3
Requires:       django-mptt >= 0.7.1
Requires:       kobo >= 0.4.2
Requires:       kobo-django
Requires:       patternfly1 == 1.3.0
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
* Wed Nov 15 2017 Chuang Cao <chcao@redhat.com> 1.9.0-2
- Fix checking arch for multi-destinations API (lholecek@redhat.com)

* Fri Nov 10 2017 Chuang Cao <chcao@redhat.com> 1.9.0-1
- Add release-files endpoint (chcao@redhat.com)
- Allow filter multi-destinations by repo names (lholecek@redhat.com)
- Fix filtering by subscribers for mutli-destinations (lholecek@redhat.com)
- Use numerical ID to refer to variant-cpes (lholecek@redhat.com)
- Fix filter type of IDs in docs (lholecek@redhat.com)
- Ignore files created by setuptools (lholecek@redhat.com)
- Support OneToOneRel in RelatedNestedOrderingFilter (chuzhang@redhat.com)
- Fix reporting some validation errors (lholecek@redhat.com)
- Remove "trailing slash" hint from errors (lholecek@redhat.com)
- Fix partial update of variant-cpes (lholecek@redhat.com)
- Fix flake8 warnings (lholecek@redhat.com)
- Restrict djangorestframework's version (chcao@redhat.com)
- Fix the URL format in the unreleasedvariants documentation
  (matthew.prahl@outlook.com)
- Remove unused 'lookup_regex' variable (matthew.prahl@outlook.com)
- Add a delete test for the unreleasedvariants API (matthew.prahl@outlook.com)
- Fix the PATCH API in unreleasedvariants (matthew.prahl@outlook.com)
- Filter multi-destinations by repo release_id (lholecek@redhat.com)
- Add multi-destinations (multi-product) endpoint (lholecek@redhat.com)

* Tue Oct 17 2017 Lukas Holecek <lholecek@redhat.com> 1.8.0-1
- Add push-targets endpoint and allowed_push_targets fields
- Add allowed_debuginfos for release (chcao@redhat.com)
- Add allow_buildroot_push to release API (chuzhang@redhat.com)
- Add signing key in release api (chcao@redhat.com)
- Add cpes endpoint (lholecek@redhat.com)
- Add variant-cpes endpoint (lholecek@redhat.com)
- Add descending ordering documentation on API pages (lholecek@redhat.com)
- Add API documentation links (lholecek@redhat.com)
- Make ComponentBranch filters case-sensitive (matt_prahl@live.com)
- Move common settings in one file (chuzhang@redhat.com)
- Always allow to select fields to display (lholecek@redhat.com)
- Allow to use ordering names from serialized JSON (lholecek@redhat.com)
- Fix not-found error string (lholecek@redhat.com)
- Fix passing field errors to client (lholecek@redhat.com)
- Use fuzzy filter for resources (lholecek@redhat.com)
- Omit changing response for DEBUG mode (lholecek@redhat.com)
- Simplify enabling debug toolbar in settings (lholecek@redhat.com)
- doc: fix "then" spelling (kdreyer@redhat.com)

* Tue Aug 15 2017 Chuang Cao <chcao@redhat.com> 1.7.0-1
- Revert "Automatic commit of package [python-pdc] minor release [1.7.0-1]."
  (chcao@redhat.com)
- Automatic commit of package [python-pdc] minor release [1.7.0-1].
  (chcao@redhat.com)
- Fix generating graphs for apps with a label (lholecek@redhat.com)
- Add tests for ordering (hluk@email.cz)
- Fix passing a serialization error to client (lholecek@redhat.com)
- Modify the comment of disable api permission (chcao@redhat.com)
- Remove unneeded django-jsonfield dependency (lholecek@redhat.com)
- Add python-django-jsonfield as a dependency (lholecek@redhat.com)
- Remove duplicate string-to-bool conversion function (lholecek@redhat.com)
- Flake8 fixes (matt_prahl@live.com)
- Update doc strings. (rbean@redhat.com)
- Remove unneeded parentheses. (rbean@redhat.com)
- Remove unused test_tree.json (rbean@redhat.com)
- Remove all references to "tree" which we never ended up using.
  (rbean@redhat.com)
- Move the folder from tree/ to module/. (rbean@redhat.com)
- Allow filtering modules by RPM's srpm_commit_branch. (qwan@redhat.com)
- Add missing database migration script for srpm_commit_hash and
  srpm_commit_branch. (jkaluza@redhat.com)
- Allow storing RPMs used in module build. (jkaluza@redhat.com)
- Add filters for build_deps and runtime_deps. (jkaluza@redhat.com)
- Make flake8 happy. (rbean@redhat.com)
- Add an active boolean field and use variant_uid for the lookup_field.
  (rbean@redhat.com)
- Fix app loading in django 1.9 like in #419. (rbean@redhat.com)
- Get the repository test suite working again. (rbean@redhat.com)
- Get the release app test suite working again. (rbean@redhat.com)
- Also require django-jsonfield for devel and tests. (rbean@redhat.com)
- Add 'modulemd' field to unreleasedvariants (jkaluza@redhat.com)
- New style deps for stream-based modulemd 1.0. (rbean@redhat.com)
- (Un)Serialize dependencies as simple strings. (nils@redhat.com)
- fix RelatedManager not iterable by iterating over .all() (lkocman@redhat.com)
- Add exports for UnreleasedVariant *_deps (lkocman@redhat.com)
- add UnreleasedVariant *_deps to filters (lkocman@redhat.com)
- Don't require runtime_deps/build_deps in the API. (nils@redhat.com)
- implement querying of variant runtime/build deps (nils@redhat.com)
- Add comment to variant_version/_release API docs. (nils@redhat.com)
- Don't require variant_version/_release in the API. (nils@redhat.com)
- Add variant_version/_release to release.Variant. (nils@redhat.com)
- Add comment to variant_version/_release. (nils@redhat.com)
- add missing fields to test API calls (nils@redhat.com)
- API end points are plural, not singular (nils@redhat.com)
- sync up filters with changes in the models (nils@redhat.com)
- Add lookup_field etc. to Tree/UnreleasedVariant. (nils@redhat.com)
- fix URLs in API docs (nils@redhat.com)
- add migrations for Tree and UnreleasedVariant (nils@redhat.com)
- rename TreeVariant* to UnreleasedVariant* (nils@redhat.com)
- require django-jsonfield (nils@redhat.com)
- move JSON test data to own file (nils@redhat.com)
- Add initial version of tree app into pdc (lkocman@redhat.com)
- Add release variant type 'module' (nils@redhat.com)
- Add nested ordering filter (chcao@redhat.com)
- Add the component-branches, component-sla-types, component-branch-slas APIs
  (matt_prahl@live.com)
- Add .idea to .gitignore (matt_prahl@live.com)
- Allow to add/update/remove component relationship types (lholecek@redhat.com)
- Fix mapping volume in example docker command (lholecek@redhat.com)
- Fix requirements for ipdb (lholecek@redhat.com)
- Fix installing kobo from requirements (lholecek@redhat.com)
- Fix accidentally uncommented line in default settings (lholecek@redhat.com)
- Default view of composes should be reversed in order (bliu@redhat.com)
- Handle new page_not_found argument in django-1.9. (rbean@redhat.com)
- unbrand (nils@redhat.com)
- Allow using mod_auth_oidc for remote user auth. (rbean@redhat.com)

* Thu Dec 15 2016 bliu <bliu@redhat.com> 1.2.0-1
- WebUI shows the groups and superusers (bliu@redhat.com)
- Remove inactive user and without group mapping to resource permission
  (bliu@redhat.com)
- Revert "To fix the bug when testing PDC-1757" (bliu@redhat.com)
- To fix the bug when testing PDC-1757 (bliu@redhat.com)
- To verify the 'read' permission for all members (bliu@redhat.com)
- To list all API permissions (bliu@redhat.com)
- Add a test specifically for the new extended unique_together setting.
  (rbean@redhat.com)
- Give a default value to ReleaseComponent.type in the Serializer.
  (rbean@redhat.com)
- Add migration for 80397f1 (rbean@redhat.com)
- Make release components be unique by name/release/type. (rbean@redhat.com)
- Rename the colunm name for release, product version and product
  (bliu@redhat.com)
- Fix apps loading in Django 1.9. (dmach@redhat.com)
- Use slug in release / product version / product URLs. (dmach@redhat.com)
- Display all/active/inactive (bliu@redhat.com)
- Display all/active/inactive and filter the datatable (bliu@redhat.com)
- Change contact APIs' response max-age to 0 (ycheng@redhat.com)
- Display all/active/inactive (bliu@redhat.com)
- Update the docs and add the ordering fields (bliu@redhat.com)
- UI for displaying resource permission (bliu@redhat.com)
- Update pdc.spec for using patternfly1 1.3.0 (bliu@redhat.com)
- Change group-resource-permissions API prompt. (ycheng@redhat.com)
- For group-resource-permissions API, add prompt when use illegal parameter.
  (ycheng@redhat.com)

* Mon Aug 08 2016 Cheng Yu <ycheng@redhat.com> 1.1.0-1
- Make group resource permission work correctly in PATCH method
  (ycheng@redhat.com)
- Change version in code. (chuzhang@redhat.com)
- Update the error info and looks friendly. (bliu@redhat.com)
- Update the valid fields for ordering (bliu@redhat.com)
- Support multiple dict values and empty input for /composes/{compose_id}/rpm-
  mapping/ (chuzhang@redhat.com)
- Unnest group resource permissions create/update/response data.
  (ycheng@redhat.com)
- Make page always locate at page header part. (chuzhang@redhat.com)
- Allowe - and , character together to ordering (bliu@redhat.com)
- Verify the ordering key and update the Release and Compose view
  (bliu@redhat.com)
- Take keys into acount for ordering of all APIs (bliu@redhat.com)
- Change the wrong doc description. (chuzhang@redhat.com)
- Change doc description for compose/compose-images/compose-rpms
  (chuzhang@redhat.com)
- Support regexp search in rpm name. (ycheng@redhat.com)
- Add more details to compose-images API docs. (chuzhang@redhat.com)
- Doc change for compose api to mention how compose get created
  (chuzhang@redhat.com)
- Add page switch to the bottom (chuzhang@redhat.com)
- Fix bugs in cache control and add test cases. (ycheng@redhat.com)
- Implement more accurate last-modified header in some resources of PDC
  (ycheng@redhat.com)
- Specify Django version less than 1.9 in spec file. (chuzhang@redhat.com)
- Add cache control headers to PDC HTTP response (ycheng@redhat.com)
- Fix bugs when inputing wrong format which will return server error
  (chuzhang@redhat.com)
- Fix sync.sh problem in upstream version part. (ycheng@redhat.com)
- Add two new rules to API stability (sochotnicky@redhat.com)
- Group rpm query parameters in and operation. (chuzhang@redhat.com)
- Add unique to Compose PathType's name field. (chuzhang@redhat.com)
- Fix test failed after merge master to release branch. (ycheng@redhat.com)
- Change "ComposeTreeRTTTestVewSet" to "ComposeTreeRTTTestViewSet"
  (bliu@redhat.com)
- Create new API of compose-tree-rtt-tests (bliu@redhat.com)
- Update documentation for compose rpm mapping's bulk update method and fix
  tests. (ycheng@redhat.com)
- Put permission control on more resources and show correct permissions.
  (ycheng@redhat.com)
- Add python-django-rest-framework-composed-permissions as a dependency.
  (ycheng@redhat.com)
- Fix a bug for api auth/resource-permissions retrieve method.
  (ycheng@redhat.com)
- Change the way to generate resource permissions automatically.
  (ycheng@redhat.com)
- Fix a url mistake in mail content. (ycheng@redhat.com)
- Create UI to display resource permissions in auth profile.
  (chuzhang@redhat.com)
- Announce big changes in PDC database (ycheng@redhat.com)
- Document how to configure when behind a reverse proxy (bliu@redhat.com)
- Fix a bug and add a flag for resource permissions. (ycheng@redhat.com)
- Update the release-groups API (bliu@redhat.com)
- Implement resource based permissions control. (ycheng@redhat.com)
- instruct curl to follow HTTP redirect (karsten@t540.str.redhat.com)
- Create release-group API (bliu@redhat.com)
- Add 'subvariant' as a query parameter in images endpoint. (ycheng@redhat.com)

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
