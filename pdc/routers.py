#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#

from pdc.apps.auth import views as pdc_auth_views
from pdc.apps.changeset import views as changeset_views
from pdc.apps.component import views as component_views
from pdc.apps.contact import views as contact_views
from pdc.apps.release import views as release_views
from pdc.apps.compose import views as compose_views
from pdc.apps.repository import views as repo_views
from pdc.apps.common import views as common_views
from pdc.apps.package import views as rpm_views
from pdc.apps.utils import SortedRouter


router = SortedRouter.PDCRouter()

# register api token auth view
router.register(r'auth/token', pdc_auth_views.TokenViewSet, base_name='token')
router.register(r'auth/groups', pdc_auth_views.GroupViewSet)
router.register(r'auth/permissions', pdc_auth_views.PermissionViewSet)
router.register(r'auth/current-user',
                pdc_auth_views.CurrentUserViewSet,
                base_name='currentuser')

# register changeset view sets
router.register(r'changesets', changeset_views.ChangesetViewSet)

# register release view sets
router.register(r'products', release_views.ProductViewSet)
router.register(r'product-versions', release_views.ProductVersionViewSet)
router.register(r'releases', release_views.ReleaseViewSet)
router.register(r'base-products', release_views.BaseProductViewSet)
router.register(r'release-types', release_views.ReleaseTypeViewSet, base_name='releasetype')

# register contact view sets
router.register(r'persons', contact_views.PersonViewSet)
router.register(r'maillists', contact_views.MaillistViewSet)
router.register(r'contact-roles', contact_views.ContactRoleViewSet)
router.register(r'role-contacts', contact_views.RoleContactViewSet)

# register component view sets
router.register(r'labels', common_views.LabelViewSet, base_name='label')

router.register(r'global-components',
                component_views.GlobalComponentViewSet,
                base_name='globalcomponent')
router.register(r'global-components/(?P<instance_pk>[^/.]+)/contacts',
                component_views.GlobalComponentContactViewSet,
                base_name='globalcomponentcontact')
router.register(r'global-components/(?P<instance_pk>[^/.]+)/labels',
                component_views.GlobalComponentLabelViewSet,
                base_name='globalcomponentlabel')
router.register(r'release-components',
                component_views.ReleaseComponentViewSet,
                base_name='releasecomponent')
router.register(r'release-components/(?P<instance_pk>[^/.]+)/contacts',
                component_views.ReleaseComponentContactViewSet,
                base_name='releasecomponentcontact')
router.register(r'bugzilla-components',
                component_views.BugzillaComponentViewSet,
                base_name='bugzillacomponent')
router.register(r'component-groups', component_views.GroupViewSet, base_name='componentgroup')
router.register(r'component-group-types', component_views.GroupTypeViewSet, base_name='componentgrouptype')
router.register(r'component-relationship-types', component_views.ReleaseComponentRelationshipTypeViewSet,
                base_name='componentrelationshiptype')
router.register(r'release-component-relationships', component_views.ReleaseComponentRelationshipViewSet,
                base_name='rcrelationship')
router.register(r'release-component-types', component_views.ReleaseComponentTypeViewSet,
                base_name='releasecomponenttype')

# register compose view sets
router.register(r'composes', compose_views.ComposeViewSet)
router.register(r'composes/(?P<compose_id>[^/]+)/rpm-mapping',
                compose_views.ComposeRPMMappingView,
                base_name='composerpmmapping')
router.register(r'compose-rpms', compose_views.ComposeRPMView)
router.register(r'compose-images', compose_views.ComposeImageView)

router.register(r'rpc/release/import-from-composeinfo',
                release_views.ReleaseImportView,
                base_name='releaseimportcomposeinfo')
router.register(r'rpc/compose/import-images',
                compose_views.ComposeImportImagesView,
                base_name='composeimportimages')

router.register(r'repos', repo_views.RepoViewSet)
router.register(r'repo-families', repo_views.RepoFamilyViewSet,
                base_name='repofamily')
router.register(r'rpc/repos/clone',
                repo_views.RepoCloneViewSet,
                base_name='repoclone')

# This must be specified after deprecated repos so that automatic link
# generation picks this version.
router.register(r'content-delivery-repos', repo_views.RepoViewSet)
router.register(r'content-delivery-repo-families', repo_views.RepoFamilyViewSet,
                base_name='contentdeliveryrepofamily')
router.register(r'rpc/content-delivery-repos/clone',
                repo_views.RepoCloneViewSet,
                base_name='cdreposclone')

router.register('overrides/rpm',
                compose_views.ReleaseOverridesRPMViewSet,
                base_name='overridesrpm')

router.register(r'rpc/release/clone',
                release_views.ReleaseCloneViewSet,
                base_name='releaseclone')
router.register(r'rpc/where-to-file-bugs', compose_views.FilterBugzillaProductsAndComponents,
                base_name='bugzilla')

router.register('rpc/find-compose-by-release-rpm/(?P<release_id>[^/]+)/(?P<rpm_name>[^/]+)',
                compose_views.FindComposeByReleaseRPMViewSet,
                base_name='findcomposebyrr')

router.register('rpc/find-latest-compose-by-compose-rpm/(?P<compose_id>[^/]+)/(?P<rpm_name>[^/]+)',
                compose_views.FindLatestComposeByComposeRPMViewSet,
                base_name='findlatestcomposebycr')

# register common view sets
router.register(r'arches', common_views.ArchViewSet)
router.register(r'sigkeys', common_views.SigKeyViewSet)

router.register('releases/(?P<release_id>[^/]+)/rpm-mapping',
                release_views.ReleaseRPMMappingView,
                base_name='releaserpmmapping')

# register package view sets
router.register(r'rpms', rpm_views.RPMViewSet, base_name='rpms')
router.register(r'images', rpm_views.ImageViewSet)
router.register(r'build-images', rpm_views.BuildImageViewSet)

router.register(r'compose/package',
                compose_views.FindComposeWithOlderPackageViewSet,
                base_name='findcomposewitholderpackage')
router.register(r'release-variants',
                release_views.ReleaseVariantViewSet)
