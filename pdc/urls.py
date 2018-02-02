#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin

from pdc.apps.utils.SortedRouter import router
from django.utils.module_loading import autodiscover_modules

from pdc.apps.release.views import ReleaseListView, ReleaseDetailView
from pdc.apps.release.views import BaseProductListView, BaseProductDetailView
from pdc.apps.release.views import ProductListView, ProductDetailView
from pdc.apps.release.views import ProductVersionListView, ProductVersionDetailView
from pdc.apps.compose.views import ComposeListView, ComposeDetailView
from pdc.apps.compose.views import ComposeRPMListView, RPMOverrideFormView, ComposeImageListView
from pdc.apps.changeset.views import ChangesetListView, ChangesetDetailView
from pdc.apps.common import views as common_views
from pdc.apps.auth import views as auth_views
from pdc.apps.release import views as release_views


autodiscover_modules('routers')

urlpatterns = [
    url(r'^$', common_views.home, name='home'),

    # see details about configuring kerberos authentication in utils/auth.py
    url(r'^auth/krb5login$', auth_views.remoteuserlogin, name='auth/krb5login'),
    url(r'^auth/saml2login$', auth_views.remoteuserlogin, name='auth/saml2login'),
    url(r'^auth/logout$', auth_views.logout, name='auth/logout'),

    url(r'^admin/', admin.site.urls),
    url(r'^auth/profile/$', auth_views.user_profile, name='auth/profile'),
    url(r'^auth/refresh-ldap/$', auth_views.refresh_ldap_groups,
        name='auth/refresh_ldap'),

    url(r"^compose/$", ComposeListView.as_view(), name="compose/index"),
    url(r"^compose/(?P<id>\d+)/$", ComposeDetailView.as_view(), name="compose/detail"),

    url(r"^compose/(?P<id>\d+)/rpms/(?P<variant>[^/]+)/$", ComposeRPMListView.as_view(),
        name="compose/id/rpms/variant"),
    url(r"^compose/(?P<id>\d+)/rpms/(?P<variant>[^/]+)/(?P<arch>[^/]+)/$",
        ComposeRPMListView.as_view(), name="compose/id/rpms/variant/arch"),

    url(r"^compose/(?P<id>\d+)/images/(?P<variant>[^/]+)/$", ComposeImageListView.as_view(),
        name="compose/id/images/variant"),
    url(r"^compose/(?P<id>\d+)/images/(?P<variant>[^/]+)/(?P<arch>[^/]+)/$",
        ComposeImageListView.as_view(), name="compose/id/images/variant/arch"),

    url(r"^override/manage/(?P<release_id>[^/]+)/", RPMOverrideFormView.as_view(),
        name="override/manage"),

    url(r"^release/$", ReleaseListView.as_view(), name="release/index"),
    url(r"^release/(?P<id>\d+)/$", ReleaseDetailView.as_view(), name="release/detail"),
    url(r"^release/(?P<release_id>[^/]+)/$", ReleaseDetailView.as_view(), name="release/detail/slug"),

    url(r"^base-product/$", BaseProductListView.as_view(), name="base_product/index"),
    url(r"^base-product/(?P<id>\d+)/$", BaseProductDetailView.as_view(), name="base_product/detail"),
    url(r"^base-product/(?P<base_product_id>[^/]+)/$", BaseProductDetailView.as_view(), name="base_product/detail/slug"),

    url(r"^product/$", ProductListView.as_view(), name="product/index"),
    url(r"^product/(?P<id>\d+)/$", ProductDetailView.as_view(), name="product/detail"),
    url(r"^product/(?P<short>[^/]+)/$", ProductDetailView.as_view(), name="product/detail/slug"),
    url(r'^product-index/$', release_views.product_pages, name='product_pages'),

    url(r"^product-version/$",
        ProductVersionListView.as_view(),
        name="product_version/index"),
    url(r"^product-version/(?P<id>\d+)/$",
        ProductVersionDetailView.as_view(),
        name="product_version/detail"),
    url(r"^product-version/(?P<product_version_id>[^/]+)/$",
        ProductVersionDetailView.as_view(),
        name="product_version/detail/slug"),

    url(r"^%s%s/" % (settings.REST_API_URL, settings.REST_API_VERSION), include(router.urls)),
    url(r"^%sperms/" % settings.REST_API_URL, auth_views.api_perms, name="api-perms"),
    url(r'^changes/$', ChangesetListView.as_view(), name='changeset/list'),
    url(r'^changes/(?P<id>\d+)/$', ChangesetDetailView.as_view(), name='changeset/detail'),
]

handler404 = 'pdc.apps.common.views.handle404'

if settings.DEBUG:
    try:
        import debug_toolbar
    except ImportError:
        pass
    else:
        urlpatterns += [
            url(r'^__debug__/', include(debug_toolbar.urls)),
        ]
