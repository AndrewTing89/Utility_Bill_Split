# 🏠 PG&E Bill Split Automation System

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-Web%20Interface-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An automated system for splitting PG&E utility bills with roommates using Gmail API, PDF generation, and Venmo payment requests. Never manually calculate bill splits again!

![PG&E Automation Demo](https://via.placeholder.com/800x400/2563eb/ffffff?text=PG%26E+Bill+Split+Automation)

## ✨ Features

- 🔄 **Automated Bill Processing** - Scans Gmail for PG&E bills automatically
- 💰 **Smart Bill Splitting** - Customizable split ratios (default: 1/3 and 2/3)
- 📄 **Professional PDFs** - Generates official-looking bill summaries
- 💳 **Venmo Integration** - One-click payment requests with deep links
- 📧 **Email Notifications** - Automatic notifications to roommates
- 📱 **SMS Integration** - Sends Venmo links directly to your phone
- 🌐 **Web Dashboard** - Intuitive interface for management and tracking
- 🗓️ **Monthly Automation** - Runs automatically on the 5th of each month
- 🔒 **Privacy First** - All data stored locally, test mode for safe testing

## 🏠 Overview

This system automatically:
- **Parses PG&E bills** from Gmail (DoNotReply@billpay.pge.com)
- **Calculates bill splits** (you: 66.7%, roommate: 33.3%)
- **Generates professional PDFs** with bill breakdown
- **Creates Venmo payment requests** with pre-filled amounts
- **Sends email notifications** to your roommate
- **Tracks everything** in a local database
- **Runs automatically** on the 5th of each month

## 🚀 Quick Start

> **💡 Coming Soon:** AWS Lambda deployment for 100% reliability and $2-5/month hosting!

### 1. Setup Virtual Environment
```bash
cd ~/Desktop/PGE\ Split\ Automation/
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Start Web Interface
```bash
python app.py
```

### 3. Open Your Browser
```
http://localhost:5001
```

## 🌐 Web Interface

The web interface provides an intuitive dashboard for managing your bills:

### Dashboard Features
- **📊 Statistics Overview:** Total bills, pending amounts, roommate portions
- **⚡ Quick Actions:** Process new bills, test connections
- **📋 Recent Bills:** View recent bill history with status indicators
- **🔧 Pending Actions:** Bills requiring PDF generation, emails, or Venmo requests

### Bill Management
- **📄 Bill List:** Filter by status (all/pending/completed)
- **🔍 Bill Details:** Complete information about each bill
- **📱 One-Click Actions:** Generate PDFs, send emails, create Venmo links
- **📈 Progress Tracking:** Visual progress indicators for each bill

### Settings & Testing
- **⚙️ Configuration:** View current system settings
- **🧪 Connection Tests:** Test Gmail, Mail app, PDF generation, Venmo links
- **📊 Feature Status:** See which features are enabled/disabled

## 🔧 System Configuration

### Environment Variables (.env)
```bash
# Gmail API
GMAIL_USER_EMAIL=andrewhting@gmail.com

# Venmo Configuration  
ROOMMATE_VENMO=UshiLo
MY_VENMO_USERNAME=andrewhting

# Email Configuration
ROOMMATE_EMAIL=loushic@gmail.com
MY_EMAIL=andrewhting@gmail.com
EMAIL_METHOD=mac_mail_app

# Bill Split (roommate pays 1/3, you pay 2/3)
ROOMMATE_SPLIT_RATIO=0.333333
MY_SPLIT_RATIO=0.666667

# Safety Features
TEST_MODE=true                    # Prevents real emails to roommate
ENABLE_EMAIL_NOTIFICATIONS=false  # Enable when ready for production
ENABLE_AUTO_OPEN=true            # Auto-open Venmo links
ENABLE_PDF_GENERATION=true       # Generate PDFs automatically
```

## 📱 Using the Web Interface

### Processing Bills

1. **Navigate to Dashboard**
   - Click "Process New Bills" to scan Gmail for PG&E emails
   - System will find and parse new bills automatically
   - Duplicate detection prevents processing the same bill twice

2. **Review Pending Bills**
   - Dashboard shows bills requiring action
   - Each bill shows current status (PDF generated, email sent, etc.)
   - Progress bars indicate completion status

3. **Generate PDFs**
   - Click "Generate PDF" for any bill
   - Creates professional PDF with bill breakdown and original email
   - PDFs saved in `data/pdfs/` directory

4. **Send Email Notifications**
   - Click "Send Email" after PDF is generated
   - **TEST MODE:** Emails are simulated (shown in interface but not sent)
   - **Production Mode:** Sends via Mac Mail app to roommate

5. **Create Venmo Requests**
   - Click "Venmo Request" for any bill
   - Generates deep links that open Venmo app with pre-filled request
   - Shows both mobile app link and web browser fallback

### Bill Tracking

- **Bills Page:** Complete list of all processed bills
- **Filter Options:** View all, pending, or completed bills
- **Bill Details:** Click any bill to see complete information
- **Download PDFs:** Download generated PDFs for your records
- **Processing History:** See complete audit trail for each bill

## 🔐 Security & Test Mode

### Test Mode (Enabled by Default)
- **No Real Emails:** Email notifications are simulated only
- **Safe Testing:** All features work without bothering your roommate
- **Visual Indicators:** Orange banner shows TEST MODE is active
- **Database Tracking:** All actions are logged for review

### Production Mode Setup
When ready to go live:
1. Edit `.env` file: `TEST_MODE=false`
2. Edit `.env` file: `ENABLE_EMAIL_NOTIFICATIONS=true`
3. Restart the application
4. Test with a single bill first

## 📊 Database & Records

### Data Storage
- **SQLite Database:** `data/bills.db` stores all bill information
- **PDF Storage:** `data/pdfs/` contains generated bill PDFs
- **Audit Trail:** Complete processing log for each bill
- **Duplicate Prevention:** Bills identified by amount + due date

### Bill Information Tracked
- Original email content and metadata
- Bill amounts and due dates
- Split calculations (your portion vs roommate portion)
- PDF generation status and file paths
- Email notification status
- Venmo request generation and links
- Complete processing timeline

## 🔄 Automation Schedule

### Monthly Processing (5th of Each Month at 9:00 AM)
The system will automatically:
1. **Scan Gmail** for new PG&E bills
2. **Parse bill amounts** and due dates
3. **Generate PDFs** with bill breakdown
4. **Send email** to roommate with PDF attachment
5. **Create Venmo request** with pre-filled amount
6. **Open Venmo link** automatically (if enabled)
7. **Log everything** to database

### Manual Processing
You can also process bills manually anytime through the web interface.

## 🧪 Testing & Troubleshooting

### Connection Tests
Use the Settings page to test:
- **Gmail API:** Verifies authentication and email access
- **Mail App:** Tests Mac Mail app integration
- **PDF Generation:** Tests ReportLab PDF creation
- **Venmo Links:** Tests URL generation and encoding

### Common Issues

**Gmail Authentication Failed:**
```bash
# Remove old token and re-authenticate
rm token.json
# Then use web interface to process bills (will prompt for auth)
```

**PDF Generation Errors:**
```bash
# Install required system dependencies
brew install --cask wkhtmltopdf  # If using wkhtmltopdf
# Or verify ReportLab installation
pip install --upgrade reportlab
```

**Mail App Integration Issues:**
- Ensure Mac Mail app is running
- Verify your email account is configured in Mail app
- Check that AppleScript permissions are granted

## 📁 Project Structure

```
~/Desktop/PGE Split Automation/
├── app.py                    # Flask web application
├── README.md                 # This documentation
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables (create from .env.example)
├── .env.example             # Template for environment variables
├── credentials.json         # Gmail API credentials
├── config/
│   ├── settings.py          # Configuration management
│   └── pge_patterns.py      # PG&E email parsing patterns
├── src/
│   ├── bill_processor.py    # Main bill processing logic
│   ├── database.py          # SQLite database operations
│   ├── gmail_parser.py      # Gmail API integration
│   ├── pdf_generator.py     # PDF generation with ReportLab
│   ├── venmo_links.py       # Venmo deep link generation
│   └── email_notifier.py    # Email notifications via Mail app
├── templates/               # HTML templates for web interface
├── data/                    # Data storage
│   ├── bills.db            # SQLite database
│   └── pdfs/               # Generated PDF files
└── logs/                   # Application logs
```

## 💡 Tips & Best Practices

### Getting Started
1. **Start in TEST MODE** - Safely test all features first
2. **Process a few bills manually** - Understand the workflow
3. **Review generated PDFs** - Ensure quality meets your needs
4. **Test Venmo links** - Verify they work on your devices
5. **Check email templates** - Review content before going live

### Monthly Workflow
1. **System processes automatically** on the 5th
2. **Check dashboard** for any issues or pending actions
3. **Open Venmo app** when notification appears
4. **Tap "Request"** to send payment request to roommate
5. **Mark bills complete** once roommate pays

### Maintenance
- **Review logs** occasionally for any errors
- **Backup database** (`data/bills.db`) for tax records
- **Update dependencies** periodically
- **Monitor Gmail API quotas** if processing many emails

## 🆘 Support

### Logs Location
- **Application Logs:** `logs/app.log`
- **Error Logs:** `logs/error.log`
- **Database:** `data/bills.db` (SQLite browser compatible)

### Debug Mode
Run with debug logging:
```bash
export LOG_LEVEL=DEBUG
python app.py
```

### Reset Database
If you need to start fresh:
```bash
rm data/bills.db
# Database will be recreated automatically
```

## 🎯 Features Summary

✅ **Automated Gmail Processing** - Scans for PG&E bills automatically  
✅ **Smart Duplicate Detection** - Prevents processing the same bill twice  
✅ **Professional PDF Generation** - Clean, detailed bill summaries  
✅ **Venmo Deep Link Integration** - One-click payment requests  
✅ **Mac Mail App Integration** - Seamless email notifications  
✅ **Web-Based Dashboard** - Intuitive interface for management  
✅ **Complete Audit Trail** - Full tracking of all actions  
✅ **Test Mode Protection** - Safe testing without real notifications  
✅ **Monthly Automation** - Hands-off operation  
✅ **Bill History Tracking** - Perfect for tax records  

## 🔒 Privacy & Security

- **Local Processing Only** - No cloud services or external APIs except Gmail
- **Secure Credential Storage** - OAuth tokens stored locally
- **Test Mode Default** - Prevents accidental emails during setup
- **Database Encryption** - SQLite database with proper permissions
- **Audit Logging** - Complete record of all system actions

---

## 🚀 Roadmap

- [ ] **AWS Lambda Deployment** - 100% uptime, $2-5/month hosting
- [ ] **Multi-Utility Support** - Support for other utility companies
- [ ] **Mobile App** - Native iOS/Android apps
- [ ] **Split Customization** - More flexible splitting options
- [ ] **Payment Tracking** - Track when roommates actually pay

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**Andrew Ting** - [AndrewTing89](https://github.com/AndrewTing89)

---

**Ready to split bills automatically!** 🏠⚡💰
