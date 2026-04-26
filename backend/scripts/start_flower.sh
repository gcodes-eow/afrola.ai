
#!/bin/bash

# Start Flower monitoring for Afrola.ai Celery tasks
# Usage: ./scripts/start_flower.sh
# Access at http://localhost:5555

PORT=${1:-5555}
USER=${2:-admin}
PASSWORD=${3:-afrola2024}

echo "Starting Flower monitoring on port $PORT..."
echo "Access at http://localhost:$PORT"
echo "Login: $USER / $PASSWORD"

cd "$(dirname "$0")/.."

celery -A config flower \
    --port=$PORT \
    --basic_auth=$USER:$PASSWORD \
    --broker=redis://localhost:6379/0
