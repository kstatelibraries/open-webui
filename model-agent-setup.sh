#!/bin/bash

# Download and Install current version of Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Edit ollama service to expose on 0.0.0.0
# Define the systemd service file to edit
SERVICE_NAME="ollama.service"

# Use systemctl edit to open an override file for the service
sudo systemctl edit $SERVICE_NAME << EOF
[Service]
Environment="OLLAMA_HOST=0.0.0.0"
EOF

# Reload systemd daemon to apply the changes
sudo systemctl daemon-reload

# Restart the service to apply the changes immediately
sudo systemctl restart $SERVICE_NAME

echo "$SERVICE_NAME is now exposed on 0.0.0.0:11434."