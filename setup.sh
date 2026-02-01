#!/bin/bash
# Setup script for Foreplay to Slack automation

echo "=========================================="
echo "Foreplay to Slack Automation Setup"
echo "=========================================="
echo

# Check Python version
echo "Checking Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "✓ Found: $PYTHON_VERSION"
else
    echo "✗ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Install dependencies
echo
echo "Installing dependencies..."
pip3 install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✓ Dependencies installed successfully"
else
    echo "✗ Failed to install dependencies"
    exit 1
fi

# Create environment file
echo
echo "Creating .env file..."
cat > .env << 'EOF'
# Foreplay API Configuration
FOREPLAY_API_KEY=ZW3RDgCTZyNmrht0aFe3foC9Wocg0XWLzNXnWOmZ0WeeEtQ7hyOcPcPNUlVi_8UHBX4ur3r7KNbjHIhEuUmO-Q

# Slack Webhook Configuration
# Get your webhook URL from: https://api.slack.com/apps
# 1. Create new app > Incoming Webhooks > Add New Webhook
# 2. Select #creative channel
# 3. Copy the webhook URL below
SLACK_WEBHOOK_URL=

EOF

echo "✓ Created .env file"
echo

# Prompt for Slack webhook
echo "=========================================="
echo "Slack Webhook Setup"
echo "=========================================="
echo
echo "To complete setup, you need to create a Slack webhook:"
echo "1. Go to: https://api.slack.com/apps"
echo "2. Click 'Create New App' > 'From scratch'"
echo "3. Name: 'Foreplay Ad Bot', select your workspace"
echo "4. Click 'Incoming Webhooks' > Toggle ON"
echo "5. Click 'Add New Webhook to Workspace'"
echo "6. Select '#creative' channel"
echo "7. Copy the webhook URL"
echo
read -p "Paste your Slack webhook URL here (or press Enter to skip): " WEBHOOK_URL

if [ -n "$WEBHOOK_URL" ]; then
    # Update .env file with webhook
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s|SLACK_WEBHOOK_URL=|SLACK_WEBHOOK_URL=$WEBHOOK_URL|" .env
    else
        # Linux
        sed -i "s|SLACK_WEBHOOK_URL=|SLACK_WEBHOOK_URL=$WEBHOOK_URL|" .env
    fi
    echo "✓ Webhook URL saved to .env"
else
    echo "⚠ Skipped webhook setup. Edit .env file manually to add your webhook URL."
fi

echo
echo "=========================================="
echo "Testing the script..."
echo "=========================================="
echo

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Run test
python3 foreplay_slack_automation.py

echo
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo
echo "Next steps:"
echo "1. If you skipped webhook setup, edit .env and add your SLACK_WEBHOOK_URL"
echo "2. Run manually: python3 foreplay_slack_automation.py"
echo "3. Set up weekly cron job (see README.md for instructions)"
echo
echo "For scheduling: crontab -e"
echo "Add line: 0 9 * * 1 cd $(pwd) && python3 foreplay_slack_automation.py >> automation.log 2>&1"
echo
