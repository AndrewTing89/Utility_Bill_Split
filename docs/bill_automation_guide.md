# PG&E Bill Split Automation System
## Complete Build Guide & Requirements

---

## Information Checklist ✅

### API Credentials
- [x] Gmail API `credentials.json` file (already in ~/Desktop/PGE Split Automation/)
- [x] Roommate's Venmo username: @UshiLo
- [x] Your Venmo username: @andrewhting
- [x] Operating System: Mac

### Utility Information
- [x] Utility to track: PG&E only
- [x] Bill email sender: DoNotReply@billpay.pge.com
- [x] Bill splitting: Split into thirds (you pay 2/3, roommate pays 1/3)
- [x] Sample PG&E bill emails (provided - 2 different formats identified)

### System Configuration
- [x] Project directory: ~/Desktop/PGE Split Automation/
- [x] Number of properties: 1 (your current residence)
- [x] Payment method: Venmo deep links (one-click automation)
- [x] Schedule: 5th of each month
- [x] PDF generation: Email-to-PDF with calculation breakdown
- [x] Roommate's email address: loushic@gmail.com

---

## Advanced Claude Prompt for Building the System

```
I need you to build a local Python CLI application for automating PG&E utility bill splitting between me and my roommate using Venmo deep links. Here are the complete requirements:

**SYSTEM OVERVIEW:**
Build a secure, local-only Python CLI application that:
1. Parses Gmail for PG&E bills from DoNotReply@billpay.pge.com using Gmail API
2. Extracts bill amounts using regex patterns specific to PG&E email format
3. Calculates roommate's portion (1/3 of total bill amount)
4. Generates professional PDF with original email content and calculation breakdown
5. Emails PDF to roommate with bill summary and split details
6. Generates Venmo deep links that open with pre-filled payment requests
7. Stores records in local SQLite database for tracking and tax records
8. Runs automatically on the 11th of each month
9. Follows security best practices for API keys and credentials

**SPECIFIC CONFIGURATION:**
- Roommate Venmo username: @UshiLo
- Your Venmo username: @andrewhting
- Roommate email: loushic@gmail.com
- Your email: andrewhting@gmail.com
- Bill splitting: Roommate pays 1/3, I pay 2/3
- Email source: DoNotReply@billpay.pge.com
- Project directory: ~/Desktop/PGE Split Automation/
- Gmail credentials: credentials.json (already in project directory)
- Operating system: Mac
- Utility: PG&E only (ignore other utilities for now)
- PDF generation: Convert email to professional PDF with calculations
- Email method: Mac Mail app integration (no password required)

**VENMO DEEP LINK INTEGRATION:**
Use Venmo URL scheme for automation:
```python
venmo_url = f"venmo://paycharge?txn=charge&recipients=UshiLo&amount={roommate_portion:.2f}&note=PG%26E%20bill%20split%20-%20{bill_date}"
```
The system should:
- Generate the deep link automatically
- Display clickable link in terminal/CLI
- Open link in browser/mobile automatically (Mac `open` command)
- Log when link was generated and clicked

**TECHNICAL REQUIREMENTS:**
- Python 3.8+ with virtual environment
- CLI interface with commands: setup, run, schedule, status, history, test
- Local SQLite database for bill records
- Environment variables for sensitive data (.env file)
- Gmail API with minimal readonly scopes
- Email-to-PDF conversion using wkhtmltopdf
- Mac Mail app integration via AppleScript (no SMTP credentials needed)
- Mac-specific scheduling using launchd
- Error handling and logging
- URL encoding for Venmo deep links

**SECURITY REQUIREMENTS:**
- All API keys in environment variables
- Local-only data processing (no cloud services)
- Secure credential storage in ~/Desktop/PGE Split Automation/credentials/
- Proper file permissions (600 for .env, 700 for credentials/)
- Gmail API with readonly scope only: 'https://www.googleapis.com/auth/gmail.readonly'

**PROJECT STRUCTURE:**
```
~/Desktop/PGE Split Automation/
├── main.py                 # CLI entry point
├── requirements.txt        # Dependencies
├── .env                   # Environment variables (create from .env.example)
├── .env.example           # Template for environment variables
├── .gitignore             # Security-focused gitignore
├── README.md              # Setup and usage instructions
├── credentials.json       # Gmail API credentials (already exists)
├── config/
│   ├── __init__.py
│   ├── settings.py        # Configuration management
│   └── pge_patterns.py    # PG&E email parsing patterns
├── src/
│   ├── __init__.py
│   ├── gmail_parser.py    # Gmail API integration
│   ├── bill_processor.py  # Bill parsing and calculation
│   ├── pdf_generator.py   # Email-to-PDF conversion
│   ├── email_notifier.py  # Send PDFs to roommate
│   ├── venmo_links.py     # Venmo deep link generation
│   ├── database.py        # SQLite operations
│   └── scheduler.py       # Mac launchd scheduling
├── credentials/           # Additional secure storage
├── logs/                  # Application logs
└── data/                  # SQLite database location
    └── bills.db
```

**CLI COMMANDS TO IMPLEMENT:**
- `python main.py setup` - Initial configuration and Gmail authentication
- `python main.py run` - Manual bill processing (parse + Venmo link only)
- `python main.py run --full` - Complete processing (parse + PDF + email + Venmo)
- `python main.py schedule` - Set up monthly automation via launchd
- `python main.py status` - Show system status and recent activity
- `python main.py history [--month YYYY-MM]` - Show bill history and payments
- `python main.py test-gmail` - Test Gmail API connection and email parsing
- `python main.py test-pdf` - Test PDF generation from sample email
- `python main.py test-email` - Test sending notification email
- `python main.py test-venmo` - Test Venmo deep link generation
- `python main.py unschedule` - Remove launchd automation

**PG&E EMAIL PARSING:**
The system needs to parse emails from DoNotReply@billpay.pge.com and extract:
- Bill amount (total due)
- Due date
- Bill period/date
- Service address (if available)

Based on provided samples, create regex patterns for these formats:

**Format 1 (Statement Balance):**
```
Statement balance: $361.30
Payment due date: 04/10/2024
```

**Format 2 (Amount Due):**
```
Amount Due: $326.71
Due Date: 10/09/2024
```

Regex patterns needed:
```python
AMOUNT_PATTERNS = [
    r'Statement balance:\s*\$(\d+\.\d{2})',
    r'Amount Due[:\s]*\$(\d+\.\d{2})'
]

DATE_PATTERNS = [
    r'Payment due date:\s*(\d{2}/\d{2}/\d{4})',
    r'Due Date[:\s]*(\d{2}/\d{2}/\d{4})'
]
```

**EMAIL INTEGRATION VIA MAC MAIL APP:**
Use AppleScript to send emails through Mac's built-in Mail app:

**Implementation:**
```python
import subprocess

def send_email_via_mail_app(to_email, subject, body, pdf_path, from_account):
    applescript = f'''
    tell application "Mail"
        set newMessage to make new outgoing message with properties {{
            subject:"{subject}",
            content:"{body}",
            sender:"{from_account}"
        }}
        tell newMessage
            make new to recipient with properties {{address:"{to_email}"}}
            make new attachment with properties {{file name:POSIX file "{pdf_path}"}}
        end tell
        send newMessage
    end tell
    '''
    subprocess.run(['osascript', '-e', applescript])
```

**Configuration:**
- From account: andrewhting@gmail.com
- To account: loushic@gmail.com
- Uses existing Mail app setup (no additional credentials needed)
- Automatically sends PDF attachment with bill breakdown
- Works with multiple email accounts in Mail app

**PDF GENERATION FEATURES:**
Convert PG&E email content to professional PDF with calculation breakdown:

**PDF Content Structure:**
```
PG&E Bill Statement - [Month Year]
═══════════════════════════════════

BILL SUMMARY:
Total Amount Due: $361.30
Due Date: 04/10/2024

SPLIT CALCULATION:
Your share (1/3): $120.43
Andrew's share (2/3): $240.87

═══════════════════════════════════
ORIGINAL BILL DETAILS:
[Clean formatted version of original PG&E email content]
```

**Implementation Requirements:**
- Use wkhtmltopdf for clean PDF generation
- PDF saved locally for records (data/pdfs/YYYY-MM-DD-pge-bill.pdf)
- Professional HTML template for consistent formatting

**VENMO DEEP LINK FEATURES:**
- Auto-calculate 1/3 split for roommate
- Generate properly URL-encoded deep links
- Include bill date and amount in note
- Provide both terminal display and auto-open functionality
- Log all generated links for tracking

**ERROR HANDLING:**
- Gmail API failures (rate limits, authentication, network issues)
- Email parsing failures (unexpected PG&E email formats)
- PDF generation errors (wkhtmltopdf issues, HTML formatting)
- Mac Mail app integration failures (AppleScript errors, Mail app not running)
- Venmo deep link generation issues
- Database connection problems
- Duplicate bill detection and handling
- Mac-specific scheduling errors

**MAC-SPECIFIC FEATURES:**
- Use `launchd` for monthly scheduling (not cron)
- Use `open` command to launch Venmo deep links
- Install wkhtmltopdf via Homebrew for PDF generation
- Mac file permission handling
- Support for Mac Python environments (homebrew, pyenv, etc.)

**DATABASE SCHEMA:**
```sql
CREATE TABLE bills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bill_date DATE,
    amount DECIMAL(10,2),
    due_date DATE,
    my_portion DECIMAL(10,2),
    roommate_portion DECIMAL(10,2),
    pdf_path TEXT,
    pdf_sent BOOLEAN DEFAULT FALSE,
    venmo_link TEXT,
    venmo_sent BOOLEAN DEFAULT FALSE,
    email_date TIMESTAMP,
    processed_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'pending',
    notes TEXT
);
```

**SAMPLE .ENV TEMPLATE:**
```
# Gmail API (uses credentials.json file)
GMAIL_USER_EMAIL=your.email@gmail.com

# Venmo Configuration
ROOMMATE_VENMO=UshiLo
MY_VENMO_USERNAME=andrewhting

# Email Configuration
ROOMMATE_EMAIL=roommate@example.com
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your.email@gmail.com
SMTP_PASSWORD=your_app_password

# Bill Configuration
ROOMMATE_SPLIT_RATIO=0.333333
MY_SPLIT_RATIO=0.666667

# Feature Settings
ENABLE_AUTO_OPEN=true
ENABLE_PDF_GENERATION=true
ENABLE_EMAIL_NOTIFICATIONS=true
ROOMMATE_EMAIL=loushic@gmail.com
MY_EMAIL=andrewhting@gmail.com
EMAIL_METHOD=mac_mail_app
ENABLE_PDF_GENERATION=true
ENABLE_EMAIL_NOTIFICATIONS=true
```

**LOGGING & MONITORING:**
- Detailed logs for all Gmail API operations
- Bill processing success/failure logs
- PDF generation and email sending logs
- Venmo link generation logs
- Monthly summary reports
- Error tracking and debugging info

**MAC LAUNCHD INTEGRATION:**
Create launchd plist file for monthly execution on the 11th:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.pge-split-automation</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/[USERNAME]/Desktop/PGE Split Automation/main.py</string>
        <string>run</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Day</key>
        <integer>11</integer>
        <key>Hour</key>
        <integer>9</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
</dict>
</plist>
```

Please build this as a production-ready application with:
1. Complete error handling and logging
2. Mac-specific implementations
3. Security best practices
4. Clear setup documentation
5. Robust PG&E email parsing
6. Reliable Venmo deep link generation
7. User-friendly CLI interface

The application should be ready to run immediately after setup with proper Gmail authentication and bill processing capabilities.
```

---

## Setup Instructions

### Step 1: Prepare Your Environment
The credentials.json file should already be in:
```
~/Desktop/PGE Split Automation/credentials.json
```

Install required system dependencies:
```bash
# Install wkhtmltopdf for PDF generation
brew install wkhtmltopdf
```

### Step 2: Configure Mail App
Ensure your Mac Mail app is set up with both accounts:
1. **Open Mail app** and verify andrewhting@gmail.com is configured
2. **Test sending** from the correct account
3. **The system will automatically use andrewhting@gmail.com** as the sender

### Step 3: Use the Advanced Prompt
1. Navigate to your project directory: `cd ~/Desktop/PGE\ Split\ Automation/`
2. Give the complete prompt above to Claude
3. Claude will build the entire system with proper Mac integration

---

## Security Best Practices

### File Permissions (Mac)
```bash
chmod 600 .env                 # Environment variables
chmod 700 credentials/         # API credentials directory
chmod 755 src/                 # Source code directory
```

### Environment Variables (.env)
```
GMAIL_USER_EMAIL=your.email@gmail.com
ROOMMATE_VENMO=UshiLo
MY_VENMO_USERNAME=your_venmo_username
ROOMMATE_SPLIT_RATIO=0.333333
MY_SPLIT_RATIO=0.666667
ENABLE_AUTO_OPEN=true
LOG_LEVEL=INFO
```

### .gitignore Template
```
.env
credentials/
*.log
__pycache__/
*.pyc
.DS_Store
venv/
.venv/
token.json
data/bills.db
```

---

## Usage Instructions

### Initial Setup
```bash
cd ~/Desktop/PGE\ Split\ Automation/
python main.py setup
```

### Complete Bill Processing with PDF & Email
```bash
python main.py run --full
```

### Quick Venmo-Only Processing
```bash
python main.py run
```

### Test PDF Generation
```bash
python main.py test-pdf
```

### Test Email Notifications
```bash
python main.py test-email
```

### Schedule Monthly Automation (11th of each month)
```bash
python main.py schedule
```

### Check System Status
```bash
python main.py status
```

### View Bill History
```bash
python main.py history --month 2025-01
```

### Test Components
```bash
python main.py test-gmail
python main.py test-venmo
```

---

## How Venmo Deep Links Work

### Generated Link Format
```
venmo://paycharge?txn=charge&recipients=UshiLo&amount=45.67&note=PG%26E%20bill%20split%20-%20Jan%202025
```

### User Experience
1. **System processes PG&E bill**: $137.00 total
2. **Calculates split**: Roommate owes $45.67 (1/3)
3. **Generates Venmo link**: Pre-filled with amount and note
4. **Auto-opens link**: Venmo app opens with request ready
5. **One tap to send**: Just hit "Request" in Venmo
6. **Tracks in database**: Records link generation and status

### Mac Integration
- Uses `open venmo://...` command to launch links
- Works with Venmo mobile app on iPhone/iPad via Handoff
- Falls back to web browser if mobile app unavailable

---

## Troubleshooting

### Common Issues
- **Gmail API Authentication**: Run `python main.py test-gmail` to verify
- **Mac Mail App Issues**: Ensure Mail app is running and andrewhting@gmail.com is configured
- **PDF Generation Errors**: Verify wkhtmltopdf is installed with `brew list wkhtmltopdf`
- **Venmo Links Not Opening**: Ensure Venmo app is installed on iPhone/iPad
- **Scheduling Issues**: Check launchd status with `launchctl list | grep pge`
- **Permission Errors**: Verify file permissions with `ls -la`

### Log Locations
- Application logs: `logs/app.log`
- Error logs: `logs/error.log`
- Bill processing: `logs/bills.log`

### Mac-Specific Notes
- Requires Python 3.8+ (install via Homebrew if needed)
- Venmo deep links work best with mobile app installed
- Uses launchd for scheduling (more reliable than cron on Mac)

---

## Monthly Automation Flow

**5th of Every Month at 9:00 AM:**
1. **Check Gmail** for new PG&E bills from DoNotReply@billpay.pge.com
2. **Parse bill amount** from email content using regex patterns
3. **Calculate split**: Roommate pays 1/3 ($120.43), you pay 2/3 ($240.87)
4. **Generate PDF** with original email + calculation breakdown
5. **Email PDF** to roommate with bill summary and split details
6. **Generate Venmo deep link** with roommate's portion
7. **Auto-open Venmo link** (if enabled) or display in terminal
8. **Log transaction** in local database with PDF path and email status
9. **Send summary** of processed bills and actions taken

**You just need to:** Tap "Request" in Venmo when it opens!

---

**Document Version**: 2.0  
**Last Updated**: January 2025  
**Configured For**: Mac user with PG&E bills and Venmo splitting  
**Automation Level**: 95% automated (one tap to send Venmo request)