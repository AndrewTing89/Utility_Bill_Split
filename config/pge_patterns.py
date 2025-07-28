import re
from typing import Dict, List, Optional, Tuple

class PGEPatterns:
    """Regex patterns for parsing PG&E email formats"""
    
    # Amount patterns for different PG&E email formats
    AMOUNT_PATTERNS = [
        # Original patterns from guide
        r'Statement balance:\s*\$(\d+\.\d{2})',
        r'Amount Due[:\s]*\$(\d+\.\d{2})',
        r'Total Amount Due[:\s]*\$(\d+\.\d{2})',
        r'Current charges[:\s]*\$(\d+\.\d{2})',
        # New patterns for HTML table format
        r'\*\*\$(\d+\.\d{2})\*\*',  # **$288.15** format from HTML conversion
        r'<strong>\$(\d+\.\d{2})</strong>',  # HTML strong tag format
        r'\$(\d+\.\d{2})</strong>',  # Partial HTML format
    ]
    
    # Date patterns
    DATE_PATTERNS = [
        # Original patterns from guide
        r'Payment due date:\s*(\d{2}/\d{2}/\d{4})',
        r'Due Date[:\s]*(\d{2}/\d{2}/\d{4})',
        r'Due by[:\s]*(\d{2}/\d{2}/\d{4})',
        # New patterns for HTML table format
        r'\*\*(\d{2}/\d{2}/\d{4})\s*\*\*',  # **08/08/2025** format
        r'<strong>(\d{2}/\d{2}/\d{4})\s*</strong>',  # HTML strong tag format
        r'(\d{2}/\d{2}/\d{4})\s*</strong>',  # Partial HTML format
    ]
    
    # Bill period patterns
    PERIOD_PATTERNS = [
        r'Bill period[:\s]*(\d{2}/\d{2}/\d{4})\s*-\s*(\d{2}/\d{2}/\d{4})',
        r'Service period[:\s]*(\d{2}/\d{2}/\d{4})\s*to\s*(\d{2}/\d{2}/\d{4})'
    ]
    
    @classmethod
    def extract_amount(cls, text: str) -> Optional[float]:
        """Extract bill amount from email text"""
        for pattern in cls.AMOUNT_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return float(match.group(1))
        return None
    
    @classmethod
    def extract_due_date(cls, text: str) -> Optional[str]:
        """Extract due date from email text"""
        for pattern in cls.DATE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    @classmethod
    def extract_bill_period(cls, text: str) -> Optional[Tuple[str, str]]:
        """Extract bill period from email text"""
        for pattern in cls.PERIOD_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return (match.group(1), match.group(2))
        return None
    
    @classmethod
    def parse_bill_email(cls, text: str) -> Dict[str, any]:
        """Parse all bill information from email text"""
        result = {
            'amount': cls.extract_amount(text),
            'due_date': cls.extract_due_date(text),
            'bill_period': cls.extract_bill_period(text),
            'raw_text': text
        }
        
        # Validate we found the required fields
        if not result['amount']:
            raise ValueError("Could not extract bill amount from email")
        
        if not result['due_date']:
            raise ValueError("Could not extract due date from email")
        
        return result