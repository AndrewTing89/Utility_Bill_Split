import os
import logging
import subprocess
import urllib.parse
from datetime import datetime
from typing import Dict, Optional
from pathlib import Path

from config.settings import settings


class VenmoLinkGenerator:
    """Generates and manages Venmo deep links for payment requests"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def generate_payment_request_link(self, bill_info: Dict) -> str:
        """Generate a Venmo deep link for payment request
        
        Args:
            bill_info: Bill information from database
            
        Returns:
            Venmo deep link URL
        """
        try:
            # Calculate amounts
            roommate_portion = float(bill_info['roommate_portion'])
            
            # Create bill note
            bill_month = datetime.strptime(bill_info['due_date'], '%m/%d/%Y').strftime('%B %Y')
            note = f"PG&E bill split - {bill_month}"
            
            # URL encode the note
            encoded_note = urllib.parse.quote(note)
            
            # Use roommate's Venmo username (phone not provided for roommate)
            recipient = settings.ROOMMATE_VENMO
            
            # Build Venmo deep link
            venmo_url = (
                f"venmo://paycharge"
                f"?txn=charge"
                f"&recipients={recipient}"
                f"&amount={roommate_portion:.2f}"
                f"&note={encoded_note}"
            )
            
            self.logger.info(f"Generated Venmo link for ${roommate_portion:.2f}")
            return venmo_url
            
        except Exception as e:
            self.logger.error(f"Failed to generate Venmo link: {e}")
            return ""
    
    def generate_web_fallback_link(self, bill_info: Dict) -> str:
        """Generate a web-based Venmo link as fallback
        
        Args:
            bill_info: Bill information from database
            
        Returns:
            Web Venmo URL
        """
        try:
            roommate_portion = float(bill_info['roommate_portion'])
            bill_month = datetime.strptime(bill_info['due_date'], '%m/%d/%Y').strftime('%B %Y')
            note = f"PG&E bill split - {bill_month}"
            
            # URL encode parameters
            encoded_note = urllib.parse.quote(note)
            
            # Use roommate's Venmo username (phone not provided for roommate)
            recipient = settings.ROOMMATE_VENMO
            encoded_recipients = urllib.parse.quote(recipient)
            
            # Build web Venmo link
            web_url = (
                f"https://venmo.com/"
                f"?txn=charge"
                f"&recipients={encoded_recipients}"
                f"&amount={roommate_portion:.2f}"
                f"&note={encoded_note}"
            )
            
            return web_url
            
        except Exception as e:
            self.logger.error(f"Failed to generate web Venmo link: {e}")
            return ""
    
    def open_venmo_link(self, venmo_url: str) -> bool:
        """Open Venmo link using Mac's 'open' command
        
        Args:
            venmo_url: The Venmo deep link to open
            
        Returns:
            True if successfully opened, False otherwise
        """
        if not venmo_url:
            print("✗ No Venmo link provided")
            return False
        
        if settings.TEST_MODE:
            print(f"🧪 TEST MODE: Would open Venmo link: {venmo_url}")
            return True
        
        try:
            # Use Mac's 'open' command to open the Venmo URL
            result = subprocess.run(
                ['open', venmo_url],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                print("✓ Venmo link opened successfully")
                self.logger.info(f"Opened Venmo link: {venmo_url}")
                return True
            else:
                print(f"✗ Failed to open Venmo link: {result.stderr}")
                self.logger.error(f"Failed to open Venmo link: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("✗ Timeout opening Venmo link")
            return False
        except Exception as e:
            print(f"✗ Error opening Venmo link: {e}")
            self.logger.error(f"Error opening Venmo link: {e}")
            return False
    
    def send_venmo_link_to_phone(self, venmo_url: str, bill_info: Dict) -> bool:
        """Send Venmo link to your phone via Messages app
        
        Args:
            venmo_url: The Venmo deep link to send
            bill_info: Bill information for context
            
        Returns:
            True if successfully sent, False otherwise
        """
        if not venmo_url or not settings.MY_PHONE or settings.MY_PHONE in ['+1234567890', '']:
            self.logger.warning("No phone number configured for Venmo link sharing")
            return False
        
        try:
            roommate_portion = float(bill_info['roommate_portion'])
            bill_month = datetime.strptime(bill_info['due_date'], '%m/%d/%Y').strftime('%B %Y')
            
            # Create message with Venmo link
            message_text = f"💰 PG&E Bill Split - {bill_month}"
            message_text += f"\\nRequest ${roommate_portion:.2f} from roommate"
            message_text += f"\\nVenmo Link: {venmo_url}"
            
            # Check if text messaging is enabled
            if not settings.ENABLE_TEXT_MESSAGING:
                print(f"📱 Text messaging disabled in settings")
                return False
            
            if settings.TEST_MODE:
                print(f"🧪 TEST MODE: Sending test message to {settings.MY_PHONE}:")
                print(f"   {message_text}")
                # In test mode, still send the message so you can test it works
            
            # Try multiple methods to send the message
            success = False
            
            # Method 1: Try iMessage first
            try:
                applescript_imessage = f'''
                tell application "Messages"
                    set targetService to 1st service whose service type = iMessage
                    set targetBuddy to buddy "{settings.MY_PHONE}" of targetService
                    send "{message_text}" to targetBuddy
                end tell
                '''
                
                result = subprocess.run(
                    ['osascript', '-e', applescript_imessage],
                    capture_output=True,
                    text=True,
                    timeout=15
                )
                
                if result.returncode == 0:
                    print(f"✓ iMessage sent to {settings.MY_PHONE}")
                    self.logger.info(f"Sent iMessage to phone: {settings.MY_PHONE}")
                    success = True
                else:
                    print(f"⚠ iMessage failed: {result.stderr}")
                    
            except Exception as e:
                print(f"⚠ iMessage error: {e}")
            
            # Method 2: Try SMS if iMessage failed
            if not success:
                try:
                    applescript_sms = f'''
                    tell application "Messages"
                        set targetService to 1st service whose service type = SMS
                        set targetBuddy to buddy "{settings.MY_PHONE}" of targetService
                        send "{message_text}" to targetBuddy
                    end tell
                    '''
                    
                    result = subprocess.run(
                        ['osascript', '-e', applescript_sms],
                        capture_output=True,
                        text=True,
                        timeout=15
                    )
                    
                    if result.returncode == 0:
                        print(f"✓ SMS sent to {settings.MY_PHONE}")
                        self.logger.info(f"Sent SMS to phone: {settings.MY_PHONE}")
                        success = True
                    else:
                        print(f"⚠ SMS failed: {result.stderr}")
                        
                except Exception as e:
                    print(f"⚠ SMS error: {e}")
            
            # Method 3: Try simple message send if both failed
            if not success:
                try:
                    applescript_simple = f'''
                    tell application "Messages"
                        send "{message_text}" to buddy "{settings.MY_PHONE}"
                    end tell
                    '''
                    
                    result = subprocess.run(
                        ['osascript', '-e', applescript_simple],
                        capture_output=True,
                        text=True,
                        timeout=15
                    )
                    
                    if result.returncode == 0:
                        print(f"✓ Message sent to {settings.MY_PHONE}")
                        self.logger.info(f"Sent message to phone: {settings.MY_PHONE}")
                        success = True
                    else:
                        print(f"✗ All message methods failed: {result.stderr}")
                        
                except Exception as e:
                    print(f"✗ Final message attempt error: {e}")
            
            if not success:
                print(f"✗ Failed to send message to {settings.MY_PHONE}")
                print("💡 Make sure Messages app is running and you're signed in")
                self.logger.error(f"Failed to send message to phone: {settings.MY_PHONE}")
            
            return success
                
        except Exception as e:
            print(f"✗ Error sending to phone: {e}")
            self.logger.error(f"Error sending to phone: {e}")
            return False
    
    def display_venmo_instructions(self, bill_info: Dict, venmo_url: str, web_url: str = None):
        """Display Venmo payment instructions to user
        
        Args:
            bill_info: Bill information from database
            venmo_url: The Venmo deep link
            web_url: Optional web fallback URL
        """
        roommate_portion = float(bill_info['roommate_portion'])
        bill_month = datetime.strptime(bill_info['due_date'], '%m/%d/%Y').strftime('%B %Y')
        
        print("\n" + "="*70)
        print("🎯 VENMO PAYMENT REQUEST")
        print("="*70)
        print(f"💰 Amount to Request: ${roommate_portion:.2f}")
        print(f"👤 Recipient: @{settings.ROOMMATE_VENMO}")
        print(f"📝 Note: PG&E bill split - {bill_month}")
        print(f"📅 Bill Due Date: {bill_info['due_date']}")
        print()
        
        print("🔗 Venmo Deep Link:")
        print(f"   {venmo_url}")
        
        if web_url:
            print("\n🌐 Web Fallback Link:")
            print(f"   {web_url}")
        
        print("\n📱 Instructions:")
        if settings.TEST_MODE:
            print("   • TEST MODE: Links are displayed but not opened automatically")
            print("   • In production, the Venmo app would open automatically")
        else:
            print("   • Venmo app should open automatically on your phone/computer")
            print("   • If not, copy the link above and paste into browser")
        
        print("   • Review the pre-filled amount and note")
        print("   • Tap 'Request' to send payment request")
        print("   • Your roommate will receive a notification")
        print("="*70)
    
    def create_payment_summary(self, bill_info: Dict) -> Dict:
        """Create a summary of the payment request
        
        Args:
            bill_info: Bill information from database
            
        Returns:
            Dictionary with payment summary
        """
        roommate_portion = float(bill_info['roommate_portion'])
        my_portion = float(bill_info['my_portion'])
        total_amount = float(bill_info['bill_amount'])
        bill_month = datetime.strptime(bill_info['due_date'], '%m/%d/%Y').strftime('%B %Y')
        
        return {
            'total_bill': total_amount,
            'roommate_owes': roommate_portion,
            'you_pay': my_portion,
            'bill_month': bill_month,
            'due_date': bill_info['due_date'],
            'venmo_recipient': settings.ROOMMATE_VENMO,
            'split_ratio': f"{settings.ROOMMATE_SPLIT_RATIO:.1%} / {settings.MY_SPLIT_RATIO:.1%}",
            'payment_note': f"PG&E bill split - {bill_month}"
        }
    
    def process_bill_venmo_request(self, bill_info: Dict, auto_open: bool = None, send_to_phone: bool = True) -> Dict:
        """Process a complete Venmo request for a bill
        
        Args:
            bill_info: Bill information from database
            auto_open: Whether to automatically open Venmo link (uses settings if None)
            send_to_phone: Whether to send Venmo link to your phone via iMessage
            
        Returns:
            Dictionary with processing results
        """
        if auto_open is None:
            auto_open = settings.ENABLE_AUTO_OPEN
        
        result = {
            'success': False,
            'venmo_url': '',
            'web_url': '',
            'opened': False,
            'sent_to_phone': False,
            'summary': {},
            'message': ''
        }
        
        try:
            # Generate links
            venmo_url = self.generate_payment_request_link(bill_info)
            web_url = self.generate_web_fallback_link(bill_info)
            
            if not venmo_url:
                result['message'] = "Failed to generate Venmo link"
                return result
            
            # Create summary
            summary = self.create_payment_summary(bill_info)
            
            # Display instructions
            self.display_venmo_instructions(bill_info, venmo_url, web_url)
            
            # Auto-open if enabled
            opened = False
            if auto_open:
                opened = self.open_venmo_link(venmo_url)
            
            # Send to phone if enabled
            sent_to_phone = False
            if send_to_phone:
                sent_to_phone = self.send_venmo_link_to_phone(venmo_url, bill_info)
            
            result.update({
                'success': True,
                'venmo_url': venmo_url,
                'web_url': web_url,
                'opened': opened,
                'sent_to_phone': sent_to_phone,
                'summary': summary,
                'message': f"Venmo request ready for ${summary['roommate_owes']:.2f}" + 
                          (f" (sent to your phone)" if sent_to_phone else "")
            })
            
            return result
            
        except Exception as e:
            result['message'] = f"Error processing Venmo request: {e}"
            self.logger.error(result['message'])
            return result
    
    def test_venmo_link_generation(self) -> bool:
        """Test Venmo link generation with sample data"""
        print("Testing Venmo link generation...")
        
        # Sample bill data
        sample_bill = {
            'bill_amount': 288.15,
            'due_date': '08/08/2025',
            'roommate_portion': 96.05,
            'my_portion': 192.10
        }
        
        try:
            # Test deep link generation
            venmo_url = self.generate_payment_request_link(sample_bill)
            if not venmo_url:
                print("✗ Failed to generate Venmo deep link")
                return False
            
            print(f"✓ Venmo deep link: {venmo_url}")
            
            # Test web fallback
            web_url = self.generate_web_fallback_link(sample_bill)
            if not web_url:
                print("✗ Failed to generate web fallback link")
                return False
            
            print(f"✓ Web fallback link: {web_url}")
            
            # Test URL encoding
            if "PG%26E" in venmo_url or "PG&E" in venmo_url:
                print("✓ URL encoding working correctly")
            else:
                print("⚠ URL encoding may have issues")
            
            # Test complete processing
            result = self.process_bill_venmo_request(sample_bill, auto_open=False)
            if result['success']:
                print("✓ Complete Venmo request processing successful")
                return True
            else:
                print(f"✗ Complete processing failed: {result['message']}")
                return False
                
        except Exception as e:
            print(f"✗ Test error: {e}")
            return False