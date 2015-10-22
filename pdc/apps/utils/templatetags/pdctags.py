#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from django import template
from django.conf import settings
from django.template.loader import get_template

from pdc import get_version


def pdc_version():
    return get_version()


def login_url(redirect=None):
    """Create login url based on settings.

    Optionally, append redirection URL.
    """
    url = settings.LOGIN_URL
    redirect = redirect or settings.LOGIN_REDIRECT_URL
    if redirect:
        url += '?next=' + redirect
    return url


def do_help_modal(parser, token):
    nodelist = parser.parse(('endhelpmodal',))
    parser.delete_first_token()
    return HelpModalNode(nodelist)


class HelpModalNode(template.Node):
    """Create a Bootstrap modal dialog with help.

    Use the ``help_button.html`` template to create a button to display this
    dialog.

    To use it, just wrap the dialog contents with template tags like ::

        {% helpmodal %}
            Contents of the dialog...
        {% endhelpmodal %}

    On each page, there can be only one dialog created using this tag.
    """
    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        t = get_template('help_modal.html')
        output = self.nodelist.render(context)
        context['content'] = output
        return t.render(context)


register = template.Library()

register.simple_tag(pdc_version)
register.simple_tag(login_url)
register.tag('helpmodal', do_help_modal)
