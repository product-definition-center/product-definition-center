default: help

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

all_tests: test api_doc_test verify_migrations

test:
	python manage.py test --settings pdc.settings_test --parallel -- pdc contrib

cover_test:
	coverage run --parallel-mode manage.py test --settings pdc.settings_test pdc contrib
	coverage combine
	coverage html --rcfile=tox.ini

api_doc_test:
	python manage.py test --settings pdc.settings_test tests.check_api_doc

verify_migrations:
	bash verify-migrations.sh

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

deploy_doc:
	./regenerate-model-svg.py
	make -C docs/ setup_gh_pages generate deploy

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

release:
	bash create-release.sh
