"""
Email sender utility for monthly reports.
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
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
            insights: AI-generated insights
            chart_paths: Optional list of paths to chart images
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.email_from
            msg['To'] = self.email_to
            msg['Subject'] = f"[Insightify] Monthly Report - {monthly_data.get('month', 'N/A')}"
            
            # Build HTML body
            html_body = self._build_html_report(monthly_data, insights)
            msg.attach(MIMEText(html_body, 'html'))
            
            # Attach charts if provided
            if chart_paths:
                for chart_path in chart_paths:
                    if os.path.exists(chart_path):
                        self._attach_file(msg, chart_path)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_from, self.email_password)
                server.send_message(msg)
            
            print(f"Monthly report sent successfully to {self.email_to}")
            return True
            
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            return False
    
    def _build_html_report(self, data: Dict[str, Any], insights: str) -> str:
        """Build HTML email body for monthly report."""
        total_commits = data.get('total_commits', 0)
        total_hours = data.get('total_hours', 0)
        active_days = data.get('active_days', 0)
        streak = data.get('longest_streak', 0)
        languages = data.get('languages', {})
        top_repos = data.get('top_repositories', [])
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    border-radius: 10px;
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 32px;
                }}
                .stats-grid {{
                    display: grid;
                    grid-template-columns: repeat(3, 1fr);
                    gap: 20px;
                    margin-bottom: 30px;
                }}
                .stat-card {{
                    background: #f8f9fa;
                    padding: 20px;
                    border-radius: 8px;
                    text-align: center;
                    border-left: 4px solid #667eea;
                }}
                .stat-value {{
                    font-size: 36px;
                    font-weight: bold;
                    color: #667eea;
                    margin: 10px 0;
                }}
                .stat-label {{
                    color: #666;
                    font-size: 14px;
                    text-transform: uppercase;
                }}
                .section {{
                    background: white;
                    padding: 25px;
                    margin-bottom: 20px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .section h2 {{
                    color: #667eea;
                    border-bottom: 2px solid #667eea;
                    padding-bottom: 10px;
                    margin-top: 0;
                }}
                .language-list, .repo-list {{
                    list-style: none;
                    padding: 0;
                }}
                .language-list li, .repo-list li {{
                    padding: 10px;
                    margin: 5px 0;
                    background: #f8f9fa;
                    border-radius: 5px;
                    display: flex;
                    justify-content: space-between;
                }}
                .insights {{
                    background: #f0f7ff;
                    padding: 20px;
                    border-radius: 8px;
                    border-left: 4px solid #667eea;
                    white-space: pre-wrap;
                }}
                .footer {{
                    text-align: center;
                    color: #999;
                    margin-top: 40px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📊 Monthly Progress Report</h1>
                <p style="margin: 10px 0 0 0; font-size: 18px;">{data.get('month', 'N/A')}</p>
            </div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-label">Total Commits</div>
                    <div class="stat-value">{total_commits}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Coding Hours</div>
                    <div class="stat-value">{total_hours}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Active Days</div>
                    <div class="stat-value">{active_days}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Longest Streak</div>
                    <div class="stat-value">{streak}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Avg Commits/Day</div>
                    <div class="stat-value">{data.get('avg_commits_per_day', 0)}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Repositories</div>
                    <div class="stat-value">{data.get('total_repos', 0)}</div>
                </div>
            </div>
        """
        
        # Add languages section
        if languages:
            html += """
            <div class="section">
                <h2>💻 Language Breakdown</h2>
                <ul class="language-list">
            """
            for lang, count in sorted(languages.items(), key=lambda x: x[1], reverse=True):
                html += f"<li><span>{lang}</span><strong>{count} commits</strong></li>"
            html += "</ul></div>"
        
        # Add top repositories
        if top_repos:
            html += """
            <div class="section">
                <h2>🔥 Top Repositories</h2>
                <ul class="repo-list">
            """
            for repo in top_repos[:10]:
                html += f"<li><span>{repo}</span></li>"
            html += "</ul></div>"
        
        # Add AI insights
        html += f"""
            <div class="section">
                <h2>🤖 AI-Generated Insights</h2>
                <div class="insights">{insights}</div>
            </div>
            
            <div class="footer">
                <p><strong>Insightify</strong> - Your Personal Coding Analytics</p>
                <p style="font-size: 12px;">Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    @staticmethod
    def _attach_file(msg: MIMEMultipart, filepath: str):
        """Attach a file to the email message."""
        filename = os.path.basename(filepath)
        
        with open(filepath, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
        
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename={filename}')
        msg.attach(part)
