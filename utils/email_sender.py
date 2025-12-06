"""
Email sender utility for monthly reports.
"""

import os
import smtplib
import base64
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email import encoders
from typing import Dict, Any, Optional
from datetime import datetime


class EmailSender:
    """Client for sending email reports."""
    
    def __init__(self, smtp_server: str, smtp_port: int, email_from: str, 
                 email_password: str, email_to: str):
        """
        Initialize email sender.
        
        Args:
            smtp_server: SMTP server address
            smtp_port: SMTP server port
            email_from: Sender email address
            email_password: Sender email password (app password)
            email_to: Recipient email address
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.email_from = email_from
        self.email_password = email_password
        self.email_to = email_to
    
    def send_monthly_report(self, monthly_data: Dict[str, Any], insights: str, 
                           chart_paths: Optional[list] = None) -> bool:
        """
        Send monthly report via email.
        
        Args:
            monthly_data: Dictionary containing monthly statistics
            insights: AI-generated insights (markdown format)
            chart_paths: Optional list of paths to chart images
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart('related')
            msg['From'] = self.email_from
            msg['To'] = self.email_to
            msg['Subject'] = f"📊 Monthly Code Analysis - {monthly_data.get('month', 'N/A')}"
            
            # Prepare chart CIDs (without attaching yet)
            chart_cids = []
            if chart_paths:
                for i, chart_path in enumerate(chart_paths):
                    if os.path.exists(chart_path):
                        chart_cids.append(f"chart{i}")
            
            # Build HTML body with embedded charts
            html_body = self._build_html_report(monthly_data, insights, chart_cids)
            
            # Print HTML to console for debugging
            print("\n" + "="*60)
            print("EMAIL HTML PREVIEW:")
            print("="*60)
            print(html_body)  # Print first 2000 chars
            
            print("="*60)
            
            # Attach HTML with explicit UTF-8 encoding FIRST
            html_part = MIMEText(html_body, 'html', 'utf-8')
            msg.attach(html_part)
            
            # Now embed charts as inline images AFTER the HTML
            if chart_paths:
                for i, chart_path in enumerate(chart_paths):
                    if os.path.exists(chart_path):
                        self._embed_image(msg, chart_path, i)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_from, self.email_password)
                server.send_message(msg)
            
            print(f"✅ Monthly report sent successfully to {self.email_to}")
            return True
            
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            return False
    
    def _build_html_report(self, data: Dict[str, Any], insights: str, chart_cids: list = None) -> str:
        """Build HTML email body for monthly report with embedded charts - Gmail compatible with inline styles."""
        total_commits = data.get('total_commits', 0)
        total_hours = data.get('total_hours', 0)
        active_days = data.get('active_days', 0)
        streak = data.get('longest_streak', 0)
        languages = data.get('languages', {})
        top_repos = data.get('top_repositories', [])
        
        # Convert markdown to HTML
        if not insights or len(insights.strip()) == 0:
            insights = "⚠️ AI analysis could not be generated. Please check the configuration and try again."
        insights_html = self._markdown_to_html(insights)
        
        # Build charts HTML with inline styles
        charts_html = ""
        if chart_cids:
            for cid in chart_cids:
                charts_html += f'<div style="margin: 25px 0; text-align: center;"><img src="cid:{cid}" alt="Chart" style="max-width: 100%; height: auto; border-radius: 10px;"></div>'
        
        # Gmail-compatible HTML with inline styles
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="margin: 0; padding: 20px; font-family: Arial, sans-serif; background-color: #f7fafc; color: #2d3748;">
            <table width="100%" cellpadding="0" cellspacing="0" style="max-width: 600px; margin: 0 auto; background-color: #ffffff;">
                <!-- Header -->
                <tr>
                    <td style="background: linear-gradient(135deg, #1a202c 0%, #2d3748 100%); background-color: #1a202c; color: white; padding: 40px 30px; text-align: center;">
                        <h1 style="margin: 0 0 8px 0; font-size: 32px; font-weight: 700;">📊 Monthly Code Analysis</h1>
                        <p style="margin: 0; font-size: 18px;">{data.get('month', 'N/A')}</p>
                    </td>
                </tr>
                
                <!-- Stats Grid -->
                <tr>
                    <td style="padding: 40px 30px;">
                        <table width="100%" cellpadding="10" cellspacing="0">
                            <tr>
                                <td width="33%" style="background: #f7fafc; padding: 20px; text-align: center; border: 2px solid #e2e8f0; border-radius: 8px;">
                                    <div style="color: #718096; font-size: 12px; text-transform: uppercase; font-weight: 600;">Total Commits</div>
                                    <div style="font-size: 32px; font-weight: 700; color: #1a202c; margin: 8px 0;">{total_commits}</div>
                                </td>
                                <td width="33%" style="background: #f7fafc; padding: 20px; text-align: center; border: 2px solid #e2e8f0; border-radius: 8px;">
                                    <div style="color: #718096; font-size: 12px; text-transform: uppercase; font-weight: 600;">Coding Hours</div>
                                    <div style="font-size: 32px; font-weight: 700; color: #1a202c; margin: 8px 0;">{total_hours}</div>
                                </td>
                                <td width="33%" style="background: #f7fafc; padding: 20px; text-align: center; border: 2px solid #e2e8f0; border-radius: 8px;">
                                    <div style="color: #718096; font-size: 12px; text-transform: uppercase; font-weight: 600;">Active Days</div>
                                    <div style="font-size: 32px; font-weight: 700; color: #1a202c; margin: 8px 0;">{active_days}</div>
                                </td>
                            </tr>
                            <tr>
                                <td width="33%" style="background: #f7fafc; padding: 20px; text-align: center; border: 2px solid #e2e8f0; border-radius: 8px;">
                                    <div style="color: #718096; font-size: 12px; text-transform: uppercase; font-weight: 600;">Longest Streak</div>
                                    <div style="font-size: 32px; font-weight: 700; color: #1a202c; margin: 8px 0;">{streak}</div>
                                </td>
                                <td width="33%" style="background: #f7fafc; padding: 20px; text-align: center; border: 2px solid #e2e8f0; border-radius: 8px;">
                                    <div style="color: #718096; font-size: 12px; text-transform: uppercase; font-weight: 600;">Avg/Day</div>
                                    <div style="font-size: 32px; font-weight: 700; color: #1a202c; margin: 8px 0;">{data.get('avg_commits_per_day', 0)}</div>
                                </td>
                                <td width="33%" style="background: #f7fafc; padding: 20px; text-align: center; border: 2px solid #e2e8f0; border-radius: 8px;">
                                    <div style="color: #718096; font-size: 12px; text-transform: uppercase; font-weight: 600;">Repositories</div>
                                    <div style="font-size: 32px; font-weight: 700; color: #1a202c; margin: 8px 0;">{data.get('total_repos', 0)}</div>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
        """
        
        # Add languages section
        if languages:
            html += """
                <tr>
                    <td style="padding: 0 30px 30px 30px;">
                        <h2 style="color: #1a202c; font-size: 20px; font-weight: 700; margin-bottom: 15px; padding-bottom: 8px; border-bottom: 3px solid #e2e8f0;">💻 Language Breakdown</h2>
                        <table width="100%" cellpadding="0" cellspacing="0">
            """
            for lang, count in sorted(languages.items(), key=lambda x: x[1], reverse=True):
                html += f"""
                            <tr>
                                <td style="padding: 12px 15px; margin: 5px 0; background: #f7fafc; border-left: 4px solid #4a5568;">
                                    <table width="100%"><tr>
                                        <td style="color: #2d3748;">{lang}</td>
                                        <td align="right" style="color: #1a202c; font-weight: 600;">{count} commits</td>
                                    </tr></table>
                                </td>
                            </tr>
                """
            html += """
                        </table>
                    </td>
                </tr>
            """
        
        # Add top repositories
        if top_repos:
            html += """
                <tr>
                    <td style="padding: 0 30px 30px 30px;">
                        <h2 style="color: #1a202c; font-size: 20px; font-weight: 700; margin-bottom: 15px; padding-bottom: 8px; border-bottom: 3px solid #e2e8f0;">🔥 Top Repositories</h2>
                        <table width="100%" cellpadding="0" cellspacing="0">
            """
            for repo in top_repos[:10]:
                html += f"""
                            <tr>
                                <td style="padding: 12px 15px; margin: 5px 0; background: #f7fafc; border-left: 4px solid #4a5568; color: #2d3748;">
                                    {repo}
                                </td>
                            </tr>
                """
            html += """
                        </table>
                    </td>
                </tr>
            """
        
        # Add charts
        if charts_html:
            html += f"""
                <tr>
                    <td style="padding: 0 30px 30px 30px;">
                        <h2 style="color: #1a202c; font-size: 20px; font-weight: 700; margin-bottom: 15px; padding-bottom: 8px; border-bottom: 3px solid #e2e8f0;">📈 Visual Analytics</h2>
                        {charts_html}
                    </td>
                </tr>
            """
        
        # Add AI insights with inline styles for markdown elements
        insights_styled = insights_html.replace('<h1', '<h1 style="color: #1a202c; font-size: 24px; margin: 20px 0 10px 0;"')
        insights_styled = insights_styled.replace('<h2', '<h2 style="color: #1a202c; font-size: 20px; margin: 18px 0 10px 0;"')
        insights_styled = insights_styled.replace('<h3', '<h3 style="color: #1a202c; font-size: 18px; margin: 16px 0 8px 0;"')
        insights_styled = insights_styled.replace('<p>', '<p style="margin: 0 0 12px 0; color: #2d3748; line-height: 1.6;">')
        insights_styled = insights_styled.replace('<ul>', '<ul style="margin: 0 0 12px 20px; color: #2d3748;">')
        insights_styled = insights_styled.replace('<li>', '<li style="margin-bottom: 6px;">')
        insights_styled = insights_styled.replace('<strong>', '<strong style="color: #1a202c; font-weight: 700;">')
        insights_styled = insights_styled.replace('<code>', '<code style="background: #cbd5e0; padding: 2px 6px; border-radius: 3px; font-family: monospace;">')
        
        html += f"""
                <tr>
                    <td style="padding: 0 30px 30px 30px;">
                        <h2 style="color: #1a202c; font-size: 20px; font-weight: 700; margin-bottom: 15px; padding-bottom: 8px; border-bottom: 3px solid #e2e8f0;">🎯 AI Analysis</h2>
                        <div style="background: #edf2f7; padding: 25px; border-left: 4px solid #e53e3e; line-height: 1.7;">
                            {insights_styled}
                        </div>
                    </td>
                </tr>
                
                <!-- Footer -->
                <tr>
                    <td style="padding: 30px; text-align: center; color: #718096; border-top: 2px solid #e2e8f0;">
                        <p style="margin: 0; font-weight: 700; color: #2d3748;">Insightify</p>
                        <p style="margin: 8px 0 0 0; font-size: 12px;">Your Personal Coding Analytics</p>
                        <p style="margin: 5px 0 0 0; font-size: 11px;">Generated on {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}</p>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
        
        return html
    
    def _markdown_to_html(self, markdown_text: str) -> str:
        """Convert markdown to HTML."""
        if not markdown_text:
            return "<p>No analysis available.</p>"
        
        html = markdown_text
        
        # Headers (must be done before other replacements)
        html = re.sub(r'^### (.+?)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.+?)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^# (.+?)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
        
        # Lists (unordered)
        html = re.sub(r'^\s*[-*]\s+(.+?)$', r'<li>\1</li>', html, flags=re.MULTILINE)
        html = re.sub(r'(<li>.*?</li>)', r'<ul>\1</ul>', html, flags=re.DOTALL)
        html = re.sub(r'</ul>\s*<ul>', '', html)  # Merge consecutive ul tags
        
        # Bold
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
        
        # Italic
        html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
        
        # Code blocks
        html = re.sub(r'`(.+?)`', r'<code>\1</code>', html)
        
        # Line breaks - convert double newlines to paragraphs, single to br
        html = re.sub(r'\n\n+', '</p><p>', html)
        html = re.sub(r'\n', '<br>', html)
        
        # Wrap in paragraph if not already wrapped in block elements
        if not html.startswith('<'):
            html = f'<p>{html}</p>'
        
        return html
    
    def _embed_image(self, msg: MIMEMultipart, filepath: str, index: int):
        """Embed image in email with Content-ID for inline display."""
        cid = f"chart{index}"
        
        with open(filepath, 'rb') as f:
            img = MIMEImage(f.read())
            img.add_header('Content-ID', f'<{cid}>')
            img.add_header('Content-Disposition', 'inline', filename=os.path.basename(filepath))
            msg.attach(img)
