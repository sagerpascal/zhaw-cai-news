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

### Meeting rooms show "No meetings today" even though there are meetings

This is a **permissions issue** with the Azure App Registration. The error `403 Forbidden` means the app doesn't have the right permissions.

#### Required Azure Permissions

You need to add **Application** permissions (not Delegated) in Azure Portal:

1. Go to **Azure Portal** → **App Registrations** → Your App
2. Click **"API permissions"** in the left sidebar
3. Click **"+ Add a permission"**
4. Select **"Microsoft Graph"**
5. Choose **"Application permissions"** (NOT Delegated!)
6. Add **ALL** of these permissions:
   - `Calendars.Read` - Read calendars in all mailboxes
   - `Calendars.ReadWrite` - Read and write calendars in all mailboxes  
   - `Schedule.Read.All` - Read all schedules
   - `Place.Read.All` - Read all place resources

7. **CRITICAL**: Click **"Grant admin consent for [Your Organization]"**
   - You must be a Global Administrator or Application Administrator
   - The button should show a green checkmark after clicking

8. Wait 5-10 minutes for permissions to propagate through Microsoft's systems

#### Verify Permissions

After adding permissions, test the connection:

```bash
curl http://localhost:8000/api/test-graph-api
```

Look for:
- `"token_test": "SUCCESS"` - Authentication works
- `"events_found": 0` with `"status": "SUCCESS"` - Permission issue
- Check the logs for specific error messages

#### Alternative: Use a Service Account

If you continue to have issues, you may need to:

1. Create a dedicated service account in your organization
2. Give this account explicit permission to view the room calendars in Exchange/Outlook
3. Use delegated permissions instead of application permissions
4. Update the authentication flow to use username/password or certificate-based auth

#### Common Issues

- **"Grant admin consent" not available**: You need admin privileges in Azure AD
- **Still getting 403 after granting consent**: Wait 10-15 minutes and restart the app
- **Room mailboxes not accessible**: Room resources may need special configuration in Exchange Online
- **Works for user mailboxes but not rooms**: Rooms may need `Place.Read.All` permission

### Service won't start
- Check logs: `sudo journalctl -u zhaw-cai-news -n 50`
- Verify Python is installed: `python3 --version`
- Check if port 8000 is already in use: `sudo lsof -i :8000`

### Can't access from other devices
- Verify the service is running: `sudo systemctl status zhaw-cai-news`
- Check firewall settings
- Ensure devices are on the same network
