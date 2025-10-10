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
    export PATH="$HOME/.cargo/bin:$PATH"
else
    echo "uv is already installed"
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
Environment="PATH=$HOME/.cargo/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=$HOME/.cargo/bin/uv run fastapi dev src/zhaw_cai_news/main.py --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd, enable and start the service
echo "Enabling and starting service..."
sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl start "$SERVICE_NAME"

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