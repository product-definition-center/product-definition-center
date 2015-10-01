#! /bin/bash

set -e

if python manage.py makemigrations --dry-run --exit; then
    exit 1
fi
