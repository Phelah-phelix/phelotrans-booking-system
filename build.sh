#!/bin/bash
echo "Building the application..."

# Install dependencies
pip install -r requirements.txt

# Run database migrations
python manage.py migrate --noinput

# Collect static files
python manage.py collectstatic --noinput

echo "Build completed successfully!"
