# 🚀 PG&E Bill Split Automation - Quick Start Guide

Get your automated bill splitting system up and running in under 2 minutes!

## ⚡ One-Command Launch

```bash
cd ~/Desktop/PGE\ Split\ Automation/ && source venv/bin/activate && python app.py
```

Then open: **http://localhost:5001**

## 📋 Step-by-Step Quick Start

### 1. Navigate to Project
```bash
cd ~/Desktop/PGE\ Split\ Automation/
```

### 2. Activate Virtual Environment
```bash
source venv/bin/activate
```

### 3. Launch Web Interface
```bash
python app.py
```

### 4. Open Your Browser
```
http://localhost:5001
```

## 🛠️ Useful Commands

### Check if Everything is Working
```bash
# Test all connections at once
curl -s http://localhost:5001/test-connection/gmail | jq
curl -s http://localhost:5001/test-connection/pdf | jq
curl -s http://localhost:5001/test-connection/venmo | jq
curl -s http://localhost:5001/test-connection/mail-app | jq
```

### View Current Settings
```bash
cat .env
```

### Check Database Status
```bash
sqlite3 data/bills.db "SELECT COUNT(*) as total_bills FROM bills;"
sqlite3 data/bills.db "SELECT * FROM bills ORDER BY created_date DESC LIMIT 5;"
```

### View Recent Logs
```bash
tail -f logs/automation.log
```

### Monthly Automation Management
```bash
# Check if automation is running
python manage_schedule.py status

# Install monthly automation (5th of each month)
python manage_schedule.py install

# Test automation manually
python manage_schedule.py test

# Remove automation
python manage_schedule.py uninstall
```

## 🎯 First Time Setup Checklist

- [ ] **Gmail API**: Ensure `credentials.json` is in the project root
- [ ] **Phone Number**: Your phone (`+19298884132`) is configured in `.env`
- [ ] **Test Mode**: Keep `TEST_MODE=true` until ready for production
- [ ] **Email Access**: Make sure you have PG&E bills in Gmail from `DoNotReply@billpay.pge.com`

## 🔍 Quick Health Check

Open the web interface and click:
1. **Settings** → Test all connections (should all be green ✅)
2. **Dashboard** → Process New Bills (should find your PG&E emails)
3. **Bills** → View any processed bills

## 📂 Data Storage Locations

All your bill history and data is stored locally in these locations:

### 🗄️ **Database** (SQLite)
```
📁 data/bills.db
```
- **Bills Table**: All processed bills with amounts, dates, status
- **Processing Log**: Complete audit trail of all actions
- **Duplicate Detection**: Prevents processing same bill twice

**View Database:**
```bash
# Install SQLite browser (one-time)
brew install --cask db-browser-for-sqlite

# Open database
open data/bills.db
```

### 📄 **PDF Files**
```
📁 data/pdfs/
├── 08-08-2025-pge-bill.pdf
├── 09-08-2025-pge-bill.pdf
└── 10-08-2025-pge-bill.pdf
```
- **Professional PDFs** with bill breakdown and original email content
- **Named by due date** for easy identification
- **Permanent storage** for tax records

### 📊 **Log Files**
```
📁 logs/
├── automation.log          # Monthly automation logs
├── automation_stderr.log   # Error logs from automation
└── automation_stdout.log   # Output logs from automation
```

### ⚙️ **Configuration Files**
```
📁 Project Root/
├── .env                    # Your settings (phone, emails, etc.)
├── credentials.json        # Gmail API credentials
├── token.json             # Gmail authentication token
└── monthly_automation.py   # Generated automation script
```

## 🔍 **History Section Data Sources**

The **Dashboard** and **Bills** pages pull data from:

1. **`bills` table** in `data/bills.db`:
   ```sql
   SELECT * FROM bills ORDER BY created_date DESC;
   ```

2. **`processing_log` table** for activity history:
   ```sql
   SELECT * FROM processing_log ORDER BY timestamp DESC;
   ```

3. **PDF files** in `data/pdfs/` for downloads

4. **Real-time calculations** for statistics and summaries

## 📱 **Quick Mobile Access**

Add to your phone's home screen for easy access:
1. Open **http://localhost:5001** on your phone (same WiFi network)
2. Safari → Share → Add to Home Screen
3. Name it "PG&E Bills"

## 🆘 **Troubleshooting Quick Fixes**

### Web App Won't Start
```bash
# Check if port is in use
lsof -ti:5001

# Kill process if needed
kill -9 $(lsof -ti:5001)

# Restart
python app.py
```

### Gmail Authentication Issues
```bash
# Remove old token and re-authenticate
rm token.json
# Then process bills via web interface
```

### Database Issues
```bash
# Check database file exists and is readable
ls -la data/bills.db
sqlite3 data/bills.db ".tables"
```

### Missing Dependencies
```bash
# Reinstall requirements
pip install -r requirements.txt
```

## 🎉 **You're Ready!**

Your PG&E Bill Split Automation system is now running at:
**http://localhost:5001**

- 📊 **Dashboard**: Overview and quick actions
- 📋 **Bills**: Complete bill history and management  
- ⚙️ **Settings**: Configuration and connection tests

The system will automatically process bills on the **5th of each month** and send Venmo links to your phone!