#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from django.db import transaction

from pdc.apps.common import hacks as common_hacks
from pdc.apps.common import models as common_models
from . import models


def get_or_create_integrated_release(orig_release, release):
    """
    Given a PDC release and a release retrieved from compose info specified in
    a variant, return the release for integrated layered product. The Product,
    ProductVersion and BaseProduct instances will also be created if necessary.
    """
    integrated_base_product, _ = models.BaseProduct.objects.get_or_create(
        name=orig_release.name,
        short=orig_release.short,
        version=orig_release.version.split('.')[0]
    )
    integrated_product, _ = models.Product.objects.get_or_create(
        name=release.name,
        short=release.short.lower()
    )
    integrated_product_version, _ = models.ProductVersion.objects.get_or_create(
        product=integrated_product,
        name=release.name,
        short=release.short.lower(),
        version=release.version.split('.')[0]
    )
    integrated_release, _ = models.Release.objects.get_or_create(
        name=release.name,
        short=release.short.lower(),
        release_type=orig_release.release_type,
        version=release.version,
        base_product=integrated_base_product,
        integrated_with=orig_release,
        product_version=integrated_product_version
    )
    return integrated_release


@transaction.atomic
def release__import_from_composeinfo(request, composeinfo_json):
    """
    Import release including variants and architectures from composeinfo json.
    """
    ci = common_hacks.composeinfo_from_str(composeinfo_json)

    if ci.release.is_layered:
        base_product_obj, _ = models.BaseProduct.objects.get_or_create(
            name=ci.base_product.name,
            short=ci.base_product.short.lower(),
            version=ci.base_product.version
        )
    else:
        base_product_obj = None

    product_obj, _ = models.Product.objects.get_or_create(
        name=ci.release.name,
        short=ci.release.short.lower()
    )
    product_version_obj, _ = models.ProductVersion.objects.get_or_create(
        product=product_obj,
        name=ci.release.name,
        short=ci.release.short.lower(),
        version=ci.release.major_version
    )

    release_type_obj = models.ReleaseType.objects.get(short=getattr(ci.release, "type", "ga"))
    release_obj, created = models.Release.objects.get_or_create(
        name=ci.release.name,
        short=ci.release.short.lower(),
        version=ci.release.version,
        base_product=base_product_obj,
        release_type=release_type_obj,
        product_version=product_version_obj,
    )

    # if not created:
    #    raise RuntimeError("Release already exists: %s" % release_obj)

    for variant in ci.get_variants(recursive=True):
        variant_type = models.VariantType.objects.get(name=variant.type)
        release = variant.release
        integrated_variant = None
        if release.name:
            integrated_release = get_or_create_integrated_release(
                release_obj,
                release
            )
            integrated_variant, _ = models.Variant.objects.get_or_create(
                release=integrated_release,
                variant_id=variant.id,
                variant_uid=variant.uid,
                variant_name=variant.name,
                variant_type=models.VariantType.objects.get(name='variant')
            )
        variant_obj, _ = models.Variant.objects.get_or_create(
            release=release_obj,
            variant_id=variant.id,
            variant_uid=variant.uid,
            variant_name=variant.name,
            variant_type=variant_type,
        )
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
