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
                },
                safety_settings=[
                    {
                        "category": "HARM_CATEGORY_HARASSMENT",
                        "threshold": "BLOCK_NONE",
                    },
                    {
                        "category": "HARM_CATEGORY_HATE_SPEECH",
                        "threshold": "BLOCK_NONE",
                    },
                ]
            )
            
            # Check if response was blocked
            if not response.text:
                # Fallback to basic analysis
                return self._generate_fallback_insights(commit_data)
            
            return response.text
        except Exception as e:
            print(f"Warning: AI generation failed ({str(e)}), using fallback analysis")
            return self._generate_fallback_insights(commit_data)
    
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
                },
                safety_settings=[
                    {
                        "category": "HARM_CATEGORY_HARASSMENT",
                        "threshold": "BLOCK_NONE",
                    },
                    {
                        "category": "HARM_CATEGORY_HATE_SPEECH",
                        "threshold": "BLOCK_NONE",
                    },
                    {
                        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                        "threshold": "BLOCK_NONE",
                    },
                    {
                        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                        "threshold": "BLOCK_NONE",
                    },
                ]
            )
            
            # Check if response was blocked
            if not response.text:
                print("⚠️  Warning: AI response was blocked, using fallback analysis")
                return self._generate_monthly_fallback(monthly_data)
            
            return response.text
        except Exception as e:
            print(f"⚠️  Warning: AI generation failed ({str(e)}), using fallback analysis")
            return self._generate_monthly_fallback(monthly_data)
    
    def _build_daily_prompt(self, data: Dict[str, Any]) -> str:
        """Build prompt for daily insights."""
        total_commits = data.get('total_commits', 0)
        repos = data.get('repositories', {})
        languages = data.get('languages', {})
        estimated_hours = data.get('estimated_hours', 0)
        commit_messages = data.get('commit_messages', [])
        previous_days = data.get('previous_days', [])
        
        # Extract commit messages for analysis
        commit_msgs = "\n".join([f"  - [{msg['repo']}] {msg['message']}" for msg in commit_messages[:15]])
        
        # Build context from previous days
        prev_context = ""
        if previous_days:
            # Get last 7 days summary
            prev_repos = set()
            prev_total_commits = 0
            prev_languages = set()
            
            for day in previous_days:
                prev_total_commits += day.get('total_commits', 0)
                prev_repos.update(day.get('repositories', {}).keys())
                prev_languages.update(day.get('languages', {}).keys())
            
            avg_commits = prev_total_commits / len(previous_days) if previous_days else 0
            
            prev_context = f"""
**Last 7 Days Context:**
- Average commits/day: {avg_commits:.1f}
- Total unique repos: {len(prev_repos)}
- Recent repos: {', '.join(list(prev_repos)[:5])}
- Languages used: {', '.join(prev_languages)}
"""
        
        prompt = f"""You are a brutally honest senior developer reviewing a junior's daily activity. Be direct, specific, and call out issues without sugarcoating. Use actual data points.

**Today's Data ({data.get('date', 'N/A')})**
Commits: {total_commits} | Time: {estimated_hours}h | Repos: {len(repos)} | Languages: {', '.join(languages.keys()) if languages else 'None'}

{prev_context}

**Recent Commit Messages:**
{commit_msgs if commit_msgs else "No commits today"}

**Active Repositories:**
{self._format_repos(repos)}

Analyze this and respond in EXACTLY this format (no extra commentary):

Pattern Detection:
[2-3 sentences maximum] Be SPECIFIC about what's happening. Name the actual repos (e.g., "Backend + Frontend work on Hygieia"). Mention the exact language split (e.g., "Mix of TypeScript/Python"). Call out the pace explicitly (e.g., "{total_commits} commits across {estimated_hours}h = slower pace than usual" OR "solid productivity"). Reference whether it's full-stack, polyglot, or focused work.

Red Flags:
[2-3 sentences maximum] SCRUTINIZE the commit messages and patterns. Look for: 
- Vague messages like "fix", "update", "REVERT", "added code" instead of descriptive ones
- Same repo appearing in previous days context (stuck/grinding)
- Low commits for high hours (procrastinating/stuck?)
- Too many repos (unfocused?)
- Build fixes and reverts (breaking things?)
If you find issues, call them out by name. If truly nothing wrong, say "None detected - clean commits and focused work."

Brutal Truth:
[1-2 sentences maximum] Give the REAL insight. Examples: "Still grinding on Hygieia for days without clear feature completion - might be stuck or scope creeping." OR "3 commits with 'fix' and 'update' messages - what are you actually fixing?" OR "REVERT commit suggests you pushed broken code - slow down and test locally." Reference specific repos and commit messages. Don't be generic.

CRITICAL: Use ACTUAL repo names from the data, ACTUAL commit messages, and ACTUAL numbers. No placeholders, no generic advice."""
        
        return prompt
    
    def _build_monthly_prompt(self, data: Dict[str, Any]) -> str:
        """Build prompt for monthly insights - strict mentor style."""
        total_commits = data.get('total_commits', 0)
        total_hours = data.get('total_hours', 0)
        active_days = data.get('active_days', 0)
        languages = data.get('languages', {})
        top_repos = data.get('top_repositories', [])
        streak = data.get('longest_streak', 0)
        total_days = data.get('total_days', 30)
        avg_commits = data.get('avg_commits_per_day', 0)
        
        prompt = f"""You are a strict technical mentor reviewing a developer's monthly GitHub performance. Be honest, critical, and constructive. Avoid any generic introductions or conclusions like "Here's a comprehensive analysis" or "In conclusion". Get straight to the point.

**Monthly Data ({data.get('month', 'N/A')})**
- Total Commits: {total_commits}
- Coding Time: {total_hours}h
- Active Days: {active_days}/{total_days} days
- Longest Streak: {streak} days
- Avg Commits/Day: {avg_commits}
- Repositories: {data.get('total_repos', 0)}

**Languages:**
{self._format_dict(languages)}

**Top Repositories:**
{self._format_list(top_repos)}

**Weekly Pattern:**
{self._format_dict(data.get('commits_by_week', {}))}

Provide your analysis in this EXACT structure (use markdown headers):

## Performance Reality Check
[2-3 sentences] Hit the facts hard. Calculate actual productivity metrics: {active_days}/{total_days} days active means X% engagement. {total_commits} commits in {total_hours}h = Y commits/hour. Compare this to professional standards. If they're slacking, say it. If consistency is poor, point it out specifically with numbers.

## Technical Depth & Focus
[2-3 sentences] Analyze their language distribution and repository focus. Are they spreading too thin across {data.get('total_repos', 0)} repos? Is the language diversity ({', '.join(list(languages.keys())[:3])}) helping or hindering? Call out if they're jumping between projects without finishing anything. Reference specific repos from the top list.

## Critical Issues
[2-3 bullet points] Identify concrete problems:
- Consistency gaps (check if streak of {streak} days vs {active_days} active days shows irregular pattern)
- Productivity concerns (low commits/hour, inactive days pattern)
- Scope/focus problems (too many repos, language scatter)
Be specific. Use actual repo names and numbers from the data. If there are genuine issues, don't soften them. If performance is actually solid, acknowledge it briefly.

## What Needs to Change
[2-3 specific, actionable points] Give direct orders, not suggestions:
- "Commit daily to reach 80%+ active days" (if currently low)
- "Focus on finishing [specific repo] before starting new work" (if scattered)
- "Increase commit frequency to 3+/day on active days" (if low productivity)
Be brutally specific based on the actual weaknesses you identified above.

CRITICAL RULES:
- NO introductory sentences like "Here's my analysis" or "Let me review"
- NO concluding statements like "In summary" or "Overall"
- Use ACTUAL repo names from the top repositories list
- Reference SPECIFIC numbers from the data
- If performance is poor, be blunt about it
- If performance is good, be brief and move to areas for improvement
- This is a performance review, not a motivational speech"""
        
        return prompt
    
    def _generate_fallback_insights(self, data: Dict[str, Any]) -> str:
        """Generate brutally honest basic insights when AI fails."""
        total_commits = data.get('total_commits', 0)
        repos = data.get('repositories', {})
        languages = data.get('languages', {})
        hours = data.get('estimated_hours', 0)
        previous_days = data.get('previous_days', [])
        commit_messages = data.get('commit_messages', [])
        
        if total_commits == 0:
            return "Pattern Detection:\nNo commits today - either you're planning, stuck, or slacking.\n\nRed Flags:\nZero output is a red flag itself.\n\nBrutal Truth:\nNothing shipped, nothing learned."
        
        # Analyze commit quality
        vague_commits = []
        for msg in commit_messages[:10]:
            message_lower = msg['message'].lower()
            if any(word in message_lower for word in ['fix', 'update', 'change', 'revert', 'added code', 'updated']):
                if len(msg['message'].split()) < 4:  # Very short and vague
                    vague_commits.append(f"{msg['repo']}: '{msg['message']}'")
        
        # Build sections
        top_lang = max(languages.items(), key=lambda x: x[1])[0] if languages else "Unknown"
        repo_list = ', '.join(list(repos.keys())[:3])
        
        # Pattern Detection
        work_type = "full-stack" if len(repos) >= 2 and any('frontend' in r.lower() or 'backend' in r.lower() for r in repos.keys()) else "focused"
        pace_comment = "slow pace" if hours > 3 and total_commits < 5 else "reasonable pace" if hours > 2 else "focused burst"
        pattern = f"Pattern Detection:\n{total_commits} commits across {len(repos)} repos ({repo_list}) in {hours}h - {work_type} work. Primary language: {top_lang}. {pace_comment.capitalize()}."
        
        # Red Flags
        red_flags = []
        if vague_commits:
            red_flags.append(f"Vague commit messages detected: {', '.join(vague_commits[:2])} - what exactly did you change?")
        if hours > 3 and total_commits < 4:
            red_flags.append(f"{hours}h for {total_commits} commits - low output suggests you're stuck or distracted.")
        if len(repos) > 4:
            red_flags.append(f"Working across {len(repos)} repos - too much context switching.")
        
        # Check previous days for grinding
        if previous_days:
            prev_repos = set()
            for day in previous_days[-3:]:  # Last 3 days
                prev_repos.update(day.get('repositories', {}).keys())
            
            grinding_repos = set(repos.keys()).intersection(prev_repos)
            if grinding_repos and len(grinding_repos) == len(repos):
                red_flags.append(f"Still on {', '.join(list(grinding_repos)[:2])} from previous days - long-running work or stuck?")
        
        red_flags_text = "Red Flags:\n" + " ".join(red_flags) if red_flags else "Red Flags:\nNone detected - clean commits and focused work."
        
        # Brutal Truth
        if vague_commits and len(repos) == 1:
            truth = f"Brutal Truth:\nGrinding on {list(repos.keys())[0]} with vague commits - scope creeping or unclear objectives?"
        elif len(repos) > 3:
            truth = f"Brutal Truth:\nJumping between {len(repos)} projects - pick one and finish it."
        elif hours > 4 and total_commits < 3:
            truth = f"Brutal Truth:\n{hours}h for {total_commits} commits - productivity gap suggests blockers or distractions."
        else:
            truth = f"Brutal Truth:\nSolid focused work on {repo_list} - keep this momentum."
        
        return f"{pattern}\n\n{red_flags_text}\n\n{truth}"
    
    def _generate_monthly_fallback(self, data: Dict[str, Any]) -> str:
        """Generate fallback monthly insights when AI fails."""
        total_commits = data.get('total_commits', 0)
        total_hours = data.get('total_hours', 0)
        active_days = data.get('active_days', 0)
        total_days = data.get('total_days', 30)
        streak = data.get('longest_streak', 0)
        avg_commits = data.get('avg_commits_per_day', 0)
        languages = data.get('languages', {})
        top_repos = data.get('top_repositories', [])
        
        # Calculate engagement
        engagement_pct = (active_days / total_days * 100) if total_days > 0 else 0
        commits_per_hour = (total_commits / total_hours) if total_hours > 0 else 0
        
        # Performance Reality Check
        perf_rating = "excellent" if engagement_pct >= 80 else "good" if engagement_pct >= 60 else "needs improvement"
        performance = f"""## Performance Reality Check
{active_days}/{total_days} days active ({engagement_pct:.1f}% engagement) - {perf_rating}. {total_commits} commits in {total_hours}h equals {commits_per_hour:.1f} commits/hour. Longest streak: {streak} days."""
        
        # Technical Depth
        top_lang = max(languages.items(), key=lambda x: x[1])[0] if languages else "Unknown"
        lang_count = len(languages)
        repo_count = len(top_repos)
        
        focus_assessment = "too scattered" if repo_count > 10 else "well-focused" if repo_count <= 5 else "moderate spread"
        technical = f"""## Technical Depth & Focus
Working across {repo_count} repositories with {lang_count} languages (primary: {top_lang}). Distribution is {focus_assessment}. Top repos: {', '.join(top_repos[:3])}."""
        
        # Critical Issues
        issues = []
        if engagement_pct < 60:
            issues.append(f"Low consistency: only {active_days}/{total_days} active days")
        if streak < 5:
            issues.append(f"Weak streak: longest is only {streak} days - build better habits")
        if commits_per_hour < 0.5:
            issues.append(f"Low productivity: {commits_per_hour:.1f} commits/hour suggests inefficiency")
        if repo_count > 10:
            issues.append(f"Too scattered: working across {repo_count} repos")
        
        if not issues:
            issues.append("Solid performance overall - maintain this pace")
        
        critical = "## Critical Issues\n" + "\n".join([f"- {issue}" for issue in issues])
        
        # What Needs to Change
        changes = []
        if engagement_pct < 70:
            changes.append(f"Commit daily to reach 80%+ active days (currently {engagement_pct:.1f}%)")
        if streak < 7:
            changes.append(f"Build a 7+ day streak (current max: {streak} days)")
        if repo_count > 8:
            changes.append(f"Focus on top 3-5 repos: {', '.join(top_repos[:3])}")
        if commits_per_hour < 1:
            changes.append(f"Increase commit frequency to 3+ commits per active day")
        
        if not changes:
            changes.append("Continue current pace and maintain consistency")
        
        action = "## What Needs to Change\n" + "\n".join([f"- {change}" for change in changes])
        
        return f"{performance}\n\n{technical}\n\n{critical}\n\n{action}"
    
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
