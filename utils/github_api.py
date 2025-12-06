"""
GitHub API utility module for fetching commit data and analyzing activity.
"""

import os
from datetime import datetime, timedelta
from typing import Dict, List, Any
from collections import defaultdict
import pytz
from github import Github
from github.GithubException import GithubException


class GitHubClient:
    """Client for interacting with GitHub API."""
    
    def __init__(self, token: str, username: str):
        """
        Initialize GitHub client.
        
        Args:
            token: GitHub personal access token
            username: GitHub username to track
        """
        self.client = Github(token)
        self.username = username
        self.user = self.client.get_user(username)
    
    def get_daily_commits(self, date: datetime = None, hours_back: int = 24) -> Dict[str, Any]:
        """
        Fetch commits for a specific day.
        
        Args:
            date: Date to fetch commits for (default: today)
            hours_back: Number of hours to look back (default: 24)
            
        Returns:
            Dictionary containing commit data and statistics
        """
        if date is None:
            date = datetime.now(pytz.UTC)
        
        # Calculate time range
        end_time = date
        start_time = end_time - timedelta(hours=hours_back)
        
        commits_data = {
            'date': date.strftime('%Y-%m-%d'),
            'total_commits': 0,
            'repositories': {},
            'languages': defaultdict(int),
            'commits_by_hour': defaultdict(int),
            'commit_messages': [],
            'time_range': {
                'start': start_time.isoformat(),
                'end': end_time.isoformat()
            }
        }
        
        try:
            # Get all user repositories
            repos = self.user.get_repos()
            
            for repo in repos:
                try:
                    # Get commits by author in the time range
                    commits = repo.get_commits(
                        author=self.username,
                        since=start_time,
                        until=end_time
                    )
                    
                    repo_commits = []
                    for commit in commits:
                        commit_data = {
                            'sha': commit.sha[:7],
                            'message': commit.commit.message.split('\n')[0],  # First line only
                            'timestamp': commit.commit.author.date.isoformat(),
                            'url': commit.html_url
                        }
                        repo_commits.append(commit_data)
                        commits_data['commit_messages'].append({
                            'repo': repo.name,
                            **commit_data
                        })
                        
                        # Track commits by hour
                        hour = commit.commit.author.date.hour
                        commits_data['commits_by_hour'][hour] += 1
                    
                    if repo_commits:
                        # Get primary language
                        language = repo.language or 'Unknown'
                        commits_data['languages'][language] += len(repo_commits)
                        
                        commits_data['repositories'][repo.name] = {
                            'commits_count': len(repo_commits),
                            'language': language,
                            'url': repo.html_url,
                            'commits': repo_commits
                        }
                        commits_data['total_commits'] += len(repo_commits)
                
                except GithubException as e:
                    # Skip repos we can't access
                    print(f"Warning: Could not access repo {repo.name}: {str(e)}")
                    continue
            
            # Convert defaultdicts to regular dicts for JSON serialization
            commits_data['languages'] = dict(commits_data['languages'])
            commits_data['commits_by_hour'] = dict(commits_data['commits_by_hour'])
            
            # Calculate approximate time spent (rough estimate based on commit timestamps)
            commits_data['estimated_hours'] = self._estimate_time_spent(commits_data['commit_messages'])
            
        except GithubException as e:
            print(f"Error fetching GitHub data: {str(e)}")
            raise
        
        return commits_data
    
    def _estimate_time_spent(self, commits: List[Dict]) -> float:
        """
        Estimate time spent coding based on commit timestamps.
        Uses a simple heuristic: gaps > 2 hours are considered breaks.
        
        Args:
            commits: List of commit dictionaries
            
        Returns:
            Estimated hours spent
        """
        if not commits:
            return 0.0
        
        # Sort commits by timestamp
        sorted_commits = sorted(commits, key=lambda x: x['timestamp'])
        
        total_hours = 0.0
        MAX_GAP_HOURS = 2  # Consider gaps > 2 hours as breaks
        
        for i in range(1, len(sorted_commits)):
            prev_time = datetime.fromisoformat(sorted_commits[i-1]['timestamp'])
            curr_time = datetime.fromisoformat(sorted_commits[i]['timestamp'])
            
            gap = (curr_time - prev_time).total_seconds() / 3600  # Convert to hours
            
            if gap <= MAX_GAP_HOURS:
                total_hours += gap
        
        # Add some base time for the first and last commits
        if len(sorted_commits) > 0:
            total_hours += 0.5  # 30 minutes base
        
        return round(total_hours, 2)
    
    def get_user_info(self) -> Dict[str, Any]:
        """
        Get basic user information.
        
        Returns:
            Dictionary with user info
        """
        return {
            'username': self.user.login,
            'name': self.user.name,
            'public_repos': self.user.public_repos,
            'followers': self.user.followers,
            'following': self.user.following,
            'bio': self.user.bio,
            'avatar_url': self.user.avatar_url
        }
