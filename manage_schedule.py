#!/usr/bin/env python3
"""
PG&E Bill Split Automation - Schedule Management

This script helps you manage the monthly automation schedule.
Use this to install, uninstall, and check the status of automated bill processing.
"""

import sys
import argparse
from datetime import datetime
from src.scheduler import MacScheduler
from config.settings import settings

def main():
    parser = argparse.ArgumentParser(
        description="Manage PG&E Bill Split Automation Schedule",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python manage_schedule.py status       # Check current schedule status
  python manage_schedule.py install      # Install monthly automation
  python manage_schedule.py uninstall    # Remove automation
  python manage_schedule.py test         # Test automation script manually

Schedule Details:
  - Runs on the 5th of each month at 9:00 AM
  - Processes new PG&E bills automatically
  - Sends notifications and creates Venmo requests
  - Logs all activities for review
        """
    )
    
    parser.add_argument(
        'action',
        choices=['status', 'install', 'uninstall', 'test'],
        help='Action to perform'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force action without confirmation prompts'
    )
    
    args = parser.parse_args()
    
    # Initialize scheduler
    scheduler = MacScheduler()
    
    print("🏠 PG&E Bill Split Automation - Schedule Manager")
    print("=" * 60)
    print(f"📅 Target Schedule: 5th of each month at 9:00 AM")
    print(f"🔧 Test Mode: {'ENABLED' if settings.TEST_MODE else 'DISABLED'}")
    print("=" * 60)
    
    if args.action == 'status':
        show_status(scheduler)
    
    elif args.action == 'install':
        install_schedule(scheduler, args.force)
    
    elif args.action == 'uninstall':
        uninstall_schedule(scheduler, args.force)
    
    elif args.action == 'test':
        test_automation(scheduler)

def show_status(scheduler):
    """Show current schedule status"""
    print("📊 Checking Schedule Status...")
    print("-" * 40)
    
    status = scheduler.get_schedule_status()
    
    if 'error' in status:
        print(f"❌ Error checking status: {status['error']}")
        return
    
    print(f"📁 Plist File: {'✅ Exists' if status['installed'] else '❌ Not Found'}")
    print(f"🔄 Job Loaded: {'✅ Active' if status['loaded'] else '❌ Inactive'}")
    print(f"📅 Schedule: {status['schedule']}")
    
    print(f"\n📂 File Locations:")
    print(f"  Plist: {status['plist_path']}")
    print(f"  Script: {status['script_path']}")
    
    if status['loaded']:
        print(f"\n✅ Automation is ACTIVE and will run on schedule")
        
        # Show next run date
        from datetime import datetime, timedelta
        import calendar
        
        today = datetime.now()
        year = today.year
        month = today.month
        
        # If we're past the 5th this month, next run is next month
        if today.day >= 5:
            if month == 12:
                next_month = 1
                next_year = year + 1
            else:
                next_month = month + 1
                next_year = year
        else:
            next_month = month
            next_year = year
        
        next_run = datetime(next_year, next_month, 5, 9, 0)
        print(f"🗓️  Next Run: {next_run.strftime('%A, %B %d, %Y at %I:%M %p')}")
        
    else:
        print(f"\n⚠️  Automation is NOT active")
        print(f"   Run 'python manage_schedule.py install' to activate")
    
    # Show recent logs if available
    log_file = settings.LOGS_DIR / 'automation.log'
    if log_file.exists():
        print(f"\n📋 Recent Log Entries:")
        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()
                for line in lines[-5:]:  # Show last 5 lines
                    print(f"   {line.strip()}")
        except Exception as e:
            print(f"   Error reading log: {e}")

def install_schedule(scheduler, force=False):
    """Install the automation schedule"""
    print("⚙️  Installing Automation Schedule...")
    print("-" * 40)
    
    # Check current status
    status = scheduler.get_schedule_status()
    
    if status.get('loaded') and not force:
        print("⚠️  Automation is already installed and active.")
        response = input("Do you want to reinstall? (y/N): ")
        if response.lower() != 'y':
            print("Installation cancelled.")
            return
        
        # Uninstall first
        print("🗑️  Removing existing installation...")
        scheduler.uninstall_schedule()
    
    # Install
    print("📝 Creating automation script...")
    print("📅 Creating schedule configuration...")
    print("🔄 Loading schedule with launchd...")
    
    success, message = scheduler.install_schedule()
    
    if success:
        print(f"✅ {message}")
        print()
        print("🎉 Automation Successfully Installed!")
        print()
        print("📋 What happens next:")
        print("  • System will run automatically on the 5th of each month at 9:00 AM")
        print("  • New PG&E bills will be processed from Gmail")
        print("  • PDFs will be generated and emailed to your roommate")
        print("  • Venmo payment requests will be created")
        print("  • All activities will be logged for review")
        print()
        if settings.TEST_MODE:
            print("🧪 TEST MODE: No actual emails will be sent to your roommate")
            print("   Disable TEST_MODE in .env when ready for production")
        print()
        print("💡 Use 'python manage_schedule.py test' to test the automation manually")
        
    else:
        print(f"❌ Installation failed: {message}")
        sys.exit(1)

def uninstall_schedule(scheduler, force=False):
    """Uninstall the automation schedule"""
    print("🗑️  Uninstalling Automation Schedule...")
    print("-" * 40)
    
    status = scheduler.get_schedule_status()
    
    if not status.get('installed') and not force:
        print("ℹ️  No automation schedule found to remove.")
        return
    
    if not force:
        print("⚠️  This will remove the monthly automation schedule.")
        print("     You'll need to process bills manually after this.")
        response = input("Are you sure you want to continue? (y/N): ")
        if response.lower() != 'y':
            print("Uninstall cancelled.")
            return
    
    success, message = scheduler.uninstall_schedule()
    
    if success:
        print(f"✅ {message}")
        print()
        print("🗑️  Automation Successfully Removed!")
        print()
        print("📋 What this means:")
        print("  • No more automatic bill processing")
        print("  • You'll need to use the web interface manually")
        print("  • All existing data and PDFs are preserved")
        print()
        print("💡 Use 'python manage_schedule.py install' to re-enable automation")
        
    else:
        print(f"❌ Uninstall failed: {message}")
        sys.exit(1)

def test_automation(scheduler):
    """Test the automation script manually"""
    print("🧪 Testing Automation Script...")
    print("-" * 40)
    
    print("ℹ️  This will run the monthly automation script manually.")
    print("   It will process bills just like the scheduled run.")
    
    if settings.TEST_MODE:
        print("🧪 TEST MODE: No actual emails will be sent")
    else:
        print("⚠️  PRODUCTION MODE: Real emails will be sent!")
        response = input("Continue with test? (y/N): ")
        if response.lower() != 'y':
            print("Test cancelled.")
            return
    
    print()
    print("🚀 Running automation script...")
    print("   This may take a few minutes...")
    print()
    
    success, output = scheduler.test_automation_script()
    
    if success:
        print("✅ Automation test completed successfully!")
        print()
        print("📋 Test Output:")
        print("-" * 30)
        # Show last 20 lines of output
        lines = output.split('\n')
        for line in lines[-20:]:
            if line.strip():
                print(f"   {line}")
        print("-" * 30)
        
    else:
        print("❌ Automation test failed!")
        print()
        print("📋 Error Details:")
        print("-" * 30)
        print(output)
        print("-" * 30)
        print()
        print("💡 Check the logs for more details:")
        print(f"   - {settings.LOGS_DIR}/automation.log")
        print(f"   - {settings.LOGS_DIR}/automation_stderr.log")

if __name__ == '__main__':
    main()