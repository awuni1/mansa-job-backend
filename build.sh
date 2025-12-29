#!/usr/bin/env bash
# Render Build Script for Django Backend

set -o errexit  # exit on error

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Run database migrations
python manage.py migrate
