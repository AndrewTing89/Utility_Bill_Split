import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from src.gmail_parser import GmailParser
from src.database import BillDatabase
from config.settings import settings


class BillProcessor:
    """Main processor for handling PG&E bills end-to-end"""
    
    def __init__(self):
        self.gmail = GmailParser()
        self.db = BillDatabase()
        self.logger = logging.getLogger(__name__)
    
    def authenticate_gmail(self) -> bool:
        """Authenticate with Gmail API"""
        try:
            self.gmail.authenticate()
            return True
        except Exception as e:
            self.logger.error(f"Gmail authentication failed: {e}")
            return False
    
    def process_latest_bills(self, days_back: int = 30) -> Dict:
        """Process all recent PG&E bills
        
        Args:
            days_back: How many days back to search for emails
            
        Returns:
            Dict with processing results
        """
        results = {
            'processed': 0,
            'duplicates': 0,
            'errors': 0,
            'new_bills': [],
            'duplicate_bills': [],
            'error_messages': []
        }
        
        print(f"Processing PG&E bills from last {days_back} days...")
        
        # Get Gmail messages
        messages = self.gmail.search_pge_bills(days_back=days_back)
        if not messages:
            print("No PG&E emails found")
            return results
        
        print(f"Found {len(messages)} PG&E emails to process")
        
        # Process each message
        for i, message in enumerate(messages, 1):
            print(f"\n[{i}/{len(messages)}] Processing email {message['id'][:10]}...")
            
            try:
                # Parse the bill
                bill_info = self.gmail.parse_pge_bill(message['id'])
                
                if not bill_info:
                    print("  ✗ Could not parse bill information")
                    results['errors'] += 1
                    results['error_messages'].append(f"Failed to parse email {message['id']}")
                    continue
                
                # Add to database
                success, message_text, bill_id = self.db.add_bill(bill_info)
                
                if success:
                    print(f"  ✓ {message_text}")
                    results['processed'] += 1
                    results['new_bills'].append({
                        'bill_id': bill_id,
                        'amount': bill_info['amount'],
                        'due_date': bill_info['due_date'],
                        'roommate_portion': bill_info['amount'] * settings.ROOMMATE_SPLIT_RATIO,
                        'email_subject': bill_info['email_subject']
                    })
                else:
                    print(f"  ⚠ {message_text}")
                    results['duplicates'] += 1
                    results['duplicate_bills'].append({
                        'amount': bill_info['amount'],
                        'due_date': bill_info['due_date'],
                        'email_subject': bill_info['email_subject']
                    })
                
            except Exception as e:
                print(f"  ✗ Error processing email: {e}")
                results['errors'] += 1
                results['error_messages'].append(f"Error processing {message['id']}: {e}")
        
        return results
    
    def get_pending_bills(self) -> List[Dict]:
        """Get all bills that still need processing"""
        return self.db.get_bills_by_status('pending')
    
    def get_bill_summary(self, bill_id: int) -> Optional[Dict]:
        """Get a formatted summary of a bill"""
        bill = self.db.get_bill_by_id(bill_id)
        if not bill:
            return None
        
        return {
            'id': bill['id'],
            'amount': f"${bill['bill_amount']:.2f}",
            'due_date': bill['due_date'],
            'roommate_portion': f"${bill['roommate_portion']:.2f}",
            'my_portion': f"${bill['my_portion']:.2f}",
            'status': bill['status'],
            'email_subject': bill['email_subject'],
            'processed_date': bill['processed_date'],
            'pdf_generated': bill['pdf_generated'],
            'pdf_sent': bill['pdf_sent'],
            'venmo_sent': bill['venmo_sent']
        }
    
    def mark_bill_completed(self, bill_id: int, notes: str = None) -> bool:
        """Mark a bill as completed"""
        return self.db.update_bill_status(bill_id, 'completed', notes)
    
    def get_duplicate_detection_summary(self) -> Dict:
        """Get summary of duplicate detection effectiveness"""
        log_entries = self.db.get_processing_log()
        
        duplicates_detected = len([
            entry for entry in log_entries 
            if entry['action'] == 'duplicate_detected'
        ])
        
        bills_added = len([
            entry for entry in log_entries 
            if entry['action'] == 'bill_added'
        ])
        
        return {
            'bills_added': bills_added,
            'duplicates_detected': duplicates_detected,
            'duplicate_rate': duplicates_detected / (bills_added + duplicates_detected) * 100 
                             if (bills_added + duplicates_detected) > 0 else 0
        }
    
    def test_duplicate_detection(self) -> bool:
        """Test duplicate detection by processing the same emails twice"""
        print("Testing duplicate detection...")
        
        # Process bills once
        first_run = self.process_latest_bills(days_back=60)
        print(f"\nFirst run: {first_run['processed']} processed, {first_run['duplicates']} duplicates")
        
        # Process same bills again
        second_run = self.process_latest_bills(days_back=60)
        print(f"Second run: {second_run['processed']} processed, {second_run['duplicates']} duplicates")
        
        # All bills in second run should be duplicates
        success = (second_run['processed'] == 0 and second_run['duplicates'] > 0)
        
        if success:
            print("✓ Duplicate detection working correctly!")
        else:
            print("✗ Duplicate detection may have issues")
        
        return success
    
    def show_processing_stats(self):
        """Display processing statistics"""
        stats = self.db.get_stats()
        dup_stats = self.get_duplicate_detection_summary()
        
        print("\n" + "="*50)
        print("BILL PROCESSING STATISTICS")
        print("="*50)
        print(f"Total Bills Processed: {stats['total_bills']}")
        print(f"Pending Bills: {stats['pending_bills']}")
        print(f"Completed Bills: {stats['completed_bills']}")
        print(f"Duplicates Detected: {dup_stats['duplicates_detected']}")
        print(f"Duplicate Detection Rate: {dup_stats['duplicate_rate']:.1f}%")
        print(f"\nPDFs Generated: {stats['pdfs_generated']}")
        print(f"PDFs Sent: {stats['pdfs_sent']}")
        print(f"Venmo Requests Sent: {stats['venmo_sent']}")
        print(f"\nTotal Amount: ${stats['total_amount']:.2f}")
        print(f"Roommate Portion: ${stats['total_roommate_portion']:.2f}")
        print(f"Your Portion: ${stats['total_my_portion']:.2f}")
        print("="*50)