#!/usr/bin/env bash
set -o errexit

python manage.py migrate

gunicorn lamane.wsgi:application
