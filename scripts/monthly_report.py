#!/usr/bin/env python3
"""
Monthly Report Script
Aggregates daily data, generates charts, and sends monthly report via email.
"""

import os
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
from dotenv import load_dotenv
import pytz
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from utils import (
    GeminiClient,
    DiscordNotifier,
    EmailSender,
    load_config
)


def load_daily_data(data_dir: Path, year: int, month: int) -> list:
    """
    Load all daily JSON files for a specific month.
    
    Args:
        data_dir: Directory containing daily JSON files
        year: Year to load
        month: Month to load (1-12)
        
    Returns:
        List of daily data dictionaries
    """
    daily_data = []
    
    # Get all days in the month
    from calendar import monthrange
    _, num_days = monthrange(year, month)
    
    for day in range(1, num_days + 1):
        date_str = f"{year:04d}-{month:02d}-{day:02d}"
        file_path = data_dir / f"{date_str}.json"
        
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    daily_data.append(data)
            except Exception as e:
                print(f"⚠️  Warning: Could not load {file_path}: {str(e)}")
    
    return daily_data


def aggregate_monthly_data(daily_data: list) -> dict:
    """
    Aggregate daily data into monthly statistics.
    
    Args:
        daily_data: List of daily data dictionaries
        
    Returns:
        Dictionary containing monthly aggregated data
    """
    monthly = {
        'total_commits': 0,
        'total_hours': 0.0,
        'active_days': 0,
        'languages': defaultdict(int),
        'repositories': defaultdict(int),
        'commits_by_day': {},
        'commits_by_week': defaultdict(int),
        'daily_breakdown': []
    }
    
    for day_data in daily_data:
        date = day_data.get('date', '')
        commits = day_data.get('total_commits', 0)
        
        if commits > 0:
            monthly['active_days'] += 1
        
        monthly['total_commits'] += commits
        monthly['total_hours'] += day_data.get('estimated_hours', 0)
        
        # Language aggregation
        for lang, count in day_data.get('languages', {}).items():
            monthly['languages'][lang] += count
        
        # Repository aggregation
        for repo, info in day_data.get('repositories', {}).items():
            monthly['repositories'][repo] += info.get('commits_count', 0)
        
        # Daily breakdown
        monthly['commits_by_day'][date] = commits
        
        # Week number
        try:
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            week_num = date_obj.isocalendar()[1]
            monthly['commits_by_week'][f"Week {week_num}"] += commits
        except:
            pass
        
        monthly['daily_breakdown'].append({
            'date': date,
            'commits': commits,
            'hours': day_data.get('estimated_hours', 0)
        })
    
    # Convert defaultdicts to regular dicts
    monthly['languages'] = dict(monthly['languages'])
    monthly['repositories'] = dict(monthly['repositories'])
    monthly['commits_by_week'] = dict(monthly['commits_by_week'])
    
    # Calculate additional metrics
    monthly['total_hours'] = round(monthly['total_hours'], 2)
    monthly['avg_commits_per_day'] = round(
        monthly['total_commits'] / len(daily_data) if daily_data else 0, 2
    )
    monthly['total_repos'] = len(monthly['repositories'])
    
    # Get top repositories
    monthly['top_repositories'] = [
        repo for repo, _ in sorted(
            monthly['repositories'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
    ]
    
    # Calculate longest streak
    monthly['longest_streak'] = calculate_longest_streak(monthly['commits_by_day'])
    
    return monthly


def calculate_longest_streak(commits_by_day: dict) -> int:
    """Calculate the longest streak of consecutive active days."""
    if not commits_by_day:
        return 0
    
    # Sort dates
    sorted_dates = sorted(commits_by_day.keys())
    
    current_streak = 0
    longest_streak = 0
    
    for i, date_str in enumerate(sorted_dates):
        if commits_by_day[date_str] > 0:
            if i == 0:
                current_streak = 1
            else:
                prev_date = datetime.strptime(sorted_dates[i-1], '%Y-%m-%d')
                curr_date = datetime.strptime(date_str, '%Y-%m-%d')
                
                # Check if consecutive day
                if (curr_date - prev_date).days == 1:
                    current_streak += 1
                else:
                    current_streak = 1
            
            longest_streak = max(longest_streak, current_streak)
        else:
            current_streak = 0
    
    return longest_streak


def generate_charts(monthly_data: dict, output_dir: Path, month_str: str):
    """
    Generate visualization charts for the monthly data.
    
    Args:
        monthly_data: Aggregated monthly data
        output_dir: Directory to save charts
        month_str: Month string (e.g., "2024-12")
        
    Returns:
        List of chart file paths
    """
    output_dir.mkdir(exist_ok=True)
    chart_paths = []
    
    # Set style (using modern matplotlib style)
    plt.style.use('default')
    plt.rcParams['axes.grid'] = True
    plt.rcParams['grid.alpha'] = 0.3
    
    # 1. Daily Commits Chart
    fig, ax = plt.subplots(figsize=(12, 6))
    
    dates = []
    commits = []
    for entry in sorted(monthly_data['daily_breakdown'], key=lambda x: x['date']):
        dates.append(datetime.strptime(entry['date'], '%Y-%m-%d'))
        commits.append(entry['commits'])
    
    ax.plot(dates, commits, marker='o', linewidth=2, markersize=6, color='#667eea')
    ax.fill_between(dates, commits, alpha=0.3, color='#667eea')
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Commits', fontsize=12)
    ax.set_title(f'Daily Commits - {month_str}', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    
    # Format x-axis
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    chart_path = output_dir / f'daily_commits_{month_str}.png'
    plt.savefig(chart_path, dpi=300, bbox_inches='tight')
    plt.close()
    chart_paths.append(str(chart_path))
    
    # 2. Language Distribution Pie Chart
    if monthly_data['languages']:
        fig, ax = plt.subplots(figsize=(10, 8))
        
        languages = list(monthly_data['languages'].keys())
        counts = list(monthly_data['languages'].values())
        
        colors = plt.cm.Set3(range(len(languages)))
        
        wedges, texts, autotexts = ax.pie(
            counts,
            labels=languages,
            autopct='%1.1f%%',
            startangle=90,
            colors=colors
        )
        
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        ax.set_title(f'Language Distribution - {month_str}', fontsize=14, fontweight='bold')
        plt.tight_layout()
        
        chart_path = output_dir / f'languages_{month_str}.png'
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        chart_paths.append(str(chart_path))
    
    # 3. Top Repositories Bar Chart
    if monthly_data['repositories']:
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Get top 10 repositories
        top_repos = sorted(
            monthly_data['repositories'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        repos = [r[0] for r in top_repos]
        commits = [r[1] for r in top_repos]
        
        bars = ax.barh(repos, commits, color='#667eea')
        
        # Add value labels
        for i, bar in enumerate(bars):
            width = bar.get_width()
            ax.text(width, bar.get_y() + bar.get_height()/2,
                   f' {int(width)}',
                   ha='left', va='center', fontweight='bold')
        
        ax.set_xlabel('Commits', fontsize=12)
        ax.set_title(f'Top 10 Repositories - {month_str}', fontsize=14, fontweight='bold')
        ax.invert_yaxis()
        plt.tight_layout()
        
        chart_path = output_dir / f'top_repos_{month_str}.png'
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        chart_paths.append(str(chart_path))
    
    return chart_paths


def main():
    """Main function to run monthly report generation."""
    print("=" * 60)
    print("📊 Insightify - Monthly Report Generator")
    print("=" * 60)
    
    # Load environment variables
    load_dotenv()
    
    # Get required credentials
    gemini_api_key = os.getenv('GEMINI_API_KEY')
    discord_webhook = os.getenv('DISCORD_WEBHOOK_URL')
    
    email_from = os.getenv('EMAIL_FROM')
    email_to = os.getenv('EMAIL_TO')
    email_password = os.getenv('EMAIL_PASSWORD')
    smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    
    # Validate credentials
    if not gemini_api_key:
        print("❌ Error: GEMINI_API_KEY is required!")
        sys.exit(1)
    
    # Load configuration
    try:
        config = load_config()
    except Exception as e:
        print(f"❌ Error loading config: {str(e)}")
        sys.exit(1)
    
    # Get previous month
    pkt_tz = pytz.timezone(config.get('timezone', 'Asia/Karachi'))
    current_time = datetime.now(pkt_tz)
    
    # Calculate previous month
    first_of_month = current_time.replace(day=1)
    last_month = first_of_month - timedelta(days=1)
    
    year = last_month.year
    month = last_month.month
    month_str = f"{year}-{month:02d}"
    
    print(f"\n📅 Generating report for: {last_month.strftime('%B %Y')} ({month_str})")
    
    # Load daily data
    data_dir = Path(__file__).parent.parent / config.get('data_directory', 'data')
    
    print(f"\n📂 Loading daily data from: {data_dir}")
    daily_data = load_daily_data(data_dir, year, month)
    
    if not daily_data:
        print(f"⚠️  No data found for {month_str}. Exiting.")
        sys.exit(0)
    
    print(f"✅ Loaded {len(daily_data)} days of data")
    
    # Aggregate data
    print("\n📊 Aggregating monthly statistics...")
    monthly_data = aggregate_monthly_data(daily_data)
    monthly_data['month'] = last_month.strftime('%B %Y')
    monthly_data['month_str'] = month_str
    
    print(f"✅ Total commits: {monthly_data['total_commits']}")
    print(f"✅ Active days: {monthly_data['active_days']}/{len(daily_data)}")
    print(f"✅ Total hours: {monthly_data['total_hours']}")
    print(f"✅ Longest streak: {monthly_data['longest_streak']} days")
    
    # Generate charts
    print("\n📈 Generating charts...")
    charts_dir = Path(__file__).parent.parent / 'charts'
    try:
        chart_paths = generate_charts(monthly_data, charts_dir, month_str)
        print(f"✅ Generated {len(chart_paths)} charts")
    except Exception as e:
        print(f"⚠️  Warning: Could not generate charts: {str(e)}")
        chart_paths = []
    
    # Initialize Gemini client
    print("\n🤖 Generating AI insights...")
    try:
        gemini_client = GeminiClient(
            gemini_api_key,
            model=config.get('gemini', {}).get('model', 'gemini-1.5-flash'),
            temperature=config.get('gemini', {}).get('temperature', 0.7)
        )
        insights = gemini_client.generate_monthly_insights(monthly_data)
        print("✅ Insights generated")
        print("\n" + "─" * 60)
        print(insights)
        print("─" * 60)
    except Exception as e:
        print(f"⚠️  Warning: Could not generate insights: {str(e)}")
        insights = "Insights generation failed."
    
    # Save monthly report
    report_file = data_dir / f"monthly_report_{month_str}.json"
    monthly_data['ai_insights'] = insights
    monthly_data['chart_paths'] = chart_paths
    
    print(f"\n💾 Saving monthly report to: {report_file}")
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(monthly_data, f, indent=2, ensure_ascii=False)
    print("✅ Report saved")
    
    # Send to Discord
    if discord_webhook and config.get('discord', {}).get('enabled', True):
        print("\n📤 Sending to Discord...")
        try:
            discord_client = DiscordNotifier(discord_webhook)
            success = discord_client.send_monthly_summary(monthly_data, insights)
            if success:
                print("✅ Discord notification sent")
            else:
                print("⚠️  Failed to send Discord notification")
        except Exception as e:
            print(f"⚠️  Error sending to Discord: {str(e)}")
    
    # Send email
    if all([email_from, email_to, email_password]) and config.get('email', {}).get('enabled', True):
        print("\n📧 Sending email report...")
        try:
            email_client = EmailSender(
                smtp_server, smtp_port,
                email_from, email_password, email_to
            )
            success = email_client.send_monthly_report(
                monthly_data, insights, chart_paths
            )
            if success:
                print("✅ Email sent successfully")
            else:
                print("⚠️  Failed to send email")
        except Exception as e:
            print(f"⚠️  Error sending email: {str(e)}")
    
    # Summary
    print("\n" + "=" * 60)
    print("✨ Monthly report generation complete!")
    print("=" * 60)
    print(f"📊 Period: {monthly_data['month']}")
    print(f"💻 Total commits: {monthly_data['total_commits']}")
    print(f"⏱️  Total hours: {monthly_data['total_hours']}")
    print(f"📅 Active days: {monthly_data['active_days']}")
    print(f"🔥 Longest streak: {monthly_data['longest_streak']} days")
    print(f"📁 Report saved: {report_file}")
    print("=" * 60)


if __name__ == '__main__':
    main()
