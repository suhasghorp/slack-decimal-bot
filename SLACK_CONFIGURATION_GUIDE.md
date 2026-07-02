# Slack Socket Mode Configuration Guide
### Decimal Submission Bot — Detailed App & Workspace Setup

---

## Table of Contents

1. [Overview](#overview)
2. [Part 1: Create the Slack App](#part-1-create-the-slack-app)
3. [Part 2: Configure Bot Permissions](#part-2-configure-bot-permissions)
4. [Part 3: Enable Socket Mode](#part-3-enable-socket-mode)
5. [Part 4: Enable Interactivity](#part-4-enable-interactivity)
6. [Part 5: Install the App](#part-5-install-the-app)
7. [Part 6: Set Up the Workspace](#part-6-set-up-the-workspace)
8. [Part 7: Collect Credentials](#part-7-collect-credentials)
9. [Part 8: Populate .env](#part-8-populate-env)
10. [Appendix A: Corporate Proxy Configuration](#appendix-a-corporate-proxy-configuration)

---

## Overview

This guide walks you through creating a Slack app and configuring your workspace to work with the Decimal Submission Bot using **Socket Mode**. Socket Mode allows the bot to work in restricted networks where inbound internet access is blocked.

### What You'll Need
- A Slack workspace where you have **app installation permissions**
- Administrator access to the workspace is ideal (or ask your Slack admin to perform these steps)
- 15-20 minutes to complete the setup

### Key Concepts

| Term | What It Is |
|---|---|
| **Bot Token** (`xoxb-...`) | Credentials that let the bot call Slack API methods (send messages, read user info, etc.) |
| **App Token** (`xapp-...`) | Credentials that let the bot open a Socket Mode connection to Slack |
| **Socket Mode** | An outbound WebSocket connection from the bot to Slack (no inbound request URL needed) |
| **Scopes** | Permissions that define what the bot can do (read channels, write messages, etc.) |

---

# PART 1: Create the Slack App

## Step 1.1 — Go to api.slack.com

1. Open your web browser and go to: **https://api.slack.com/apps**
2. You should see a page titled **"Your Apps"** with a green **"Create New App"** button in the top right
3. Sign in with your Slack account if you're not already logged in
   - You must have **at least one Slack workspace** associated with your account
   - If you don't have a workspace, create one first at https://slack.com/

## Step 1.2 — Create a New App

1. Click the green **"Create New App"** button
2. A dialog box appears with two options:
   - **"From scratch"** (choose this)
   - "From an app manifest"
3. Click **"From scratch"**
4. A form appears asking for two pieces of information:

### Fill in the App Creation Form

**App Name Field:**
- Enter: `Decimal Submission Bot`

**Select a workspace to develop your app in:**
- Click the dropdown
- Select your target Slack workspace from the list
- If you don't see your workspace, you may need admin access to it first

5. Click the **"Create App"** button

You should see a confirmation page showing:
```
✓ App created successfully

Your app has been created. Get started by...
```

You will be automatically taken to the **Basic Information** page for your new app.

---

# PART 2: Configure Bot Permissions

## Step 2.1 — Open OAuth & Permissions

In the left sidebar, look for the **Features** section (usually showing a lightning bolt icon):

1. Click **"OAuth & Permissions"** (should be near the top of the sidebar)
2. You'll see a page with several sections:
   - **OAuth Tokens & URLs** (at the top)
   - **Scopes** (below that)
   - **Installed Apps** (at the bottom)

## Step 2.2 — Add Bot Token Scopes

Under the **"Scopes"** section:

1. Look for the subsection labeled **"Bot Token Scopes"**
2. You should see a button that says **"Add an OAuth Scope"** or a list of existing scopes (likely empty initially)
3. Click **"Add an OAuth Scope"** to add the first permission

### Add Each Required Scope

Add **each of these scopes one by one**. For each scope:

1. Click **"Add an OAuth Scope"**
2. A search box appears
3. Type or search for the scope name
4. Click the scope name when it appears in the dropdown

**Scopes to add (in order):**

1. **`chat:write`**
   - *What it does:* Allows the bot to post messages in channels and send DMs
   - *Why needed:* To post the monthly submission request and send confirmations

2. **`chat:write.public`**
   - *What it does:* Allows posting to public channels the bot hasn't explicitly joined
   - *Why needed:* Ensures the bot can post even if channel permissions change

3. **`users:read`**
   - *What it does:* Allows the bot to read Slack user profile information
   - *Why needed:* To display user names and gather user metadata

4. **`channels:read`**
   - *What it does:* Allows the bot to read information about public channels
   - *Why needed:* To verify the channel exists and get channel metadata

5. **`groups:read`**
   - *What it does:* Allows the bot to read information about private channels
   - *Why needed:* If your submission channel is private, the bot needs this

6. **`im:write`**
   - *What it does:* Allows the bot to send direct messages to users
   - *Why needed:* To send submission confirmations and status messages via DM

### Verify All Scopes Are Added

After adding all 6 scopes, scroll up to see the **Bot Token Scopes** section again. You should see:

```
✓ chat:write
✓ chat:write.public
✓ users:read
✓ channels:read
✓ groups:read
✓ im:write
```

All 6 scopes should have a checkmark or green indicator.

---

# PART 3: Enable Socket Mode

## Step 3.1 — Open Socket Mode Settings

In the left sidebar:

1. Look for **"Socket Mode"** (usually in the **Features** section, lower than OAuth & Permissions)
2. Click **"Socket Mode"**
3. You'll see a toggle switch labeled **"Enable Socket Mode"** with a description explaining Socket Mode

## Step 3.2 — Enable the Toggle

1. Click the toggle switch to turn it **ON** (it should turn green/blue)
2. You may see a confirmation message:
   ```
   Socket Mode enabled
   Your app is now using Socket Mode
   ```

3. A new section appears: **"App-Level Tokens"**

## Step 3.3 — Create an App-Level Token

In the **"App-Level Tokens"** section:

1. Click the button labeled **"Generate Token and Set Required Scopes"** or **"Generate"**
2. A dialog box asks you to name this token:
   - Suggested name: `decimal-bot-socket-token`
   - This is just a label for your records (you can name it anything)
   - Enter the name and click **"Generate"** or **"Next"**

3. Another dialog appears: **"Choose token scopes"**
   - You'll see a list of available scopes
   - Look for the scope: **`connections:write`**
   - Click the checkbox next to `connections:write`
   - This is the **ONLY** scope needed for an app-level token

4. Click **"Generate"** or **"Create"**

## Step 3.4 — Copy Your App-Level Token

A dialog box appears showing your newly created token:

**IMPORTANT: This is the ONLY time Slack will show this token. Copy it immediately.**

The token format looks like:
```
xapp-1-A1234567890-1234567890-abcdefghijklmnop
```

### How to Copy

1. Look for a **"Copy"** button next to the token (usually on the right side)
2. Click **"Copy"** to copy the token to your clipboard
3. **Paste it somewhere temporary** (Notepad, an email draft to yourself, etc.)
4. Apply the label: `SLACK_APP_TOKEN`

**After copying:**
- You can close the dialog
- Don't worry if you didn't copy it perfectly—you can regenerate the token later if needed
- The token will appear in the list below with the message "Tokens" or "Generated tokens"

---

# PART 4: Enable Interactivity

The bot uses interactive elements (buttons and modals) for the submission interface. You must enable interactivity for this to work.

## Step 4.1 — Open Interactivity & Shortcuts

In the left sidebar:

1. Look for **"Interactivity & Shortcuts"** in the Features section
2. Click on it
3. You'll see a toggle switch labeled **"Interactivity"** with the description:
   ```
   Enable interactivity features such as interactive components 
   and shortcuts for your app
   ```

## Step 4.2 — Enable the Toggle

1. Click the toggle to turn **Interactivity ON** (it turns green/blue)
2. You may see a message: `Interactivity is enabled`

3. Below the toggle, a new section appears: **"Request URL"**
   - Leave this **BLANK** for Socket Mode (this would be needed for HTTP mode, but Socket Mode doesn't use it)

4. Click **"Save Changes"** or similar button at the bottom of the page

## Step 4.3 — Verify Interactivity is Enabled

The toggle should remain green, and you should see:
```
✓ Interactivity is enabled
```

---

# PART 5: Install the App

Now that the app is configured, you need to install it to your workspace to get the **Bot User OAuth Token**.

## Step 5.1 — Go to Install App

In the left sidebar:

1. Look for **"Install App"** or **"Install to Workspace"** (usually at the top of the Features section, below Basic Information)
2. Click on it
3. The page shows:
   - A section called **"Install App to Workspace"**
   - A button labeled **"Install to Workspace"**

## Step 5.2 — Install to Your Workspace

1. Click **"Install to Workspace"**
2. You'll be redirected to a Slack authorization page showing:
   - App name: `Decimal Submission Bot`
   - A list of permissions it's requesting (matching the scopes you added)
   - A large button: **"Allow"** or **"Install"**

3. Review the permissions (they should match the 6 scopes you added earlier)
4. Click **"Allow"**

5. You'll be redirected back to the **Install App** page, now showing:
   ```
   ✓ App successfully installed to [Your Workspace Name]
   ```

## Step 5.3 — Copy the Bot User OAuth Token

On the same **Install App** page, you should now see a new section: **"OAuth Tokens for Your Workspace"**

In that section:
1. Look for the field labeled **"Bot User OAuth Token"**
2. It shows a token starting with `xoxb-`, for example:
   ```
   xoxb-1234567890-9876543210-ABcDeFgHiJkLmNoPqRsT
   ```

3. Click the **"Copy"** button next to it
4. **Paste it somewhere temporary** to save it
5. Apply the label: `SLACK_BOT_TOKEN`

---

# PART 6: Set Up the Workspace

Now that the app is installed, you need to set up the Slack workspace in your team.

## Step 6.1 — Create a Target Channel (Recommended)

Create a dedicated channel for the monthly submissions.

**In Slack (desktop app or web):**

1. In the left sidebar, find the **Channels** section
2. Click the **+** (plus icon) next to "Channels"
3. Choose **"Create a channel"**
4. Fill in the form:
   - **Channel name:** `decimal-submissions` (lowercase, no spaces)
   - **Description (optional):** "Monthly decimal data collection - Automated by Slack bot"
   - **Privacy:** Choose **"Private"** if submissions are sensitive, or **"Public"** if they should be visible
   - **Add members (optional):** You can add them now or later

5. Click **"Create Channel"**
6. You'll see a message: `"#decimal-submissions" is a new channel`

## Step 6.2 — Find Your Channel ID

You need the **Channel ID** (an internal Slack identifier, not the channel name).

**Using Slack Desktop or Web:**

1. Open your new channel: `#decimal-submissions`
2. At the top of the channel, click on the **channel name** (should show `# decimal-submissions`)
3. A panel opens on the right side showing channel details
4. Scroll down in the panel until you see: **"Channel ID"**
5. It looks like: `C0XXXXXXXXX` (starts with C, followed by alphanumerics)
6. Click the **copy icon** next to it (or manually write it down)
7. **Save it** with the label: `SLACK_CHANNEL_ID`

**Alternative method — using the URL:**

If you're viewing the channel in a web browser:
```
https://app.slack.com/client/T12345678/C0XXXXXXXXX
```
The part after the last slash is the Channel ID: `C0XXXXXXXXX`

## Step 6.3 — Invite the Bot to the Channel

The bot **must be a member** of the channel to post messages there.

**In your Slack channel:**

1. Open the channel `#decimal-submissions`
2. In the message box, type:
   ```
   /invite @Decimal Submission Bot
   ```
3. Press **Enter**
4. You should see a message:
   ```
   @Decimal Submission Bot has joined the channel
   ```

If this doesn't work:
- Try right-clicking on the channel name → "View channel details" → "Integrations" → "Add an app" → Select "Decimal Submission Bot"

---

# PART 7: Collect User IDs

You need to gather the Slack user IDs for all users who will be submitting data.

## Step 7.1 — Get User IDs from Slack

For **each person** who needs to submit data:

1. In Slack, click on their name or profile picture anywhere you see it
2. Their profile card opens on the right side
3. Click the **three dots (...)** menu in the top-right of the profile card
4. Select **"Copy member ID"**
5. A member ID is copied to your clipboard, for example: `U0A1B2C3D4`

## Step 7.2 — Collect All User IDs

Repeat Step 7.1 for each user. You should end up with a list like:

```
U0A1B2C3D4  (Alex Smith)
U0E5F6G7H8  (Jordan Lee)
U0I9J0K1L2  (Casey Chen)
```

## Step 7.3 — Create Your TARGET_USER_IDS Value

Combine all the user IDs into a **comma-separated list** (no spaces):

```
U0A1B2C3D4,U0E5F6G7H8,U0I9J0K1L2
```

**Save this** with the label: `TARGET_USER_IDS`

---

# PART 8: Populate .env

Now you have all the information needed to configure the bot.

## Step 8.1 — Create or Edit Your .env File

Navigate to your project directory and create (or edit) a file named `.env`:

```powershell
# On Windows, using PowerShell:
cd C:\PycharmProjects\slack-decimal-bot
notepad .env
```

## Step 8.2 — Fill in the Required Values

Paste or type the following into your `.env` file, replacing the placeholder values with the information you collected:

```env
# ═══════════════════════════════════════════════════════════
# SLACK CONFIGURATION (from api.slack.com/apps)
# ═══════════════════════════════════════════════════════════

# Bot token (from "Install App" → "Bot User OAuth Token")
# Starts with xoxb-
SLACK_BOT_TOKEN=xoxb-1234567890-9876543210-ABcDeFgHiJkLmNoPqRsT

# App token (from "Socket Mode" → "Generate Token")
# Starts with xapp-
SLACK_APP_TOKEN=xapp-1-A1234567890-1234567890-abcdefghijklmnop

# Channel ID (from opening the channel and scrolling to "Channel ID")
# Starts with C
SLACK_CHANNEL_ID=C0XXXXXXXXX

# User IDs (collected from each user's profile)
# Comma-separated, no spaces, each starts with U
TARGET_USER_IDS=U0A1B2C3D4,U0E5F6G7H8,U0I9J0K1L2

# ═══════════════════════════════════════════════════════════
# SQL SERVER CONFIGURATION
# ═══════════════════════════════════════════════════════════

SQL_CONNECTION_STRING=Driver={ODBC Driver 17 for SQL Server};Server=YOUR_SERVER;Database=YOUR_DB;Trusted_Connection=yes;

# ═══════════════════════════════════════════════════════════
# SCHEDULING
# ═══════════════════════════════════════════════════════════

# Run on the 1st of each month
TRIGGER_DAY_OF_MONTH=1

# Run at 9:00 AM UTC
TRIGGER_HOUR=9
TRIGGER_MINUTE=0

# Deadline for submissions (days after trigger)
SUBMISSION_DEADLINE_DAYS=10

# ═══════════════════════════════════════════════════════════
# VALIDATION
# ═══════════════════════════════════════════════════════════

# Minimum allowed decimal value
MIN_DECIMAL=0.00

# Maximum allowed decimal value
MAX_DECIMAL=100.00

# ═══════════════════════════════════════════════════════════
# LOGGING & MONITORING
# ═══════════════════════════════════════════════════════════

# Log level: DEBUG, INFO, WARNING, ERROR
LOG_LEVEL=INFO

# Log file location
LOG_FILE=logs/bot.log

# Health endpoint port
HEALTH_PORT=5000
HEALTH_HOST=0.0.0.0

# ═══════════════════════════════════════════════════════════
# CORPORATE PROXY (Optional - only if needed)
# ═══════════════════════════════════════════════════════════

# Uncomment and set these if outbound Slack access requires a proxy
# SLACK_PROXY_URL=http://proxy.company.com:8080
# SLACK_PROXY_HEADERS={"Proxy-Authorization": "Bearer token"}
```

## Step 8.3 — Save the File

1. After pasting and filling in all values, save the file:
   - In Notepad: **File → Save**
   - Keyboard shortcut: **Ctrl + S**

2. Make sure the file is named exactly `.env` (with the dot at the start)

---

# PART 9: Verify Configuration

Run the configuration test to verify everything is set up correctly.

## Step 9.1 — Run the Configuration Test

```powershell
cd C:\PycharmProjects\slack-decimal-bot
.\venv\Scripts\Activate.ps1
python test_config.py
```

## Step 9.2 — Expected Output

If everything is configured correctly, you should see:

```
════════════════════════════════════════════════════════════
Slack Decimal Bot - Pre-Deployment Configuration Test
════════════════════════════════════════════════════════════

Testing imports...
✓ All required packages imported successfully

Testing environment variables...
✓ SLACK_BOT_TOKEN: xoxb-...
✓ SLACK_APP_TOKEN: xapp-...
✓ SQL_CONNECTION_STRING: Driver={OD...
✓ SLACK_CHANNEL_ID: C0XXXXXXXXX
✓ TARGET_USER_IDS: U0A1B..., U0E5F...

[... more tests ...]

════════════════════════════════════════════════════════════
SUMMARY
════════════════════════════════════════════════════════════

✓ PASS: Imports
✓ PASS: Environment Variables
✓ PASS: Configuration Validation
✓ PASS: Database Connection
✓ PASS: Database Tables
✓ PASS: Slack Credentials
✓ PASS: Scheduler Setup

Total: 7/7 tests passed

✓ All tests passed! Bot is ready for deployment.
```

If any tests fail, see the [Troubleshooting](#troubleshooting) section below.

---

# Troubleshooting

## Problem: "SLACK_BOT_TOKEN must start with 'xoxb-'"

**Cause:** You copied the wrong token or it's malformed.

**Fix:**
1. Go to https://api.slack.com/apps
2. Select your app
3. Go to "Install App"
4. Copy the "Bot User OAuth Token" again
5. Make sure it starts with `xoxb-`
6. Update `.env` and retry

## Problem: "SLACK_APP_TOKEN must start with 'xapp-'"

**Cause:** You copied the wrong token or it's malformed.

**Fix:**
1. Go to https://api.slack.com/apps
2. Select your app
3. Go to "Socket Mode"
4. Look at "App-Level Tokens"
5. Copy the token that starts with`xapp-`
6. Update `.env` and retry

## Problem: "Slack authentication failed"

**Cause:** The tokens are invalid or have been revoked.

**Fix:**
1. Go to https://api.slack.com/apps
2. Select your app
3. Go to "Install App"
4. Click "Reinstall to Workspace" to generate new tokens
5. Copy the new Bot User OAuth Token
6. Update `.env` with the new token
7. Retry the test

## Problem: "Channel ID is invalid" or "not_in_channel"

**Cause:** The channel ID is wrong, or the bot isn't a member of the channel.

**Fix:**
1. Verify the channel ID by opening the channel in Slack
2. Click the channel name at the top
3. Scroll to find "Channel ID"
4. Copy the exact ID
5. Update `.env`
6. Invite the bot to the channel again: `/invite @Decimal Submission Bot`
7. Retry

## Problem: "Slack bot token authentication failed"

**Cause:** Token is expired or has been revoked.

**Fix:**
1. Go to https://api.slack.com/apps
2. Select your app
3. Go to "OAuth & Permissions"
4. Scroll to "OAuth Tokens"
5. Look for "Bot User OAuth Token"
6. Click "Regenerate" or "Reinstall"
7. Copy the new token
8. Update `.env`
9. Retry

---

# Appendix A: Corporate Proxy Configuration

If your organization requires outbound internet access to go through a proxy server, you can configure the bot to use a proxy for all Slack connectivity.

## How it works

When configured, the bot will route all outbound connections to Slack through your corporate proxy:

- **Socket Mode WebSocket connection** goes through the proxy
- **Slack Web API calls** go through the proxy
- **All TLS/HTTPS traffic** uses the proxy

## Configuration

**Option 1: Basic proxy (no authentication)**

Edit your `.env` file and add:

```env
SLACK_PROXY_URL=http://proxy.company.com:8080
```

**Option 2: Proxy with authentication**

If your proxy requires authentication, set additional headers:

```env
SLACK_PROXY_URL=http://proxy.company.com:8080
SLACK_PROXY_HEADERS={"Proxy-Authorization": "Basic dXNlcjpwYXNz"}
```

To generate a Basic auth header:
1. Combine `username:password`
2. Base64 encode the result
3. Prefix with `"Basic "`

**PowerShell example:**

```powershell
$credentials = "myuser:mypassword"
$encoded = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($credentials))
$authHeader = "Basic $encoded"
Write-Host $authHeader
```

Then place in `.env`:

```env
SLACK_PROXY_HEADERS={"Proxy-Authorization": "Basic bXl1c2VyOm15cGFzc3dvcmQ="}
```

**Option 3: Proxy with custom headers**

If your proxy requires additional headers (e.g., department ID, cost center), include them:

```env
SLACK_PROXY_URL=http://proxy.company.com:8080
SLACK_PROXY_HEADERS={"Proxy-Authorization": "Bearer token123", "Department": "Engineering", "Cost-Center": "1234"}
```

## NTLM authentication (Windows proxy)

If your corporate proxy uses NTLM authentication (common on Windows networks):

The Slack SDK and Python libraries support NTLM through `requests-negotiate-sspi` on Windows or `requests-ntlm` on other systems.

To enable NTLM:

```powershell
.\venv\Scripts\pip install requests-negotiate-sspi
```

Then configure the proxy URL without credentials (the OS will supply them):

```env
SLACK_PROXY_URL=http://proxy.company.com:8080
```

## Testing the proxy configuration

After updating `.env` with your proxy settings, run the configuration test:

```powershell
python test_config.py
```

If the test completes successfully, the proxy configuration is working. If it fails with proxy-related errors, verify:

1. **Proxy URL is reachable** from the bot server:
   ```powershell
   Test-NetConnection proxy.company.com -Port 8080
   ```

2. **Proxy credentials are correct** (if used):
   - Test the credentials with your organization's proxy documentation
   - Verify the Base64 encoding is exact

3. **Proxy allows WebSocket connections**:
   - Some proxies block WebSocket traffic
   - Contact your network team to confirm WebSocket (WSS) traffic is allowed

4. **Proxy allows HTTPS traffic to Slack**:
   - Some proxies perform SSL inspection
   - The bot should handle this automatically, but contact your network team if issues persist

## Common proxy issues

| Issue | Cause | Fix |
|---|---|---|
| `Connection timeout` | Proxy is unreachable or port is wrong | Verify proxy URL and port with `Test-NetConnection` |
| `407 Proxy Authentication Required` | Credentials are missing or incorrect | Verify `SLACK_PROXY_HEADERS` contains correct Base64-encoded auth |
| `WebSocket connection failed` | Proxy doesn't support WebSocket upgrade | Contact network team; some proxies require special config for WSS |
| `SSL certificate verification failed` | Proxy performs SSL inspection | Usually handled automatically; if it persists, contact IT |
| `Slack API errors after proxy is set` | Bot is behind proxy but Slack doesn't recognize it | Remove proxy config and verify direct connection works first |

## Troubleshooting

**Enable debug logging to see proxy details:**

```env
LOG_LEVEL=DEBUG
```

Then check `logs/bot.log` for proxy-related messages.

**Test the proxy manually:**

```powershell
$proxy = @{
    "http" = "http://proxy.company.com:8080"
    "https" = "http://proxy.company.com:8080"
}

# This will test if Python can reach Google through the proxy
python -c "
import requests
try:
    r = requests.get('https://www.google.com', proxies=$proxy, timeout=5)
    print('Proxy is working')
except Exception as e:
    print(f'Proxy error: {e}')
"
```

## Reference: Environment variables format

**SLACK_PROXY_URL**

- Format: `http://[host]:[port]` or `https://[host]:[port]`
- Example: `http://proxy.company.com:8080`
- Default: (empty - no proxy used)

**SLACK_PROXY_HEADERS**

- Format: JSON object as a single-line string
- Example: `{"Proxy-Authorization": "Basic dXNlcjpwYXNz"}`
- Common headers:
  - `Proxy-Authorization`: for proxy authentication
  - Custom headers defined by your proxy/firewall
- Default: (empty - no custom headers)

---

## Network diagram with proxy

```
┌─────────────────────────────────────────────────────────┐
│ Corporate Network                                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────────────────────────┐                  │
│  │ DMZ Server (Bot)                 │                  │
│  │ ├─ Python Slack Bot              │                  │
│  │ └─ Socket Mode + Scheduler       │                  │
│  └──────────────┬────────────────────┘                  │
│                 │                                       │
│                 │ (internal)                            │
│                 │                                       │
│  ┌──────────────▼────────────────────┐                  │
│  │ Corporate Proxy                   │                  │
│  │ ├─ HTTP/HTTPS filtering           │                  │
│  │ ├─ WebSocket upgrade support      │                  │
│  │ └─ SSL inspection (optional)      │                  │
│  └──────────────┬────────────────────┘                  │
│                 │                                       │
│                 │ (outbound internet)                   │
│                 ▼                                       │
└─────────────────────────────────────────────────────────┘
                  │
                  ▼
        ┌─────────────────┐
        │ Slack Cloud     │
        │ API Endpoints   │
        │ (443/TLS)       │
        └─────────────────┘

Text flow:
1. Bot initiates outbound Socket Mode WSS connection
2. Connection goes through proxy (on port 8080)
3. Proxy forwards to Slack Cloud (TLS on 443)
4. All Slack API calls also flow through proxy
```

---

## Quick answer for security / network teams

You can share this summary directly:

> This Slack bot uses **Slack Socket Mode**. It does **not** require inbound internet access from Slack into the DMZ server. The bot initiates an **outbound** secure WebSocket connection to Slack over TCP 443 and also makes outbound HTTPS calls to Slack Web API endpoints. If outbound Slack connectivity is allowed, the bot can operate without any public-facing inbound listener. If your environment requires a proxy, the bot supports standard HTTP proxy configuration with optional authentication headers.
