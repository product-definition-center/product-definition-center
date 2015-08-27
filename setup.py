# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

from pdc import get_version


PACKAGE_NAME = 'pdc'
PACKAGE_VER = get_version()
PACKAGE_DESC = 'PDC - Product Definition Center'
PACKAGE_URL = 'https://github.com/release-engineering/product-definition-center.git'  # noqa


def get_install_requires():
    requires = []
    links = []
    for line in open('requirements/production.txt', 'r'):
        line = line.strip()
        if not line.startswith('#'):
            parts = line.split('#egg=')
            if len(parts) == 2:
                links.append(line)
                requires.append(parts[1])
            else:
                requires.append(line)
    return requires, links


install_requires, dependency_links = get_install_requires()


setup(
    name=PACKAGE_NAME,
    version=PACKAGE_VER,
    description=PACKAGE_DESC,
    url=PACKAGE_URL,
    author='PDC Devel Team',
    author_email='pdc-dev-list@redhat.com',
    packages=find_packages(),
    include_package_data=True,
    install_requires=install_requires,
    dependency_links=dependency_links,
)
