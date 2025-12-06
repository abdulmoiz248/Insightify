"""
Discord webhook notifier for sending daily summaries.
"""

import requests
from typing import Dict, Any
from datetime import datetime


class DiscordNotifier:
    """Client for sending notifications to Discord via webhook."""
    
    def __init__(self, webhook_url: str):
        """
        Initialize Discord notifier.
        
        Args:
            webhook_url: Discord webhook URL
        """
        self.webhook_url = webhook_url
    
    def send_daily_summary(self, commit_data: Dict[str, Any], insights: str) -> bool:
        """
        Send daily summary to Discord.
        
        Args:
            commit_data: Dictionary containing commit data
            insights: AI-generated insights
            
        Returns:
            True if successful, False otherwise
        """
        embed = self._build_daily_embed(commit_data, insights)
        
        payload = {
            "username": "Insightify Bot",
            "avatar_url": "https://cdn-icons-png.flaticon.com/512/25/25231.png",
            "embeds": [embed]
        }
        
        try:
            response = requests.post(self.webhook_url, json=payload)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            print(f"Error sending Discord notification: {str(e)}")
            return False
    
    def send_monthly_summary(self, monthly_data: Dict[str, Any], insights: str) -> bool:
        """
        Send monthly summary to Discord.
        
        Args:
            monthly_data: Dictionary containing monthly statistics
            insights: AI-generated insights
            
        Returns:
            True if successful, False otherwise
        """
        embed = self._build_monthly_embed(monthly_data, insights)
        
        payload = {
            "username": "Insightify Bot",
            "avatar_url": "https://cdn-icons-png.flaticon.com/512/25/25231.png",
            "embeds": [embed]
        }
        
        try:
            response = requests.post(self.webhook_url, json=payload)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            print(f"Error sending Discord notification: {str(e)}")
            return False
    
    def _build_daily_embed(self, data: Dict[str, Any], insights: str) -> Dict:
        """Build Discord embed for daily summary."""
        total_commits = data.get('total_commits', 0)
        estimated_hours = data.get('estimated_hours', 0)
        languages = data.get('languages', {})
        repos = data.get('repositories', {})
        
        # Determine color based on activity level
        if total_commits == 0:
            color = 0x95a5a6  # Gray
        elif total_commits < 5:
            color = 0x3498db  # Blue
        elif total_commits < 10:
            color = 0x2ecc71  # Green
        else:
            color = 0xf39c12  # Orange (high activity)
        
        embed = {
            "title": f"📊 Daily Progress Report - {data.get('date', 'N/A')}",
            "color": color,
            "fields": [
                {
                    "name": "📈 Commits",
                    "value": f"**{total_commits}** commits",
                    "inline": True
                },
                {
                    "name": "⏱️ Time Spent",
                    "value": f"~**{estimated_hours}** hours",
                    "inline": True
                },
                {
                    "name": "📁 Repositories",
                    "value": f"**{len(repos)}** active",
                    "inline": True
                }
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Add languages if any
        if languages:
            lang_text = "\n".join([f"• {lang}: {count} commits" for lang, count in 
                                  sorted(languages.items(), key=lambda x: x[1], reverse=True)[:5]])
            embed["fields"].append({
                "name": "💻 Languages Used",
                "value": lang_text,
                "inline": False
            })
        
        # Add top repositories
        if repos:
            repo_text = "\n".join([f"• [{name}]({info['url']}): {info['commits_count']} commits" 
                                  for name, info in sorted(repos.items(), 
                                  key=lambda x: x[1]['commits_count'], reverse=True)[:5]])
            embed["fields"].append({
                "name": "🔥 Active Repositories",
                "value": repo_text,
                "inline": False
            })
        
        # Add AI insights
        if insights:
            # Truncate if too long (Discord limit is 1024 per field)
            insights_truncated = insights[:1000] + "..." if len(insights) > 1000 else insights
            embed["fields"].append({
                "name": "🤖 AI Insights",
                "value": insights_truncated,
                "inline": False
            })
        
        embed["footer"] = {
            "text": "Insightify - Track your coding journey"
        }
        
        return embed
    
    def _build_monthly_embed(self, data: Dict[str, Any], insights: str) -> Dict:
        """Build Discord embed for monthly summary - AI analysis only."""
        
        # Handle empty insights
        if not insights or len(insights.strip()) == 0:
            insights = "⚠️ AI analysis failed to generate. Please check the logs."
        
        # Discord description limit is 4096 characters
        # If insights are too long, we'll use description + fields
        if len(insights) <= 4000:
            embed = {
                "title": f"🤖 Monthly AI Analysis - {data.get('month', 'N/A')}",
                "color": 0x2C3E50,
                "description": insights,
                "timestamp": datetime.utcnow().isoformat(),
                "footer": {
                    "text": "Insightify - AI-Powered Code Analysis"
                }
            }
        else:
            # Split into description and fields for longer content
            embed = {
                "title": f"🤖 Monthly AI Analysis - {data.get('month', 'N/A')}",
                "color": 0x2C3E50,
                "description": insights[:2000],
                "fields": [
                    {
                        "name": "Continued...",
                        "value": insights[2000:4000] if len(insights) > 2000 else "",
                        "inline": False
                    }
                ],
                "timestamp": datetime.utcnow().isoformat(),
                "footer": {
                    "text": "Insightify - AI-Powered Code Analysis"
                }
            }
            
            # Add more fields if needed
            remaining = insights[4000:]
            if remaining and len(remaining) > 0:
                embed["fields"].append({
                    "name": "More...",
                    "value": remaining[:1024],
                    "inline": False
                })
        
        return embed
