import os
import subprocess
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Tuple

from config.settings import settings


class MacScheduler:
    """Handles Mac launchd scheduling for monthly automation"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.label = "com.user.pge-split-automation"
        self.home_dir = Path.home()
        self.plist_path = self.home_dir / "Library" / "LaunchAgents" / f"{self.label}.plist"
        self.project_dir = settings.BASE_DIR
        
    def create_automation_script(self) -> str:
        """Create the automation script that will be called by launchd"""
        script_path = self.project_dir / "monthly_automation.py"
        
        script_content = f'''#!/usr/bin/env python3
"""
PG&E Bill Split Automation - Monthly Automation Script

This script runs on the 5th of each month to:
1. Process new PG&E bills from Gmail
2. Generate PDFs with bill breakdown
3. Send email notifications to roommate
4. Create Venmo payment requests
5. Log all activities

This script is called by macOS launchd on schedule.
"""

import sys
import os
import logging
from datetime import datetime

# Add project directory to Python path
sys.path.insert(0, '{self.project_dir}')

from src.bill_processor import BillProcessor
from src.pdf_generator import PDFGenerator
from src.venmo_links import VenmoLinkGenerator
from src.email_notifier import EmailNotifier
from src.database import BillDatabase
from config.settings import settings

# Configure logging for automation
log_file = settings.LOGS_DIR / 'automation.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Main automation function"""
    logger.info("=" * 60)
    logger.info("PG&E Bill Split Automation - Run Started")
    logger.info(f"Timestamp: {{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}}")
    logger.info(f"Test Mode: {{'ENABLED' if settings.TEST_MODE else 'DISABLED'}}")
    
    # Check if this is a missed run or regular run
    today = datetime.now()
    if today.day == 5:
        logger.info("Regular monthly run on the 5th")
    else:
        logger.info(f"Running on day {{today.day}} - checking for missed bills from the 5th")
        logger.info("This could be a catch-up run after computer was off")
    
    logger.info("=" * 60)
    
    try:
        # Initialize components
        processor = BillProcessor()
        pdf_generator = PDFGenerator()
        venmo_generator = VenmoLinkGenerator()
        email_notifier = EmailNotifier()
        db = BillDatabase()
        
        # Step 1: Authenticate Gmail
        logger.info("Step 1: Authenticating with Gmail...")
        if not processor.authenticate_gmail():
            logger.error("Gmail authentication failed - aborting automation")
            return False
        
        # Step 2: Process new bills
        logger.info("Step 2: Processing new bills from Gmail...")
        results = processor.process_latest_bills(days_back=30)
        
        logger.info(f"Processing Results:")
        logger.info(f"  - New bills: {{results['processed']}}")
        logger.info(f"  - Duplicates: {{results['duplicates']}}")
        logger.info(f"  - Errors: {{results['errors']}}")
        
        if results['errors'] > 0:
            error_msg = f"{{results['errors']}} errors occurred during bill processing"
            logger.warning(error_msg)
            email_notifier.send_error_notification(error_msg)
        
        # Step 3: Process each new bill completely
        processed_bills = []
        
        for bill_info in results['new_bills']:
            bill_id = bill_info['bill_id']
            bill_amount = bill_info['amount']
            logger.info(f"Step 3: Processing bill ${{bill_amount}} (ID: {{bill_id}})")
            
            try:
                # Get full bill from database
                bill = db.get_bill_by_id(bill_id)
                if not bill:
                    logger.error(f"Could not retrieve bill {{bill_id}} from database")
                    continue
                
                # Generate PDF
                if not bill['pdf_generated']:
                    logger.info(f"  Generating PDF for bill {{bill_id}}...")
                    
                    # Get email content for PDF
                    email_content = processor.gmail.get_email_content(bill['email_id'])
                    if email_content:
                        pdf_path = pdf_generator.generate_bill_pdf(bill, email_content['body'])
                        if pdf_path:
                            db.mark_pdf_generated(bill_id, pdf_path)
                            logger.info(f"  ✓ PDF generated: {{pdf_path}}")
                        else:
                            logger.error(f"  ✗ PDF generation failed for bill {{bill_id}}")
                            continue
                    else:
                        logger.error(f"  ✗ Could not retrieve email content for bill {{bill_id}}")
                        continue
                
                # Send email notification
                if not bill['pdf_sent'] and bill['pdf_generated']:
                    logger.info(f"  Sending email notification for bill {{bill_id}}...")
                    
                    # Generate Venmo info for email
                    venmo_result = venmo_generator.process_bill_venmo_request(bill, auto_open=False)
                    if venmo_result['success']:
                        success = email_notifier.send_bill_notification(bill, bill['pdf_path'], venmo_result)
                        if success:
                            db.mark_pdf_sent(bill_id)
                            logger.info(f"  ✓ Email notification sent")
                        else:
                            logger.error(f"  ✗ Email notification failed for bill {{bill_id}}")
                    else:
                        logger.error(f"  ✗ Could not generate Venmo info for email")
                
                # Generate Venmo request
                logger.info(f"  Generating Venmo request for bill {{bill_id}}...")
                venmo_result = venmo_generator.process_bill_venmo_request(bill, auto_open=settings.ENABLE_AUTO_OPEN)
                
                if venmo_result['success']:
                    db.mark_venmo_sent(bill_id, venmo_result['venmo_url'])
                    logger.info(f"  ✓ Venmo request generated: ${{venmo_result['summary']['roommate_owes']:.2f}}")
                    
                    if settings.ENABLE_AUTO_OPEN and not settings.TEST_MODE:
                        logger.info(f"  ✓ Venmo link opened automatically")
                    
                    processed_bills.append({{
                        'bill_id': bill_id,
                        'bill_amount': bill['bill_amount'],
                        'due_date': bill['due_date'],
                        'roommate_portion': bill['roommate_portion'],
                        'my_portion': bill['my_portion']
                    }})
                else:
                    logger.error(f"  ✗ Venmo request generation failed: {{venmo_result['message']}}")
                
            except Exception as e:
                logger.error(f"Error processing bill {{bill_id}}: {{e}}")
                continue
        
        # Step 4: Send monthly summary
        if processed_bills:
            logger.info("Step 4: Sending monthly summary...")
            month_year = datetime.now().strftime('%B %Y')
            success = email_notifier.send_monthly_summary(processed_bills, month_year)
            if success:
                logger.info("✓ Monthly summary sent")
            else:
                logger.error("✗ Monthly summary failed")
        
        # Final summary
        logger.info("=" * 60)
        logger.info("Automation Summary:")
        logger.info(f"  - Bills processed: {{len(processed_bills)}}")
        logger.info(f"  - Total amount: ${{sum(bill['bill_amount'] for bill in processed_bills):.2f}}")
        logger.info(f"  - Roommate total: ${{sum(bill['roommate_portion'] for bill in processed_bills):.2f}}")
        
        if settings.TEST_MODE:
            logger.info("  - TEST MODE: No real emails sent or links opened")
        
        logger.info("PG&E Bill Split Automation - Monthly Run Completed Successfully")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        error_msg = f"Critical error during automation: {{e}}"
        logger.error(error_msg)
        
        try:
            email_notifier.send_error_notification(error_msg)
        except:
            pass  # Don't fail if error notification fails
            
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
'''
        
        # Write the script
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        # Make executable
        os.chmod(script_path, 0o755)
        
        self.logger.info(f"Created automation script: {script_path}")
        return str(script_path)
    
    def create_plist_file(self, script_path: str) -> str:
        """Create launchd plist file for scheduling"""
        
        # Get current user info
        username = os.getenv('USER', 'user')
        
        plist_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{self.label}</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>{self.project_dir}/venv/bin/python</string>
        <string>{script_path}</string>
    </array>
    
    <key>StartCalendarInterval</key>
    <dict>
        <key>Day</key>
        <integer>5</integer>
        <key>Hour</key>
        <integer>9</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    
    <key>WorkingDirectory</key>
    <string>{self.project_dir}</string>
    
    <key>StandardOutPath</key>
    <string>{self.project_dir}/logs/automation_stdout.log</string>
    
    <key>StandardErrorPath</key>
    <string>{self.project_dir}/logs/automation_stderr.log</string>
    
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin</string>
        <key>HOME</key>
        <string>{self.home_dir}</string>
    </dict>
    
    <key>RunAtLoad</key>
    <true/>
    
    <key>KeepAlive</key>
    <false/>
    
    <key>StartOnMount</key>
    <true/>
    
    <key>LaunchOnlyOnce</key>
    <false/>
</dict>
</plist>'''
        
        # Ensure LaunchAgents directory exists
        launch_agents_dir = self.home_dir / "Library" / "LaunchAgents"
        launch_agents_dir.mkdir(parents=True, exist_ok=True)
        
        # Write plist file
        with open(self.plist_path, 'w') as f:
            f.write(plist_content)
        
        self.logger.info(f"Created plist file: {self.plist_path}")
        return str(self.plist_path)
    
    def install_schedule(self) -> Tuple[bool, str]:
        """Install the scheduled automation"""
        try:
            # Create automation script
            script_path = self.create_automation_script()
            
            # Create plist file
            plist_path = self.create_plist_file(script_path)
            
            # Load the plist with launchctl
            result = subprocess.run(
                ['launchctl', 'load', str(self.plist_path)],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                self.logger.info("Successfully installed automation schedule")
                return True, f"Automation scheduled for 5th of each month at 9:00 AM"
            else:
                error_msg = f"Failed to load plist: {result.stderr}"
                self.logger.error(error_msg)
                return False, error_msg
                
        except Exception as e:
            error_msg = f"Error installing schedule: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def uninstall_schedule(self) -> Tuple[bool, str]:
        """Uninstall the scheduled automation"""
        try:
            # Unload the plist
            result = subprocess.run(
                ['launchctl', 'unload', str(self.plist_path)],
                capture_output=True,
                text=True
            )
            
            # Remove plist file
            if self.plist_path.exists():
                self.plist_path.unlink()
            
            # Remove automation script
            script_path = self.project_dir / "monthly_automation.py"
            if script_path.exists():
                script_path.unlink()
            
            self.logger.info("Successfully uninstalled automation schedule")
            return True, "Automation schedule removed"
            
        except Exception as e:
            error_msg = f"Error uninstalling schedule: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def get_schedule_status(self) -> Dict:
        """Get current schedule status"""
        try:
            # Check if plist file exists
            plist_exists = self.plist_path.exists()
            
            # Check if job is loaded
            result = subprocess.run(
                ['launchctl', 'list', self.label],
                capture_output=True,
                text=True
            )
            job_loaded = result.returncode == 0
            
            # Get job info if loaded
            job_info = {}
            if job_loaded:
                # Parse launchctl output for job details
                lines = result.stdout.strip().split('\\n')
                for line in lines:
                    if '=' in line:
                        key, value = line.split('=', 1)
                        job_info[key.strip()] = value.strip()
            
            return {
                'installed': plist_exists,
                'loaded': job_loaded,
                'plist_path': str(self.plist_path),
                'script_path': str(self.project_dir / "monthly_automation.py"),
                'schedule': "5th of each month at 9:00 AM",
                'job_info': job_info
            }
            
        except Exception as e:
            self.logger.error(f"Error getting schedule status: {e}")
            return {
                'installed': False,
                'loaded': False,
                'error': str(e)
            }
    
    def test_automation_script(self) -> Tuple[bool, str]:
        """Test the automation script manually"""
        try:
            script_path = self.project_dir / "monthly_automation.py"
            
            if not script_path.exists():
                return False, "Automation script not found - install schedule first"
            
            # Run the script
            result = subprocess.run(
                [str(self.project_dir / "venv" / "bin" / "python"), str(script_path)],
                cwd=str(self.project_dir),
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                return True, f"Automation script test successful\\n\\nOutput:\\n{result.stdout}"
            else:
                return False, f"Automation script test failed\\n\\nError:\\n{result.stderr}"
                
        except subprocess.TimeoutExpired:
            return False, "Automation script test timed out (>5 minutes)"
        except Exception as e:
            return False, f"Error testing automation script: {e}"