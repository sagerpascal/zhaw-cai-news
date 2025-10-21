#!/bin/bash
# filepath: /Users/sage/Documents/code/zhaw-cai-news/setup_server.sh

set -e  # Exit on error

echo "=== Setting up ZHAW CAI News Server ==="

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
APP_DIR="$SCRIPT_DIR"
APP_NAME="zhaw-cai-news"
SERVICE_NAME="zhaw-cai-news"

# Install uv if not already installed
if ! command -v uv &> /dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
else
    echo "uv is already installed"
    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
fi

UV_BIN="$(command -v uv || true)"
if [ -z "$UV_BIN" ]; then
    echo "uv not found after installation. Check PATH."
    exit 1
fi

ENV_FILE="/etc/${SERVICE_NAME}.env"
if ! sudo test -f "$ENV_FILE"; then
    echo "Creating protected environment file at $ENV_FILE"
    sudo tee "$ENV_FILE" > /dev/null <<'EOF'
# AZURE_CLIENT_ID=...
# AZURE_CLIENT_SECRET=...
# AZURE_TENANT_ID=...
# ROOM1_EMAIL=...
# ROOM2_EMAIL=...
# ENABLE_GRAPH_DEBUG=false
EOF
    sudo chmod 600 "$ENV_FILE"
fi

# Install Python dependencies
echo "Installing Python dependencies..."
cd "$APP_DIR"
uv sync

# Create systemd service file
echo "Creating systemd service..."
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=ZHAW CAI News Application
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$APP_DIR
EnvironmentFile=$ENV_FILE
Environment="PATH=$HOME/.local/bin:$HOME/.cargo/bin:/usr/local/bin:/usr/bin:/bin"
# FIX: Execute gunicorn as a Python module (-m) to ensure it's found within the uv environment.
ExecStart=$UV_BIN run python -m gunicorn --workers 1 --bind 0.0.0.0:8000 app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd, enable and start the service
echo "Enabling and starting service..."
sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl restart "$SERVICE_NAME" # Using restart instead of start to ensure changes are applied

# Get server IP for display
SERVER_IP=$(hostname -I | awk '{print $1}')

echo ""
echo "=== Setup Complete! ==="
echo "Service Status:"
sudo systemctl status "$SERVICE_NAME" --no-pager
echo ""
echo "The application is now running and will start automatically on boot."
echo "Access it at: http://${SERVER_IP}:8000"
echo "Or from localhost: http://localhost:8000"
echo ""
echo "Useful commands:"
echo "  Check status:  sudo systemctl status $SERVICE_NAME"
echo "  Stop service:  sudo systemctl stop $SERVICE_NAME"
echo "  Start service: sudo systemctl start $SERVICE_NAME"
echo "  Restart:       sudo systemctl restart $SERVICE_NAME"
echo "  View logs:     sudo journalctl -u $SERVICE_NAME -f"
echo "  Environment file: sudo nano $ENV_FILE"
