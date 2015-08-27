RPMBUILD='./scripts/rpmbuild.sh'

PWD=$(shell pwd)
RPMBUILD_OPTIONS=--nodeps --define "_sourcedir $(PWD)/dist" --define "_srcrpmdir $(PWD)/dist" --define "_rpmdir $(PWD)/dist"

default: help

# Target: build a local RPM
rpm: dist
	@echo "Build rpm"
	$(RPMBUILD) -bb $(RPMBUILD_OPTIONS) || exit 1
	@echo "Build rpm - Done"

# Target for constructing a source RPM:
srpm: dist
	@echo "Build source rpm"
	$(RPMBUILD) -bs $(RPMBUILD_OPTIONS) || exit 1
	@echo "Build source rpm - Done"

# Various targets for debugging the creation of an RPM or SRPM:
# Debug target: stop after the %prep stage
debug-prep: dist
	$(RPMBUILD) -bp $(RPMBUILD_OPTIONS) || exit 1

# Debug target: stop after the %build stage
debug-build: dist
	$(RPMBUILD) -bc $(RPMBUILD_OPTIONS) || exit 1

# Debug target: stop after the %install stage
debug-install: dist
	$(RPMBUILD) -bi $(RPMBUILD_OPTIONS) || exit 1

# Target for constructing a source tarball
# Based on current branch
dist: clean
	@echo "Build source tarball"
	@rm -rf dist
	@python setup.py sdist --formats=bztar
	@echo "Build source tarball - Done"

clean: FORCE
	@find -name '*.py[co]' -delete

FORCE:

# Check code convention based on flake8
CHECK_DIRS=.
FLAKE8_CONFIG_DIR=tox.ini

flake8:
	flake8 $(CHECK_DIRS) --config=$(FLAKE8_CONFIG_DIR)

run:
	python manage.py runserver 0.0.0.0:8000

test:
	python manage.py test --settings pdc.settings_test

cover_test:
	coverage run --parallel-mode manage.py test --settings pdc.settings_test
	coverage combine
	coverage html --rcfile=tox.ini

extra_test:
	python manage.py test --settings pdc.settings_test tests.check_api_doc

models_svg: export DJANGO_SETTINGS_MODULE=pdc.settings_graph_models
models_svg:
	python manage.py graph_models -aE -o docs/source/models_svg/all.svg
	python manage.py graph_models -gE bindings -o docs/source/models_svg/bindings.svg
	python manage.py graph_models -gE changeset -o docs/source/models_svg/changeset.svg
	python manage.py graph_models -gE common -o docs/source/models_svg/common.svg
	python manage.py graph_models -gE component -o docs/source/models_svg/component.svg
	python manage.py graph_models -gE compose -o docs/source/models_svg/compose.svg
	python manage.py graph_models -gE contact -o docs/source/models_svg/contact.svg
	python manage.py graph_models -gE package -o docs/source/models_svg/package.svg
	python manage.py graph_models -gE release -o docs/source/models_svg/release.svg
	python manage.py graph_models -gE repository -o docs/source/models_svg/repository.svg

doc:
	make -C docs/ html

build:
	python setup.py build

install:
	python setup.py install

help:
	@echo 'Usage: make [command]'
	@echo ''
	@echo 'Available commands:'
	@echo ''
	@echo '  clean            - delete *.py[co] files'
	@echo '  rpm              - Create binary RPM'
	@echo '  srpm             - Create source RPM'
	@echo '  dist             - Create source tarball'
	@echo '  debug-prep       - Debug pdc.spec prep'
	@echo '  debug-build      - Debug pdc.spec build'
	@echo '  debug-install    - Debug pdc.spec install'
	@echo '  flake8           - Check Python style based on flake8'
	@echo '  test             - Run command: python manage.py test'
	@echo '  cover_test       - Run test with coverage report'
	@echo '  models_svg       - Run command graph_models from django_extensions'
	@echo '                     NOTE: you need to add django_extensions to INSTALLED_APPS'
	@echo '                           which means you need to install it and also with'
	@echo '                           the required graphviz and pygraphviz'
	@echo '  doc              - Generate html docs via sphinx'
	@echo '                     NOTE: you need to install Sphinx(pip) or python-sphinx(yum)'
	@echo '  build            - Run command: python setup.py build'
	@echo '  install          - Run command: python setup.py install'
	@echo '  help             - Show this help message and exit'
