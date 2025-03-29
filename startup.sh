#!/bin/bash

# Start Flask API in the background
cd /app/backend
gunicorn --bind 0.0.0.0:5000 app:app --daemon

# Start nginx in the foreground (to keep container running)
nginx -g "daemon off;"