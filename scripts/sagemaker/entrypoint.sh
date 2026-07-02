#!/bin/sh
set -e
if [ "$1" = "serve" ]; then
  exec gunicorn --bind 0.0.0.0:8080 --workers 1 serve:app --chdir /opt/ml/code
fi
exec "$@"
