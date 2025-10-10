# Server Setup Guide

This guide explains how to set up the ZHAW CAI News application on a small internal server.

## Quick Setup

1. Make the setup script executable:
   ```bash
   chmod +x setup_server.sh
   ```

2. Run the setup script:
   ```bash
   ./setup_server.sh
   ```

The script will:
- Install `uv` (Python package manager)
- Install all Python dependencies
- Create a systemd service
- Enable automatic startup on boot
- Start the application

## Accessing the Application

After setup, the application will be available at:
- From the server: `http://localhost:8000`
- From other devices: `http://<server-ip>:8000`

The setup script will display the server IP address.

## Managing the Service

### Check service status
```bash
sudo systemctl status zhaw-cai-news
```

### View logs
```bash
sudo journalctl -u zhaw-cai-news -f
```

### Restart the service
```bash
sudo systemctl restart zhaw-cai-news
```

### Stop the service
```bash
sudo systemctl stop zhaw-cai-news
```

### Disable auto-start
```bash
sudo systemctl disable zhaw-cai-news
```

## Firewall Configuration

If you have a firewall enabled, you may need to allow port 8000:

```bash
sudo ufw allow 8000/tcp
```

## Updating the Application

To update the application:

1. Pull the latest changes (if using git)
2. Restart the service:
   ```bash
   sudo systemctl restart zhaw-cai-news
   ```

## Troubleshooting

### Service won't start
- Check logs: `sudo journalctl -u zhaw-cai-news -n 50`
- Verify Python is installed: `python3 --version`
- Check if port 8000 is already in use: `sudo lsof -i :8000`

### Can't access from other devices
- Verify the service is running: `sudo systemctl status zhaw-cai-news`
- Check firewall settings
- Ensure devices are on the same network
