#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from django.core.exceptions import ValidationError
from django.db import transaction
import json

import productmd
from productmd.common import create_release_id

from pdc.apps.common import hacks as common_hacks
from pdc.apps.common import models as common_models
from . import models


def _maybe_log(request, created, obj):
    """
    Optionally create an entry in changeset.
    """
    if created:
        request.changeset.add(obj.__class__.__name__,
                              obj.pk,
                              'null',
                              json.dumps(obj.export()))


def _logged_get_or_create(request, model, **kwargs):
    """
    Wrapper around `get_or_create` that also creates an entry in changeset.
    """
    obj, created = model.objects.get_or_create(**kwargs)
    _maybe_log(request, created, obj)
    return obj, created


def get_or_create_integrated_release(request, orig_release, release):
    """
    Given a PDC release and a release retrieved from compose info specified in
    a variant, return the release for integrated layered product. The Product,
    ProductVersion and BaseProduct instances will also be created if necessary.
    """
    integrated_base_product, _ = _logged_get_or_create(
        request, models.BaseProduct,
        name=orig_release.name,
        short=orig_release.short,
        version=orig_release.version.split('.')[0],
        release_type=orig_release.release_type
    )
    integrated_product, _ = _logged_get_or_create(
        request, models.Product,
        name=release.name,
        short=release.short.lower()
    )
    integrated_product_version, _ = _logged_get_or_create(
        request, models.ProductVersion,
        product=integrated_product,
        name=release.name,
        short=release.short.lower(),
        version=release.version.split('.')[0]
    )
    try:
        integrated_release, _ = _logged_get_or_create(
            request, models.Release,
            name=release.name,
            short=release.short.lower(),
            release_type=orig_release.release_type,
            version=release.version,
            base_product=integrated_base_product,
            integrated_with=orig_release,
            product_version=integrated_product_version
        )
    except ValidationError:
        release_id = create_release_id(
            release.short.lower(),
            release.version,
            orig_release.release_type.short,
            integrated_base_product.short,
            integrated_base_product.version,
            integrated_base_product.release_type.short,
        )
        msg = ('Failed to create release {} for integrated layered product.' +
               ' A conflicting release already exists.' +
               ' There is likely a version mismatch between the imported' +
               ' release and its layered integrated product in the composeinfo.')
        raise ValidationError(msg.format(release_id))
    return integrated_release


@transaction.atomic
def release__import_from_composeinfo(request, composeinfo_json):
    """
    Import release including variants and architectures from composeinfo json.
    """
    ci = productmd.composeinfo.ComposeInfo()
    common_hacks.deserialize_wrapper(ci.deserialize, composeinfo_json)

    if ci.release.is_layered:
        release_type_obj = models.ReleaseType.objects.get(short=getattr(ci.base_product, "type", "ga"))
        base_product_obj, _ = _logged_get_or_create(
            request, models.BaseProduct,
            name=ci.base_product.name,
            short=ci.base_product.short.lower(),
            version=ci.base_product.version,
            release_type=release_type_obj,
        )
    else:
        base_product_obj = None

    product_obj, _ = _logged_get_or_create(
        request, models.Product,
        name=ci.release.name,
        short=ci.release.short.lower()
    )
    product_version_obj, _ = _logged_get_or_create(
        request, models.ProductVersion,
        product=product_obj,
        name=ci.release.name,
        short=ci.release.short.lower(),
        version=ci.release.major_version
    )

    release_type_obj = models.ReleaseType.objects.get(short=getattr(ci.release, "type", "ga"))
    release_obj, _ = _logged_get_or_create(
        request, models.Release,
        name=ci.release.name,
        short=ci.release.short.lower(),
        version=ci.release.version,
        base_product=base_product_obj,
        release_type=release_type_obj,
        product_version=product_version_obj,
    )

    # if not created:
    #    raise RuntimeError("Release already exists: %s" % release_obj)

    # We can't log variants immediately after they are created, as their export
    # includes architectures. Therefore they are collected in this list and
    # logged once import is done. This also nicely abstracts integrated
    # variants that may not be present.
    add_to_changelog = []

    for variant in ci.variants.get_variants(recursive=True):
        variant_type = models.VariantType.objects.get(name=variant.type)
        release = variant.release
        integrated_variant = None
        if release.name:
            integrated_release = get_or_create_integrated_release(
                request,
                release_obj,
                release
            )
            integrated_variant, created = models.Variant.objects.get_or_create(
                release=integrated_release,
                variant_id=variant.id,
                variant_uid=variant.uid,
                variant_name=variant.name,
                variant_type=models.VariantType.objects.get(name='variant')
            )
            if created:
                add_to_changelog.append(integrated_variant)
        variant_obj, created = models.Variant.objects.get_or_create(
            release=release_obj,
            variant_id=variant.id,
            variant_uid=variant.uid,
            variant_name=variant.name,
            variant_type=variant_type,
        )
        if created:
            add_to_changelog.append(variant_obj)
        for arch in variant.arches:
            arch_obj = common_models.Arch.objects.get(name=arch)
            var_arch_obj, _ = models.VariantArch.objects.get_or_create(
                arch=arch_obj,
                variant=variant_obj
            )
            if integrated_variant:
                models.VariantArch.objects.get_or_create(
                    arch=arch_obj,
                    variant=integrated_variant
                )

    for obj in add_to_changelog:
        _maybe_log(request, True, obj)

    return release_obj
