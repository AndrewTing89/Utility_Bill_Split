#!/usr/bin/env python3
"""
Quick script to restore production settings after testing
"""

import os
from pathlib import Path

def restore_production_settings():
    """Restore original production settings"""
    env_file = Path(__file__).parent / '.env'
    
    print("🔄 Restoring Production Settings...")
    
    # Read current .env file
    with open(env_file, 'r') as f:
        content = f.read()
    
    # Replace test settings with production settings
    updated_content = content.replace(
        'ROOMMATE_EMAIL=andrewhting@gmail.com  # TEMPORARY: Testing with your email\n# ROOMMATE_EMAIL=loushic@gmail.com  # Original roommate email (restore after testing)',
        'ROOMMATE_EMAIL=loushic@gmail.com'
    ).replace(
        'ENABLE_EMAIL_NOTIFICATIONS=true  # TEMPORARILY ENABLED for testing',
        'ENABLE_EMAIL_NOTIFICATIONS=false  # Set to false for testing'
    ).replace(
        'TEST_MODE=false  # TEMPORARILY DISABLED to test real email sending',
        'TEST_MODE=true  # Enable test mode to prevent real emails'
    )
    
    # Write updated content
    with open(env_file, 'w') as f:
        f.write(updated_content)
    
    print("✅ Production settings restored:")
    print("   - Roommate email: loushic@gmail.com")
    print("   - Email notifications: DISABLED")
    print("   - Test mode: ENABLED")
    print("\n💡 Restart the web app to apply changes: python app.py")

if __name__ == '__main__':
    restore_production_settings()