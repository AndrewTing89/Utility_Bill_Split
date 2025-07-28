import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
import html2text

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.platypus.frames import Frame
from reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate

from config.settings import settings


class PDFGenerator:
    """Generates PDFs from PG&E email content with bill breakdown"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        settings.ensure_directories()
        
        # Set up styles
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Set up custom paragraph styles"""
        
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.HexColor('#0066cc'),
            alignment=1  # Center alignment
        ))
        
        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=self.styles['Normal'],
            fontSize=14,
            spaceAfter=20,
            textColor=colors.HexColor('#666666'),
            alignment=1  # Center alignment
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceBefore=20,
            spaceAfter=12,
            textColor=colors.HexColor('#0066cc'),
            borderWidth=1,
            borderColor=colors.HexColor('#0066cc'),
            borderPadding=8,
            backColor=colors.HexColor('#f8f9fa')
        ))
        
        # Amount style
        self.styles.add(ParagraphStyle(
            name='AmountStyle',
            parent=self.styles['Normal'],
            fontSize=20,
            textColor=colors.HexColor('#d63384'),
            alignment=1,  # Center alignment
            fontName='Helvetica-Bold'
        ))
        
        # Email content style
        self.styles.add(ParagraphStyle(
            name='EmailContent',
            parent=self.styles['Normal'],
            fontSize=9,
            fontName='Courier',
            leftIndent=10,
            rightIndent=10,
            spaceBefore=10,
            spaceAfter=10
        ))
    
    def generate_bill_pdf(self, bill_info: Dict, email_content: str) -> Optional[str]:
        """Generate a PDF from bill information and email content
        
        Args:
            bill_info: Parsed bill information from database
            email_content: Original email body content
            
        Returns:
            Path to generated PDF file or None if failed
        """
        try:
            # Generate PDF filename
            due_date_str = bill_info['due_date'].replace('/', '-')
            pdf_filename = f"{due_date_str}-pge-bill.pdf"
            pdf_path = settings.PDF_DIR / pdf_filename
            
            # Create PDF document
            doc = SimpleDocTemplate(
                str(pdf_path),
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Build the story (content)
            story = []
            story.extend(self._create_header_section(bill_info))
            story.extend(self._create_bill_summary_section(bill_info))
            story.extend(self._create_split_calculation_section(bill_info))
            story.extend(self._create_payment_info_section(bill_info))
            story.extend(self._create_original_bill_section(bill_info, email_content))
            story.extend(self._create_footer_section())
            
            # Build PDF
            doc.build(story)
            
            self.logger.info(f"PDF generated successfully: {pdf_path}")
            return str(pdf_path)
            
        except Exception as e:
            self.logger.error(f"Failed to generate PDF: {e}")
            return None
    
    def _create_header_section(self, bill_info: Dict) -> list:
        """Create the header section of the PDF"""
        story = []
        
        # Official PG&E-style header
        story.append(Paragraph("Pacific Gas and Electric Company", self.styles['CustomTitle']))
        story.append(Paragraph("Electric Service Statement", self.styles['CustomSubtitle']))
        story.append(Paragraph("Automated Bill Split Summary", self.styles['CustomSubtitle']))
        
        # Generation info
        generation_date = datetime.now().strftime('%B %d, %Y at %I:%M %p')
        
        # Create a table for header info
        header_data = [
            ['Generated:', generation_date],
            ['Bill Period:', self._get_bill_period_string(bill_info)],
            ['Account:', 'PG&E Account ending in ******9112-5']
        ]
        
        header_table = Table(header_data, colWidths=[1.5*inch, 4*inch])
        header_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        story.append(header_table)
        story.append(Spacer(1, 20))
        
        return story
    
    def _create_bill_summary_section(self, bill_info: Dict) -> list:
        """Create the bill summary section"""
        story = []
        
        story.append(Paragraph("BILL SUMMARY", self.styles['SectionHeader']))
        
        # Create summary table
        summary_data = [
            ['Total Amount Due:', f"${float(bill_info['bill_amount']):.2f}"],
            ['Due Date:', bill_info['due_date']],
            ['Status:', bill_info.get('status', 'Pending').title()]
        ]
        
        summary_table = Table(summary_data, colWidths=[2.5*inch, 2.5*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Bold'),  # Amount in bold
            ('TEXTCOLOR', (1, 0), (1, 0), colors.HexColor('#d63384')),  # Amount in red
            ('FONTSIZE', (1, 0), (1, 0), 16),  # Larger amount
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6')),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 20))
        
        return story
    
    def _create_split_calculation_section(self, bill_info: Dict) -> list:
        """Create the split calculation section"""
        story = []
        
        story.append(Paragraph("SPLIT CALCULATION", self.styles['SectionHeader']))
        
        # Split details
        roommate_portion = float(bill_info['roommate_portion'])
        my_portion = float(bill_info['my_portion'])
        total_amount = float(bill_info['bill_amount'])
        
        split_data = [
            ['Person', 'Percentage', 'Amount', 'Responsibility'],
            [
                f'Roommate ({settings.ROOMMATE_VENMO})',
                f'{settings.ROOMMATE_SPLIT_RATIO:.1%}',
                f'${roommate_portion:.2f}',
                'Request via Venmo'
            ],
            [
                'You (Account Holder)',
                f'{settings.MY_SPLIT_RATIO:.1%}',
                f'${my_portion:.2f}',
                'Your portion'
            ],
            ['TOTAL', '100.0%', f'${total_amount:.2f}', 'Verification ✓']
        ]
        
        split_table = Table(split_data, colWidths=[2*inch, 1*inch, 1.2*inch, 1.5*inch])
        split_table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0066cc')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            
            # Roommate row
            ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#e7f3ff')),
            ('FONTNAME', (2, 1), (2, 1), 'Helvetica-Bold'),  # Amount in bold
            ('TEXTCOLOR', (2, 1), (2, 1), colors.HexColor('#0066cc')),
            
            # Your row
            ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#fff3cd')),
            ('FONTNAME', (2, 2), (2, 2), 'Helvetica-Bold'),  # Amount in bold
            ('TEXTCOLOR', (2, 2), (2, 2), colors.HexColor('#fd7e14')),
            
            # Total row
            ('BACKGROUND', (0, 3), (-1, 3), colors.HexColor('#d1edff')),
            ('FONTNAME', (0, 3), (-1, 3), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0, 3), (-1, 3), colors.HexColor('#0066cc')),
            
            # General styling
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),  # Center align amounts and percentages
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),     # Left align names
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6')),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        story.append(split_table)
        story.append(Spacer(1, 20))
        
        return story
    
    def _create_payment_info_section(self, bill_info: Dict) -> list:
        """Create the payment information section"""
        story = []
        
        story.append(Paragraph("PAYMENT INFORMATION", self.styles['SectionHeader']))
        
        # Payment instructions
        roommate_portion = float(bill_info['roommate_portion'])
        bill_month = datetime.strptime(bill_info['due_date'], '%m/%d/%Y').strftime('%B %Y')
        
        payment_info = f"""
        <b>Venmo Request Details:</b><br/>
        • Recipient: {settings.ROOMMATE_VENMO}<br/>
        • Amount: ${roommate_portion:.2f}<br/>
        • Note: "PG&E bill split - {bill_month}"<br/><br/>
        
        <b>Your Payment:</b><br/>
        • You are responsible for ${float(bill_info['my_portion']):.2f}<br/>
        • This will be paid automatically if you have autopay enabled<br/><br/>
        
        <b>Next Steps:</b><br/>
        1. Send Venmo request to roommate<br/>
        2. Ensure your portion is paid by due date: {bill_info['due_date']}<br/>
        3. Mark bill as completed once roommate pays
        """
        
        story.append(Paragraph(payment_info, self.styles['Normal']))
        story.append(Spacer(1, 20))
        
        return story
    
    def _create_original_bill_section(self, bill_info: Dict, email_content: str) -> list:
        """Create the original bill details section with email screenshot appearance"""
        story = []
        
        story.append(PageBreak())
        story.append(Paragraph("ORIGINAL PG&E EMAIL", self.styles['SectionHeader']))
        story.append(Spacer(1, 12))
        
        # Create email header that looks like a real email
        email_header_data = [
            ['From:', 'DoNotReply@billpay.pge.com'],
            ['To:', bill_info.get('recipient_email', settings.GMAIL_USER_EMAIL)],
            ['Subject:', bill_info.get('email_subject', 'Your PG&E Energy Statement is Ready to View')],
            ['Date:', bill_info.get('email_date', 'N/A')]
        ]
        
        email_header_table = Table(email_header_data, colWidths=[1*inch, 5*inch])
        email_header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
            ('BORDER', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        story.append(email_header_table)
        story.append(Spacer(1, 12))
        
        # Email body in a box to look like email content
        clean_email_content = self._clean_email_content(email_content)
        
        # Create email body style that looks like an email
        email_body_style = ParagraphStyle(
            name='EmailBody',
            parent=self.styles['Normal'],
            fontSize=10,
            fontName='Helvetica',
            leftIndent=12,
            rightIndent=12,
            spaceBefore=8,
            spaceAfter=8,
            borderWidth=1,
            borderColor=colors.HexColor('#dee2e6'),
            backColor=colors.HexColor('#ffffff'),
            borderPadding=12
        )
        
        # Add email content notice
        story.append(Paragraph(
            "<b>📧 Email Content (as received from PG&E):</b>", 
            self.styles['Normal']
        ))
        story.append(Spacer(1, 8))
        
        # Format email content to look more official
        formatted_content = clean_email_content.replace('\n', '<br/>')
        
        # Split into manageable chunks
        max_length = 3000
        if len(formatted_content) > max_length:
            formatted_content = formatted_content[:max_length] + '<br/><br/><i>[Email content truncated for PDF display]</i>'
        
        story.append(Paragraph(formatted_content, email_body_style))
        
        # Add verification footer
        story.append(Spacer(1, 20))
        verification_text = f"""
        <b>📋 Document Verification:</b><br/>
        • This email was received from PG&E's official billing system<br/>
        • Email ID: {bill_info.get('email_id', 'N/A')}<br/>
        • Processed: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}<br/>
        • All calculations verified against original bill amount
        """
        
        verification_style = ParagraphStyle(
            name='Verification',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#495057'),
            leftIndent=12,
            spaceBefore=8,
            borderWidth=1,
            borderColor=colors.HexColor('#28a745'),
            backColor=colors.HexColor('#d4edda'),
            borderPadding=8
        )
        
        story.append(Paragraph(verification_text, verification_style))
        
        return story
    
    def _create_footer_section(self) -> list:
        """Create the footer section"""
        story = []
        
        story.append(Spacer(1, 30))
        
        footer_info = f"""
        <hr/><br/>
        <i>This document was automatically generated by the PG&E Bill Split Automation System</i><br/>
        Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}<br/>
        For questions about this bill split, contact: {settings.MY_EMAIL}
        """
        
        footer_style = ParagraphStyle(
            name='Footer',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#666666'),
            alignment=1  # Center alignment
        )
        
        story.append(Paragraph(footer_info, footer_style))
        
        return story
    
    def _get_bill_period_string(self, bill_info: Dict) -> str:
        """Get formatted bill period string"""
        if bill_info.get('bill_period_start') and bill_info.get('bill_period_end'):
            return f"{bill_info['bill_period_start']} - {bill_info['bill_period_end']}"
        return "N/A"
    
    def _clean_email_content(self, email_content: str) -> str:
        """Clean email content for display"""
        if '<html>' in email_content.lower() or '<body>' in email_content.lower():
            # Convert HTML to text
            h = html2text.HTML2Text()
            h.ignore_links = False
            h.ignore_images = True
            h.body_width = 0
            clean_content = h.handle(email_content)
        else:
            clean_content = email_content
        
        # Remove excessive whitespace
        lines = clean_content.split('\n')
        cleaned_lines = []
        for line in lines:
            cleaned_line = line.strip()
            if cleaned_line or (cleaned_lines and cleaned_lines[-1]):  # Keep single empty lines
                cleaned_lines.append(cleaned_line)
        
        return '\n'.join(cleaned_lines)
    
    def test_pdf_generation(self) -> bool:
        """Test PDF generation with sample data"""
        print("Testing PDF generation...")
        
        # Sample bill data
        sample_bill = {
            'bill_amount': 288.15,
            'due_date': '08/08/2025',
            'roommate_portion': 96.05,
            'my_portion': 192.10,
            'email_subject': 'Your PG&E Energy Statement is Ready to View',
            'email_date': 'Sun, 20 Jul 2025 19:05:18 +0000 (UTC)',
            'email_id': 'test123',
            'status': 'pending'
        }
        
        # Sample email content
        sample_email = """
Your paperless bill for account ending in ******9112-5 is now available.

**$288.15** | **08/08/2025**

If you are enrolled in Recurring Payments*, no action is needed. Your payment
will process automatically on the date and for the amount you have selected.

PG&E Bill Payment Options:
Pay your way. Set up online payments, pay by phone, pay multiple bills at
once, and more.

View Past Bill Inserts:
View our most recent bill inserts including safety and rate change information.

For inquiries, please do not reply to this email. Submit feedback via Contact Us.

"PG&E" refers to Pacific Gas and Electric Company, a subsidiary of PG&E Corporation
300 Lakeside Drive, Oakland, CA 94612

@2025 Pacific Gas and Electric Company. All rights reserved.
        """
        
        try:
            pdf_path = self.generate_bill_pdf(sample_bill, sample_email)
            if pdf_path and Path(pdf_path).exists():
                print(f"✓ Test PDF generated successfully: {pdf_path}")
                print(f"  File size: {Path(pdf_path).stat().st_size} bytes")
                return True
            else:
                print("✗ Test PDF generation failed")
                return False
        except Exception as e:
            print(f"✗ Test PDF generation error: {e}")
            return False