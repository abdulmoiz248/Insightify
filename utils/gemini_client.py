"""
Google Gemini AI client for generating insights and analysis.
"""

import os
from typing import Dict, Any, List
import google.generativeai as genai


class GeminiClient:
    """Client for interacting with Google Gemini API."""
    
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash", temperature: float = 0.7):
        """
        Initialize Gemini client.
        
        Args:
            api_key: Google Gemini API key
            model: Model name to use (default: gemini-1.5-flash)
            temperature: Temperature for generation (0.0-1.0)
        """
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)
        self.temperature = temperature
    
    def generate_daily_insights(self, commit_data: Dict[str, Any]) -> str:
        """
        Generate insights for daily commit data.
        
        Args:
            commit_data: Dictionary containing daily commit statistics
            
        Returns:
            Generated insights as string
        """
        # Build prompt from data
        prompt = self._build_daily_prompt(commit_data)
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config={
                    'temperature': self.temperature,
                    'max_output_tokens': 1000,
                }
            )
            return response.text
        except Exception as e:
            return f"Error generating insights: {str(e)}"
    
    def generate_monthly_insights(self, monthly_data: Dict[str, Any]) -> str:
        """
        Generate insights for monthly aggregated data.
        
        Args:
            monthly_data: Dictionary containing monthly statistics
            
        Returns:
            Generated insights as string
        """
        prompt = self._build_monthly_prompt(monthly_data)
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config={
                    'temperature': self.temperature,
                    'max_output_tokens': 2000,
                }
            )
            return response.text
        except Exception as e:
            return f"Error generating insights: {str(e)}"
    
    def _build_daily_prompt(self, data: Dict[str, Any]) -> str:
        """Build prompt for daily insights."""
        total_commits = data.get('total_commits', 0)
        repos = data.get('repositories', {})
        languages = data.get('languages', {})
        estimated_hours = data.get('estimated_hours', 0)
        
        prompt = f"""As a developer productivity analyst, analyze this developer's daily GitHub activity and provide concise, actionable insights.

**Daily Summary ({data.get('date', 'N/A')})**
- Total Commits: {total_commits}
- Estimated Coding Time: {estimated_hours} hours
- Repositories Active: {len(repos)}
- Languages Used: {', '.join(languages.keys()) if languages else 'None'}

**Language Breakdown:**
{self._format_dict(languages)}

**Repository Activity:**
{self._format_repos(repos)}

Please provide:
1. A brief productivity summary (2-3 sentences)
2. Key highlights or patterns observed
3. One suggestion for improvement or focus area

Keep the response concise and motivating."""
        
        return prompt
    
    def _build_monthly_prompt(self, data: Dict[str, Any]) -> str:
        """Build prompt for monthly insights."""
        total_commits = data.get('total_commits', 0)
        total_hours = data.get('total_hours', 0)
        active_days = data.get('active_days', 0)
        languages = data.get('languages', {})
        top_repos = data.get('top_repositories', [])
        streak = data.get('longest_streak', 0)
        
        prompt = f"""As a developer productivity analyst, analyze this developer's monthly GitHub activity and provide comprehensive insights.

**Monthly Summary ({data.get('month', 'N/A')})**
- Total Commits: {total_commits}
- Total Coding Time: {total_hours} hours
- Active Days: {active_days}
- Longest Streak: {streak} days
- Average Commits/Day: {data.get('avg_commits_per_day', 0)}

**Language Distribution:**
{self._format_dict(languages)}

**Top Repositories:**
{self._format_list(top_repos)}

**Weekly Breakdown:**
{self._format_dict(data.get('commits_by_week', {}))}

Please provide:
1. Overall productivity assessment (3-4 sentences)
2. Key achievements and milestones
3. Technology focus and diversification analysis
4. Consistency and streak analysis
5. 2-3 actionable recommendations for the next month

Keep the response comprehensive but well-structured."""
        
        return prompt
    
    @staticmethod
    def _format_dict(data: Dict) -> str:
        """Format dictionary for prompt."""
        if not data:
            return "None"
        return "\n".join([f"  - {k}: {v}" for k, v in sorted(data.items(), key=lambda x: x[1], reverse=True)])
    
    @staticmethod
    def _format_repos(repos: Dict) -> str:
        """Format repositories for prompt."""
        if not repos:
            return "None"
        result = []
        for name, info in sorted(repos.items(), key=lambda x: x[1]['commits_count'], reverse=True):
            result.append(f"  - {name}: {info['commits_count']} commits ({info['language']})")
        return "\n".join(result)
    
    @staticmethod
    def _format_list(items: List) -> str:
        """Format list for prompt."""
        if not items:
            return "None"
        return "\n".join([f"  - {item}" for item in items])
