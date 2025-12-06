#!/usr/bin/env python3
"""
Daily Progress Script
Fetches GitHub commits for the day, generates insights, and sends to Discord.
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import pytz

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from utils import (
    GitHubClient,
    GeminiClient,
    DiscordNotifier,
    load_config
)


def main():
    """Main function to run daily progress tracking."""
    print("=" * 60)
    print("🚀 Insightify - Daily Progress Tracker")
    print("=" * 60)
    
    # Load environment variables
    load_dotenv()
    
    # Get required credentials
    github_token = os.getenv('GH_TOKEN')
    github_username = os.getenv('GH_USERNAME')
    gemini_api_key = os.getenv('GEMINI_API_KEY')
    discord_webhook = os.getenv('DISCORD_WEBHOOK_URL')
    
    # Validate credentials
    if not all([github_token, github_username, gemini_api_key]):
        print("❌ Error: Missing required environment variables!")
        print("Please ensure GH_TOKEN, GH_USERNAME, and GEMINI_API_KEY are set.")
        sys.exit(1)
    
    # Load configuration
    try:
        config = load_config()
    except Exception as e:
        print(f"❌ Error loading config: {str(e)}")
        sys.exit(1)
    
    # Initialize clients
    print("\n📡 Initializing clients...")
    try:
        github_client = GitHubClient(github_token, github_username)
        gemini_client = GeminiClient(
            gemini_api_key,
            model=config.get('gemini', {}).get('model', 'gemini-1.5-flash'),
            temperature=config.get('gemini', {}).get('temperature', 0.7)
        )
        
        if discord_webhook and config.get('discord', {}).get('enabled', True):
            discord_client = DiscordNotifier(discord_webhook)
        else:
            discord_client = None
            print("⚠️  Discord notifications disabled")
    except Exception as e:
        print(f"❌ Error initializing clients: {str(e)}")
        sys.exit(1)
    
    # Get current date in PKT timezone
    pkt_tz = pytz.timezone(config.get('timezone', 'Asia/Karachi'))
    current_time = datetime.now(pkt_tz)
    date_str = current_time.strftime('%Y-%m-%d')
    
    print(f"\n📅 Fetching data for: {date_str} (PKT)")
    
    # Fetch GitHub commits
    print("📊 Fetching GitHub commits...")
    try:
        hours_back = config.get('github', {}).get('hours_lookback', 24)
        commit_data = github_client.get_daily_commits(
            date=current_time,
            hours_back=hours_back
        )
        
        print(f"✅ Found {commit_data['total_commits']} commits across {len(commit_data['repositories'])} repositories")
        
        # Display summary
        if commit_data['total_commits'] > 0:
            print(f"   ⏱️  Estimated coding time: {commit_data['estimated_hours']} hours")
            print(f"   💻 Languages used: {', '.join(commit_data['languages'].keys())}")
        
    except Exception as e:
        print(f"❌ Error fetching GitHub data: {str(e)}")
        sys.exit(1)
    
    # Save to JSON file
    data_dir = Path(__file__).parent.parent / config.get('data_directory', 'data')
    data_dir.mkdir(exist_ok=True)
    
    output_file = data_dir / f"{date_str}.json"
    
    print(f"\n💾 Saving data to: {output_file}")
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(commit_data, f, indent=2, ensure_ascii=False)
        print("✅ Data saved successfully")
    except Exception as e:
        print(f"❌ Error saving data: {str(e)}")
        sys.exit(1)
    
    # Generate AI insights
    print("\n🤖 Generating AI insights...")
    try:
        insights = gemini_client.generate_daily_insights(commit_data)
        print("✅ Insights generated")
        print("\n" + "─" * 60)
        print(insights)
        print("─" * 60)
        
        # Add insights to data
        commit_data['ai_insights'] = insights
        
        # Update JSON with insights
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(commit_data, f, indent=2, ensure_ascii=False)
            
    except Exception as e:
        print(f"⚠️  Warning: Could not generate insights: {str(e)}")
        insights = "Insights generation failed."
    
    # Send to Discord
    if discord_client:
        print("\n📤 Sending to Discord...")
        try:
            success = discord_client.send_daily_summary(commit_data, insights)
            if success:
                print("✅ Discord notification sent successfully")
            else:
                print("⚠️  Failed to send Discord notification")
        except Exception as e:
            print(f"⚠️  Error sending to Discord: {str(e)}")
    
    # Summary
    print("\n" + "=" * 60)
    print("✨ Daily progress tracking complete!")
    print("=" * 60)
    print(f"📊 Total commits: {commit_data['total_commits']}")
    print(f"⏱️  Estimated time: {commit_data['estimated_hours']} hours")
    print(f"📁 Data saved: {output_file}")
    print("=" * 60)


if __name__ == '__main__':
    main()
