# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#


from kobo.django.menu import MenuItem

menu = (
    MenuItem("Products", "product_pages", menu=(
        MenuItem("Base Products", "base_product/index"),
        MenuItem("Products", "product/index"),
        MenuItem("Product Versions", "product_version/index"),
    )),

    MenuItem("Releases", "release/index"),
    MenuItem("Composes", "compose/index"),
    MenuItem("API", "api-root"),
)

css_active_class = "active"
