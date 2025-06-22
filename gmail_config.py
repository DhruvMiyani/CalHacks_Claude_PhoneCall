# Gmail configuration for email agent
import os

APP_NAME = "CalHacksEmail"  # Gmail app name
SENDER_EMAIL = "calhackstest@gmail.com"
APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "ehhf bqpi nlio decg")  # Real Gmail App Password

# Test settings
RECIPIENT = "calhackstest@gmail.com"  # Send to same email (self-send test)
POLL_SECS = 10  # Check for replies every 10 seconds

# Note: For Gmail SMTP with 2FA, use APP_PASSWORD
# If 2FA is disabled, might need REGULAR_PASSWORD 