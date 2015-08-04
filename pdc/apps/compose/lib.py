# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#

import os
import json

import kobo

from django.db import transaction, connection
from django.db.models import Q

from pdc.apps.package.models import RPM
from pdc.apps.common import hacks as common_hacks
from pdc.apps.common import models as common_models
from pdc.apps.package import models as package_models
from pdc.apps.repository import models as repository_models
from pdc.apps.release import models as release_models
from pdc.apps.release import lib
from pdc.apps.compose import models
from pdc.apps.release.models import Release
from pdc.apps.component.models import ReleaseComponent


def get_or_insert_rpm(rpms_in_db, cursor, rpm_nevra, srpm_nevra, filename):
    rpm_id = rpms_in_db.get(rpm_nevra, None)
    if not rpm_id:
        rpm_id = package_models.RPM.bulk_insert(cursor, rpm_nevra, filename, srpm_nevra)
        rpms_in_db[rpm_nevra] = rpm_id
    return rpm_id


def insert_compose_rpms_if_nonexist(compose_rpms_in_db, cursor,
                                    variant_arch_id, rpm_id,
                                    content_category_id, sigkey_id, path_id):
    key = "%s/%s" % (variant_arch_id, rpm_id)
    if key not in compose_rpms_in_db:
        models.ComposeRPM.bulk_insert(cursor,
                                      variant_arch_id,
                                      rpm_id,
                                      content_category_id,
                                      sigkey_id,
                                      path_id)
        compose_rpms_in_db.add(key)


def _link_compose_to_integrated_product(request, compose, variant):
    """
    If the variant belongs to an integrated layered product, update the compose
    so that it is linked to the release for that product. Note that the variant
    argument should be variant retrieved from compose info, not a PDC model.
    """
    release = variant.release
    if release.name:
        integrated_from_release = lib.get_or_create_integrated_release(
            request,
            compose.release,
            release
        )
        compose.linked_releases.add(integrated_from_release)


def _add_compose_create_msg(request, compose_obj):
    """
    Add compose create message to request.messagings.
    """
    msg = {'action': 'create',
           'compose_id': compose_obj.compose_id,
           'compose_date': compose_obj.compose_date.isoformat(),
           'compose_type': compose_obj.compose_type.name,
           'compose_respin': compose_obj.compose_respin}
    request.messagings.append(('.compose', json.dumps(msg)))


@transaction.atomic
def compose__import_rpms(request, release_id, composeinfo, rpm_manifest):
    release_obj = release_models.Release.objects.get(release_id=release_id)

    ci = common_hacks.composeinfo_from_str(composeinfo)
    rm = common_hacks.rpms_from_str(rpm_manifest)

    compose_date = "%s-%s-%s" % (ci.compose.date[:4], ci.compose.date[4:6], ci.compose.date[6:])
    compose_type = models.ComposeType.objects.get(name=ci.compose.type)
    acceptance_status = models.ComposeAcceptanceTestingState.objects.get(name='untested')
    compose_obj, created = lib._logged_get_or_create(
        request, models.Compose,
        release=release_obj,
        compose_id=ci.compose.id,
        compose_date=compose_date,
        compose_type=compose_type,
        compose_respin=ci.compose.respin,
        compose_label=ci.compose.label or None,
        acceptance_testing=acceptance_status,
    )

    if created and hasattr(request, 'messagings'):
        # add message
        _add_compose_create_msg(request, compose_obj)

    rpms_in_db = {}
    qs = package_models.RPM.objects.all()
    for rpm in qs.iterator():
        key = "%s-%s:%s-%s.%s" % (rpm.name, rpm.epoch, rpm.version, rpm.release, rpm.arch)
        rpms_in_db[key] = rpm.id

    cursor = connection.cursor()
    add_to_changelog = []
    imported_rpms = 0

    for variant in ci.get_variants(recursive=True):
        _link_compose_to_integrated_product(request, compose_obj, variant)
        variant_type = release_models.VariantType.objects.get(name=variant.type)
        variant_obj, created = models.Variant.objects.get_or_create(
            compose=compose_obj,
            variant_id=variant.id,
            variant_uid=variant.uid,
            variant_name=variant.name,
            variant_type=variant_type
        )
        if created:
            add_to_changelog.append(variant_obj)
        for arch in variant.arches:
            arch_obj = common_models.Arch.objects.get(name=arch)
            var_arch_obj, _ = models.VariantArch.objects.get_or_create(arch=arch_obj,
                                                                       variant=variant_obj)

            compose_rpms_in_db = set()
            qs = models.ComposeRPM.objects.filter(variant_arch=var_arch_obj).values_list('variant_arch_id',
                                                                                         'rpm_id')
            for (variant_arch_id, rpm_id) in qs.iterator():
                key = "%s/%s" % (variant_arch_id, rpm_id)
                compose_rpms_in_db.add(key)

            sources = set()
            for srpm_nevra, rpms in rm.rpms.get(variant.uid, {}).get(arch, {}).iteritems():
                sources.add(srpm_nevra)
                for rpm_nevra, rpm_data in rpms.iteritems():
                    imported_rpms += 1
                    path, filename = os.path.split(rpm_data['path'])
                    rpm_id = get_or_insert_rpm(rpms_in_db, cursor, rpm_nevra, srpm_nevra, filename)
                    sigkey_id = common_models.SigKey.get_cached_id(rpm_data["sigkey"], create=True)
                    path_id = models.Path.get_cached_id(path, create=True)
                    content_category = rpm_data["category"]
                    content_category_id = repository_models.ContentCategory.get_cached_id(content_category)
                    insert_compose_rpms_if_nonexist(compose_rpms_in_db, cursor,
                                                    var_arch_obj.id, rpm_id,
                                                    content_category_id, sigkey_id, path_id)

    for obj in add_to_changelog:
        lib._maybe_log(request, True, obj)

    request.changeset.add('notice', 0, 'null',
                          json.dumps({
                              'compose': compose_obj.compose_id,
                              'num_linked_rpms': imported_rpms,
                          }))


@transaction.atomic
def compose__import_images(request, release_id, composeinfo, image_manifest):
    release_obj = release_models.Release.objects.get(release_id=release_id)

    ci = common_hacks.composeinfo_from_str(composeinfo)
    im = common_hacks.images_from_str(image_manifest)

    compose_date = "%s-%s-%s" % (ci.compose.date[:4], ci.compose.date[4:6], ci.compose.date[6:])
    compose_type = models.ComposeType.objects.get(name=ci.compose.type)
    compose_obj, created = lib._logged_get_or_create(
        request, models.Compose,
        release=release_obj,
        compose_id=ci.compose.id,
        compose_date=compose_date,
        compose_type=compose_type,
        compose_respin=ci.compose.respin,
        compose_label=ci.compose.label or None,
    )

    if created and hasattr(request, 'messagings'):
        # add message
        _add_compose_create_msg(request, compose_obj)

    add_to_changelog = []
    imported_images = 0

    for variant in ci.get_variants(recursive=True):
        _link_compose_to_integrated_product(request, compose_obj, variant)
        variant_type = release_models.VariantType.objects.get(name=variant.type)
        variant_obj, created = models.Variant.objects.get_or_create(
            compose=compose_obj,
            variant_id=variant.id,
            variant_uid=variant.uid,
            variant_name=variant.name,
            variant_type=variant_type
        )
        if created:
            add_to_changelog.append(variant_obj)
        for arch in variant.arches:
            arch_obj = common_models.Arch.objects.get(name=arch)
            var_arch_obj, created = models.VariantArch.objects.get_or_create(arch=arch_obj, variant=variant_obj)

            for i in im.images.get(variant.uid, {}).get(arch, []):
                # TODO: handle properly
                try:
                    image = package_models.Image.objects.get(file_name=os.path.basename(i.path), sha256=i.checksums["sha256"])
                except package_models.Image.DoesNotExist:
                    image = package_models.Image()
                image.file_name = os.path.basename(i.path)
                image.image_format_id = package_models.ImageFormat.get_cached_id(i.format)
                image.image_type_id = package_models.ImageType.get_cached_id(i.type)
                image.disc_number = i.disc_number
                image.disc_count = i.disc_count
                image.arch = i.arch
                image.mtime = i.mtime
                image.size = i.size
                image.bootable = i.bootable
                image.implant_md5 = i.implant_md5
                image.volume_id = i.volume_id
                image.md5 = i.checksums.get("md5", None)
                image.sha1 = i.checksums.get("sha1", None)
                image.sha256 = i.checksums.get("sha256", None)
                image.save()

                # TODO: path to ComposeImage
                mi, created = models.ComposeImage.objects.get_or_create(
                    variant_arch=var_arch_obj,
                    image=image)
                imported_images += 1

    for obj in add_to_changelog:
        lib._maybe_log(request, True, obj)

    request.changeset.add('notice', 0, 'null',
                          json.dumps({
                              'compose': compose_obj.compose_id,
                              'num_linked_images': imported_images,
                          }))


def _find_composes_srpm_name_with_rpm_nvr(nvr):
    """
    Filter composes and SRPM's name with rpm nvr
    """
    try:
        nvr = kobo.rpmlib.parse_nvr(nvr)
    except ValueError:
        raise ValueError("Invalid NVR: %s" % nvr)
    q = Q()
    q &= Q(variant__variantarch__composerpm__rpm__name=nvr["name"])
    q &= Q(variant__variantarch__composerpm__rpm__version=nvr["version"])
    q &= Q(variant__variantarch__composerpm__rpm__release=nvr["release"])

    rpms = RPM.objects.filter(name=nvr["name"], version=nvr["version"], release=nvr["release"])
    srpm_name = None
    if rpms:
        srpm_name = list(set([rpm.srpm_name for rpm in rpms.distinct()]))[0]
    if srpm_name is None:
        raise ValueError("not found")
    return models.Compose.objects.filter(q).distinct(), srpm_name


def find_bugzilla_products_and_components_with_rpm_nvr(nvr):
    """
    Filter bugzilla products and components with rpm nvr
    """
    composes, srpm_name = _find_composes_srpm_name_with_rpm_nvr(nvr)
    release_ids = [compose.release for compose in composes]
    releases = [Release.objects.get(release_id=release_id) for release_id in release_ids]
    result = []
    for release in releases:
        bugzilla = dict()
        bugzilla['bugzilla_product'] = release.bugzilla_product

        component_names = common_hacks.srpm_name_to_component_names(srpm_name)
        release_components = ReleaseComponent.objects.filter(
            release=release,
            name__in=component_names).distinct()
        bugzilla['bugzilla_component'] = [rc.bugzilla_component.export()
                                          for rc in release_components
                                          if rc.bugzilla_component]
        if bugzilla not in result:
            result.append(bugzilla)
    return result
